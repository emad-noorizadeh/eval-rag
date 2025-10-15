# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LangGraph implementation of the streamlined router."""

from __future__ import annotations

import operator
from typing import Annotated, Dict, Any, List, Literal, TypedDict

from langgraph.graph import StateGraph, END, START

from .utils.conversation_utils import is_ack_or_coref


Message = Dict[str, str]
Chunk = Dict[str, Any]


class AgentState(TypedDict, total=False):
    """State carried through the router graph."""

    # Persistent session metadata
    last_question: str
    awaiting_clarification: bool
    clarify_count: int
    last_clarification: str
    topic_hint: str
    session_id: str

    # Conversation history (accumulates)
    messages: Annotated[List[Message], operator.add]

    # Turn-local fields
    user_message: str
    conversation_snippet: str
    frustration_triggered: bool
    effective_question: str
    appended_history: bool
    retrieved_chunks: List[Chunk]
    retrieval_scores: List[float]
    avg_similarity: float
    rag_response: Dict[str, Any]
    answer_text: str
    clarification_question: str
    decision: Literal["answer", "clarification", "abstain"]
    metrics: Dict[str, Any]
    response: Dict[str, Any]


class SimpleRouterApp:
    """LangGraph wrapper replicating ChatAgent's streamlined router."""

    FRUSTRATION_TOKENS = {"hard", "difficult", "confusing", "confused", "unclear", "complicated"}

    def __init__(self, chat_agent):
        self.chat_agent = chat_agent
        self.rag = chat_agent.rag
        self.config = chat_agent.config
        self.graph = self._build_graph()

    # Graph construction -------------------------------------------------

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("ingest", self.ingest)
        graph.add_node("frustration", self.handle_frustration)
        graph.add_node("build_query", self.build_effective_question)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("answer", self.answer_llm)
        graph.add_node("decide", self.decide)
        graph.add_node("finalize", self.finalize)

        graph.add_edge(START, "ingest")
        graph.add_edge("ingest", "frustration")
        graph.add_conditional_edges(
            "frustration",
            lambda s: "skip_to_finalize" if s.get("frustration_triggered") else "continue",
            {"skip_to_finalize": "finalize", "continue": "build_query"},
        )
        graph.add_edge("build_query", "retrieve")
        graph.add_edge("retrieve", "answer")
        graph.add_edge("answer", "decide")
        graph.add_edge("decide", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()

    # Nodes --------------------------------------------------------------

    def ingest(self, state: AgentState) -> AgentState:
        """Append user message and refresh session state fields."""
        messages = list(state.get("messages", []))
        user_message = state.get("user_message", "")
        if user_message:
            messages.append({"role": "user", "content": user_message})
        state["messages"] = messages
        state.setdefault("last_question", "")
        state.setdefault("awaiting_clarification", False)
        state.setdefault("clarify_count", 0)
        state.setdefault("last_clarification", "")
        state.setdefault("topic_hint", "")
        return state

    def handle_frustration(self, state: AgentState) -> AgentState:
        last_question = state.get("last_question", "")
        clarify_count = state.get("clarify_count", 0)
        user_message = state.get("user_message", "")
        frustration_triggered = (
            user_message
            and not user_message.endswith("?")
            and any(token in user_message.lower() for token in self.FRUSTRATION_TOKENS)
        )

        if frustration_triggered:
            clarification = "I’m happy to help—could you tell me which part you’d like me to explain further?"
            state.update(
                {
                    "frustration_triggered": True,
                    "awaiting_clarification": True,
                    "clarify_count": clarify_count + 1,
                    "last_clarification": clarification,
                    "decision": "clarification",
                    "answer_text": clarification,
                    "clarification_question": clarification,
                    "retrieved_chunks": [],
                    "retrieval_scores": [],
                    "avg_similarity": 0.0,
                    "rag_response": {
                        "answer": "",
                        "metrics": {
                            "answer": "",
                            "confidence": "Low",
                            "faithfulness_score": 0.0,
                            "completeness_score": 0.0,
                            "abstained": True,
                            "answer_type": "clarification",
                            "clarifying_question": clarification,
                            "missing_information": ["User indicated difficulty understanding"],
                            "reasoning_notes": "Clarification auto-generated due to frustration trigger",
                        },
                    },
                }
            )
        else:
            state["frustration_triggered"] = False

        return state

    def build_effective_question(self, state: AgentState) -> AgentState:
        user_message = state.get("user_message", "").strip()
        last_question = state.get("last_question", "")
        awaiting = state.get("awaiting_clarification", False)
        appended_history = False
        effective_question = user_message

        if awaiting and last_question:
            effective_question = f"{last_question}. {user_message}".strip()
            appended_history = True
        elif len(user_message.split()) <= 4 and last_question and not is_ack_or_coref(user_message):
            effective_question = f"{last_question}. {user_message}".strip()
            appended_history = True
        elif is_ack_or_coref(user_message) and last_question:
            effective_question = last_question
            appended_history = True

        state.update({
            "effective_question": effective_question,
            "appended_history": appended_history,
        })
        return state

    def retrieve(self, state: AgentState) -> AgentState:
        effective_question = state.get("effective_question", "")
        retrieved = self.rag.retrieve_documents(
            effective_question,
            self.config.retrieval_top_k,
        )
        scores = [chunk.get("score", 0.0) for chunk in retrieved]
        avg_similarity = sum(scores) / len(scores) if scores else 0.0
        state.update(
            {
                "retrieved_chunks": retrieved,
                "retrieval_scores": scores,
                "avg_similarity": avg_similarity,
            }
        )
        return state

    def answer_llm(self, state: AgentState) -> AgentState:
        effective_question = state.get("effective_question", "")
        retrieved = state.get("retrieved_chunks", [])
        messages = state.get("messages", [])
        topic_hint = state.get("topic_hint", "")
        conversation_snippet = self.chat_agent._build_conversation_snippet(messages)

        rag_response = self.rag.generate_response(
            effective_question,
            retrieved,
            conversation_snippet=conversation_snippet,
            topic_hint=topic_hint,
        )
        state["rag_response"] = rag_response
        return state

    def decide(self, state: AgentState) -> AgentState:
        rag_response = state.get("rag_response", {})
        metrics = rag_response.get("metrics", {})
        clarifying_question = (metrics.get("clarifying_question") or "").strip()
        abstained = bool(metrics.get("abstained", False))
        interpreted_question = (metrics.get("interpreted_question") or "").strip()

        decision: Literal["answer", "clarification", "abstain"]
        answer_text = (rag_response.get("answer") or "").strip()
        awaiting = False

        if abstained and clarifying_question:
            decision = "clarification"
            answer_text = clarifying_question
            awaiting = True
            state["clarify_count"] = state.get("clarify_count", 0) + 1
        elif abstained:
            decision = "abstain"
            answer_text = "This question cannot be answered with the available information."
        else:
            decision = "answer"

        state.update(
            {
                "decision": decision,
                "answer_text": answer_text or clarifying_question or "I'm sorry, I don't have that information.",
                "clarification_question": clarifying_question,
                "awaiting_clarification": awaiting,
                "interpreted_question": interpreted_question or state.get("effective_question", ""),
            }
        )
        return state

    def finalize(self, state: AgentState) -> AgentState:
        messages = state.get("messages", [])
        rag_response = state.get("rag_response", {})
        retrieved = state.get("retrieved_chunks", [])
        metrics = self.chat_agent._create_intelligent_metrics(
            original_question=state.get("user_message", ""),
            effective_question=state.get("effective_question", ""),
            retrieved_chunks=retrieved,
            rag_response=rag_response,
            conversation_length=len(messages),
            avg_score=state.get("avg_similarity", 0.0),
            threshold=self.config.similarity_threshold,
            awaiting_clarification=state.get("awaiting_clarification", False),
            clarify_count=state.get("clarify_count", 0),
            last_clarification=state.get("clarification_question", ""),
        )

        # Update persistent metadata for next turn
        decision = state.get("decision")
        interpreted_question = state.get("interpreted_question", "")
        if decision == "clarification":
            last_question = state.get("last_question", "")
            state["awaiting_clarification"] = True
            state["last_clarification"] = state.get("clarification_question", "")
            state["topic_hint"] = last_question or interpreted_question
        else:
            state["awaiting_clarification"] = False
            state["last_clarification"] = ""
            state["last_question"] = interpreted_question
            state["topic_hint"] = interpreted_question

        sources = self.chat_agent._extract_sources_from_rag(rag_response)
        response = {
            "answer": state.get("answer_text", ""),
            "session_id": state.get("session_id"),
            "timestamp": self.chat_agent._now(),
            "metrics": metrics,
            "sources": sources,
            "retrieval_metadata": {
                "method": self.config.retrieval_method.value,
                "total_chunks": len(retrieved),
                "avg_similarity": state.get("avg_similarity", 0.0),
                "threshold": self.config.similarity_threshold,
                "routing_strategy": self.config.routing_strategy.value,
            },
            "generated_by": "answer_llm",
        }

        if state.get("appended_history"):
            response["rephrased_input"] = state.get("effective_question", "")
        if state.get("clarification_question"):
            response["clarification_question"] = state.get("clarification_question")

        retrieval_error = getattr(self.rag, "last_retrieval_error", None)
        if retrieval_error and decision != "clarification":
            response["answer"] = (
                "I ran into a connection issue while retrieving information. "
                "Please try again in a moment or adjust your question."
            )
            state["awaiting_clarification"] = False
            state["last_clarification"] = ""
            metrics["route_metrics"]["decision"] = "error"
            metrics["route_metrics"]["retrieval_error"] = retrieval_error

        messages.append({"role": "assistant", "content": response["answer"]})
        state["messages"] = messages
        state["metrics"] = metrics
        state["response"] = response

        # reset last retrieval error for next turn
        if hasattr(self.rag, "last_retrieval_error"):
            self.rag.last_retrieval_error = None
        return state

    # Helpers ------------------------------------------------------------

    def invoke(self, state: AgentState) -> AgentState:
        return self.graph.invoke(state)
