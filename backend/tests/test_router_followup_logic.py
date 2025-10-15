"""Legacy router tests (skipped)."""

import pytest

pytest.skip(
    "Legacy router logic has been replaced by the streamlined oracle-based flow; "
    "skip legacy router-specific tests.",
    allow_module_level=True,
)


class FakeRAG:
    """Minimal RAG stub for router testing."""

    def __init__(self, docs_by_query=None, response=None):
        self.docs_by_query = docs_by_query or {}
        self.response = response or {
            "answer": "Stub answer",
            "metrics": {
                "answer_type": "answer",
                "confidence": "High",
                "abstained": False,
                "clarifying_question": ""
            }
        }
        self.retrieve_calls = []
        self.generate_calls = []

    def _build_nodes(self, query):
        docs = self.docs_by_query.get(query)
        if docs is None:
            lowered = query.lower()
            for key, docs_list in self.docs_by_query.items():
                if key.lower() in lowered or lowered in key.lower():
                    docs = docs_list
                    break
        if docs is None:
            docs = []
        nodes = []
        for idx, doc in enumerate(docs):
            nodes.append({
                "chunk_id": f"C{idx+1}",
                "doc_id": doc.get("doc_id", f"D{idx+1}"),
                "text": doc["text"],
                "score": doc.get("score", 0.9),
                "metadata": doc.get("metadata", {})
            })
        return nodes

    def retrieve_documents(self, query, n_results=5):
        self.retrieve_calls.append({"method": "single", "query": query, "hint": None, "use_union": False})
        return self._build_nodes(query)

    def retrieve_documents_union_if_needed(self, original_query, hint_query, n_results=5, use_union=False):
        self.retrieve_calls.append({
            "method": "union",
            "query": original_query,
            "hint": hint_query,
            "use_union": use_union
        })
        nodes = self._build_nodes(original_query)
        if use_union and hint_query:
            nodes.extend(self._build_nodes(hint_query))
        return nodes

    def generate_response(self, question, retrieved, conversation_snippet="", topic_hint=""):
        self.generate_calls.append({
            "question": question,
            "retrieved_count": len(retrieved),
            "topic_hint": topic_hint
        })
        return self.response


def _base_state(**overrides):
    """Helper to construct an AgentState with sensible defaults."""
    base = AgentState(
        messages=[],
        focus_hint="",
        last_clarification="",
        clarify_count=0,
        max_clarify=2,
        top_k=3,
        threshold=0.45,
        reclarify_threshold=0.35,
        primary_question=""
    )
    base.update(overrides)
    return base


def test_ack_followup_uses_focus_hint_and_answers():
    docs_by_query = {
        "gold tier requirements": [
            {"text": "Gold tier requires a combined balance of $20,000.", "score": 0.82}
        ]
    }
    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    messages = [
        {"role": "user", "content": "what is the preferred rewards program?"},
        {"role": "assistant", "content": "Could you clarify which tier you're interested in?"},
        {"role": "user", "content": "yes"}
    ]

    state = _base_state(
        messages=messages,
        focus_hint="gold tier requirements",
        last_clarification="Could you clarify which tier you're interested in?",
        clarify_count=1
    )

    result = router.invoke(state)

    assert result["answer_type"] != "clarification"
    assert result["answer"].startswith("Stub answer")
    assert rag.retrieve_calls, "Retrieval should have been attempted"
    first_call = rag.retrieve_calls[0]
    assert first_call["method"] == "union"
    assert first_call["hint"] == "gold tier requirements"
    assert first_call["use_union"] is True
    assert result.get("route_metrics", {}).get("decision") == "answer_high_confidence"
    assert result.get("effective_question") == "yes"
    assert rag.generate_calls and rag.generate_calls[0]["question"] == "yes"


def test_nonsense_followup_forces_clarification_without_retrieval():
    rag = FakeRAG()
    router = SimpleRouterApp(model_manager=None, rag=rag)

    messages = [
        {"role": "user", "content": "tell me about tiers"},
        {"role": "assistant", "content": "Could you clarify which tier you mean?"},
        {"role": "user", "content": "???"}
    ]

    state = _base_state(
        messages=messages,
        focus_hint="",
        last_clarification="Could you clarify which tier you mean?",
        clarify_count=1
    )

    result = router.invoke(state)

    assert result["answer_type"] == "clarification"
    assert result.get("route_metrics", {}).get("decision") in {"clarify_forced", "clarify_no_context", "clarify_missing_entities"}


def test_relaxed_threshold_allows_followup_answer():
    docs_by_query = {
        "preferred rewards gold tier requirements": [
            {"text": "Gold tier requires $20k average balance.", "score": 0.4}
        ],
        "tell me about preferred rewards preferred rewards gold tier requirements": [
            {"text": "Gold tier requires $20k average balance.", "score": 0.4}
        ]
    }
    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    messages = [
        {"role": "user", "content": "tell me about preferred rewards"},
        {"role": "assistant", "content": "Which tier are you interested in?"},
        {"role": "user", "content": "requirements"}
    ]

    state = _base_state(
        messages=messages,
        focus_hint="preferred rewards gold tier",
        last_clarification="Which tier are you interested in?",
        clarify_count=1,
        reclarify_threshold=0.35
    )

    result = router.invoke(state)

    assert result["answer_type"] != "clarification"
    metrics = result.get("route_metrics", {})
    assert metrics.get("decision") == "answer_followup_relaxed"
    assert result.get("avg_score") == 0.4
    assert result.get("raw_avg_score") == 0.4
    assert rag.generate_calls and "preferred rewards" in rag.generate_calls[0]["question"].lower()


def test_followup_combines_with_previous_question():
    docs_by_query = {
        "what is the minimum fee savings": [
            {"text": "The minimum fee for savings is $5.", "score": 0.8}
        ],
        "savings": [
            {"text": "Savings general info", "score": 0.7}
        ]
    }
    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    messages = [
        {"role": "user", "content": "what is the minimum fee"},
        {"role": "assistant", "content": "Could you please specify which type of account or fee you are referring to?"},
        {"role": "user", "content": "savings"}
    ]

    state = _base_state(
        messages=messages,
        focus_hint="",
        last_clarification="Could you please specify which type of account or fee you are referring to?",
        clarify_count=1
    )

    result = router.invoke(state)

    assert result["answer_type"] == "answer"
    assert result["answer"].startswith("Stub answer")
    assert rag.retrieve_calls
    assert "savings" in rag.retrieve_calls[0]["query"].lower()


def test_fee_savings_followup_flow():
    docs_by_query = {
        "minimum fee": [
            {"text": "SafeBalance checking has a $4.95 monthly maintenance fee.", "score": 0.85}
        ],
        "savings": [
            {"text": "Advantage Savings has a $5 monthly fee that can be waived with qualifying activity.", "score": 0.82}
        ],
        "all savings": [
            {"text": "Regular Savings: $5 fee; Advantage Savings: $5 fee; Custodial Savings: $0 fee.", "score": 0.78}
        ]
    }
    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    base_state = {
        "top_k": 3,
        "threshold": 0.45,
        "reclarify_threshold": 0.35,
        "max_clarify": 3
    }

    # Turn 1: minimum fee
    state1 = AgentState(
        **base_state,
        messages=[{"role": "user", "content": "minimum fee"}],
        intent_qualifiers=[],
        intent_pending_slots=[],
        intent_filled_slots={},
        clarify_count=0
    )
    result1 = router.invoke(state1)
    assert result1["answer_type"] == "answer"

    # Turn 2: what about savings
    messages2 = [
        {"role": "user", "content": "minimum fee"},
        {"role": "assistant", "content": result1["answer"]},
        {"role": "user", "content": "what about savings"}
    ]
    state2 = AgentState(
        **base_state,
        messages=messages2,
        focus_hint=result1.get("focus_hint", ""),
        intent_topic=result1.get("intent_topic", ""),
        intent_subject=result1.get("intent_subject", ""),
        intent_qualifiers=result1.get("intent_qualifiers", []),
        intent_pending_slots=result1.get("intent_pending_slots", []),
        intent_filled_slots=result1.get("intent_filled_slots", {}),
        primary_question=result1.get("primary_question", "minimum fee"),
        clarify_count=result1.get("clarify_count", 0)
    )
    result2 = router.invoke(state2)
    assert result2["answer_type"] == "answer"
    assert result2.get("coverage_score", 0.0) > 0.0

    # Turn 3: fee for savings account
    messages3 = messages2 + [
        {"role": "assistant", "content": result2["answer"]},
        {"role": "user", "content": "fee for savings account"}
    ]
    state3 = AgentState(
        **base_state,
        messages=messages3,
        focus_hint=result2.get("focus_hint", ""),
        intent_topic=result2.get("intent_topic", ""),
        intent_subject=result2.get("intent_subject", ""),
        intent_qualifiers=result2.get("intent_qualifiers", []),
        intent_pending_slots=result2.get("intent_pending_slots", []),
        intent_filled_slots=result2.get("intent_filled_slots", {}),
        primary_question=result2.get("primary_question", "minimum fee"),
        clarify_count=result2.get("clarify_count", 0)
    )
    result3 = router.invoke(state3)
    assert result3["answer_type"] == "answer"

    # Turn 4: all savings
    messages4 = messages3 + [
        {"role": "assistant", "content": result3["answer"]},
        {"role": "user", "content": "all savings"}
    ]
    state4 = AgentState(
        **base_state,
        messages=messages4,
        focus_hint=result3.get("focus_hint", ""),
        intent_topic=result3.get("intent_topic", ""),
        intent_subject=result3.get("intent_subject", ""),
        intent_qualifiers=result3.get("intent_qualifiers", []),
        intent_pending_slots=result3.get("intent_pending_slots", []),
        intent_filled_slots=result3.get("intent_filled_slots", {}),
        primary_question=result3.get("primary_question", "minimum fee"),
        clarify_count=result3.get("clarify_count", 0)
    )
    result4 = router.invoke(state4)
    assert result4["answer_type"] == "answer"
    assert not result4.get("route_metrics", {}).get("decision", "").startswith("clarify")


def test_requirements_after_tier_question():
    docs_by_query = {
        "what is tier": [
            {"text": "Preferred Rewards tiers are Gold, Platinum, Platinum Honors, and Diamond Honors.", "score": 0.9}
        ],
        "what are the requirements for preferred rewards tier": [
            {"text": "Gold requires $20,000, Platinum $50,000, Platinum Honors $100,000, Diamond Honors $1,000,000.", "score": 0.88}
        ],
        "preferred rewards requirements": [
            {"text": "Preferred Rewards tiers require combined balances across Bank of America and Merrill accounts.", "score": 0.86}
        ]
    }

    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    base_state = {
        "top_k": 3,
        "threshold": 0.45,
        "reclarify_threshold": 0.35,
        "max_clarify": 3
    }

    # Turn 1: what is tier
    state1 = AgentState(
        **base_state,
        messages=[{"role": "user", "content": "what is tier"}],
        intent_qualifiers=[],
        intent_pending_slots=[],
        intent_filled_slots={},
        clarify_count=0
    )
    result1 = router.invoke(state1)
    assert result1["answer_type"] == "answer"

    # Turn 2: what is the requirements
    messages2 = [
        {"role": "user", "content": "what is tier"},
        {"role": "assistant", "content": result1["answer"]},
        {"role": "user", "content": "what is the requirements"}
    ]
    state2 = AgentState(
        **base_state,
        messages=messages2,
        focus_hint=result1.get("focus_hint", ""),
        intent_topic=result1.get("intent_topic", ""),
        intent_subject=result1.get("intent_subject", ""),
        intent_qualifiers=result1.get("intent_qualifiers", []),
        intent_pending_slots=result1.get("intent_pending_slots", []),
        intent_filled_slots=result1.get("intent_filled_slots", {}),
        primary_question=result1.get("primary_question", "what is tier"),
        clarify_count=result1.get("clarify_count", 0)
    )
    result2 = router.invoke(state2)

    assert result2["answer_type"] == "answer"
    effective_question = result2.get("effective_question", "").lower()
    assert "requirement" in effective_question
    assert "preferred rewards" in effective_question


def test_specific_tier_followup_answers():
    docs_by_query = {
        "what is tier": [
            {"text": "Preferred Rewards tiers are Gold, Platinum, Platinum Honors, and Diamond Honors.", "score": 0.8}
        ],
        "gold tier": [
            {"text": "Gold tier requires a combined daily balance of $20,000 across eligible accounts.", "score": 0.82}
        ]
    }
    rag = FakeRAG(docs_by_query=docs_by_query)
    router = SimpleRouterApp(model_manager=SimpleNamespace(), rag=rag)

    # Turn 1: what is tier
    state1 = _base_state(
        messages=[{"role": "user", "content": "what is tier"}],
        clarify_count=0,
        intent_qualifiers=[],
        intent_pending_slots=[],
        intent_filled_slots={}
    )
    result1 = router.invoke(state1)
    assert result1["answer_type"] in {"answer", "clarification"}

    # Turn 2: gold tier
    messages2 = [
        {"role": "user", "content": "what is tier"},
        {"role": "assistant", "content": result1.get("answer", "")},
        {"role": "user", "content": "gold tier"}
    ]
    state2 = _base_state(
        messages=messages2,
        focus_hint=result1.get("focus_hint", ""),
        intent_topic=result1.get("intent_topic", ""),
        intent_subject=result1.get("intent_subject", ""),
        intent_qualifiers=result1.get("intent_qualifiers", []),
        intent_pending_slots=result1.get("intent_pending_slots", []),
        intent_filled_slots=result1.get("intent_filled_slots", {}),
        primary_question=result1.get("primary_question", "what is tier"),
        clarify_count=result1.get("clarify_count", 0)
    )
    result2 = router.invoke(state2)
    assert result2["answer_type"] == "answer"
    decision = result2.get("route_metrics", {}).get("decision")
    assert decision in {"answer_high_confidence", "answer_followup_relaxed"}
