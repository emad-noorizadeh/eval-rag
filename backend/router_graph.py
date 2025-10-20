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

import logging
import operator
import time
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
        self.logger = logging.getLogger(__name__ + ".router")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)

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
        user_message = state.get("user_message", "")
        session_id = state.get("session_id", "unknown")
        self.logger.info(
            "node=ingest session=%s message='%s'",
            session_id,
            user_message[:160],
        )

        updates: AgentState = {}
        if user_message:
            updates["messages"] = [{"role": "user", "content": user_message}]

        # Ensure persistent defaults exist for downstream nodes.
        updates["last_question"] = state.get("last_question", "")
        updates["awaiting_clarification"] = state.get("awaiting_clarification", False)
        updates["clarify_count"] = state.get("clarify_count", 0)
        updates["last_clarification"] = state.get("last_clarification", "")
        updates["topic_hint"] = state.get("topic_hint", "")

        return updates

    def handle_frustration(self, state: AgentState) -> AgentState:
        user_message = state.get("user_message", "")
        session_id = state.get("session_id", "unknown")
        self.logger.debug("node=frustration session=%s", session_id)
        frustration_triggered = (
            user_message
            and not user_message.endswith("?")
            and any(token in user_message.lower() for token in self.FRUSTRATION_TOKENS)
        )

        updates: AgentState = {
            "frustration_triggered": bool(frustration_triggered),
        }

        if frustration_triggered:
            clarification = "I’m happy to help—could you tell me which part you’d like me to explain further?"
            self.logger.info(
                "node=frustration session=%s triggered tokens",
                state.get("session_id", "unknown"),
            )
            clarify_count = state.get("clarify_count", 0) + 1
            updates.update(
                {
                    "awaiting_clarification": True,
                    "clarify_count": clarify_count,
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
            self.logger.debug(
                "node=frustration session=%s not_triggered",
                state.get("session_id", "unknown"),
            )

        return updates

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

        self.logger.info(
            "node=build_query session=%s effective='%s' appended_history=%s",
            state.get("session_id", "unknown"),
            effective_question[:160],
            appended_history,
        )
        return {
            "effective_question": effective_question,
            "appended_history": appended_history,
        }

    def retrieve(self, state: AgentState) -> AgentState:
        effective_question = state.get("effective_question", "")
        self.logger.info(
            "node=retrieve session=%s question='%s'",
            state.get("session_id", "unknown"),
            effective_question[:160],
        )
        start = time.perf_counter()
        retrieved = self.rag.retrieve_documents(
            effective_question,
            self.config.retrieval_top_k,
        )
        scores = [chunk.get("score", 0.0) for chunk in retrieved]
        avg_similarity = sum(scores) / len(scores) if scores else 0.0
        elapsed = time.perf_counter() - start
        self.logger.info(
            "node=retrieve session=%s elapsed=%.3fs retrieved=%d avg_similarity=%.3f max_score=%.3f",
            state.get("session_id", "unknown"),
            elapsed,
            len(retrieved),
            avg_similarity,
            max(scores) if scores else 0.0,
        )
        return {
            "retrieved_chunks": retrieved,
            "retrieval_scores": scores,
            "avg_similarity": avg_similarity,
        }

    def answer_llm(self, state: AgentState) -> AgentState:
        effective_question = state.get("effective_question", "")
        retrieved = state.get("retrieved_chunks", [])
        messages = state.get("messages", [])
        topic_hint = state.get("topic_hint", "")
        conversation_snippet = self.chat_agent._build_conversation_snippet(messages)

        self.logger.info(
            "node=answer_llm session=%s calling_generate_response chunks=%d",
            state.get("session_id", "unknown"),
            len(retrieved),
        )
        start = time.perf_counter()
        rag_response = self.rag.generate_response(
            effective_question,
            retrieved,
            conversation_snippet=conversation_snippet,
            topic_hint=topic_hint,
        )
        elapsed = time.perf_counter() - start
        self.logger.info(
            "node=answer_llm session=%s elapsed=%.3fs llm_response_received answer_len=%d",
            state.get("session_id", "unknown"),
            elapsed,
            len(rag_response.get("answer", "")),
        )
        return {"rag_response": rag_response}

    def decide(self, state: AgentState) -> AgentState:
        session_id = state.get("session_id", "unknown")
        self.logger.debug("node=decide session=%s entering", session_id)
        start = time.perf_counter()
        rag_response = state.get("rag_response", {}) or {}
        metrics_raw = rag_response.get("metrics", {})
        if not isinstance(metrics_raw, dict):
            self.logger.warning(
                "node=decide session=%s metrics_not_dict type=%s",
                session_id,
                type(metrics_raw).__name__,
            )
            metrics = {}
        else:
            metrics = metrics_raw

        try:
            clarifying_question = self._safe_strip(metrics.get("clarifying_question"))
            abstained = bool(metrics.get("abstained", False))
            interpreted_question = self._safe_strip(metrics.get("interpreted_question"))

            decision: Literal["answer", "clarification", "abstain"]
            answer_text = self._safe_strip(rag_response.get("answer"))
            awaiting = False
            new_clarify_count = state.get("clarify_count", 0)

            if abstained and clarifying_question:
                decision = "clarification"
                answer_text = clarifying_question
                awaiting = True
                new_clarify_count = new_clarify_count + 1
            elif abstained:
                decision = "abstain"
                answer_text = "This question cannot be answered with the available information."
            else:
                decision = "answer"

            elapsed = time.perf_counter() - start
            self.logger.info(
                "node=decide session=%s elapsed=%.3fs decision=%s abstained=%s clarifying=%s",
                session_id,
                elapsed,
                decision,
                abstained,
                bool(clarifying_question),
            )

            updates: AgentState = {
                "decision": decision,
                "answer_text": (
                    answer_text
                    or clarifying_question
                    or "I'm sorry, I don't have that information."
                ),
                "clarification_question": clarifying_question,
                "awaiting_clarification": awaiting,
                "interpreted_question": interpreted_question
                or self._safe_strip(state.get("effective_question")),
            }
            if new_clarify_count != state.get("clarify_count"):
                updates["clarify_count"] = new_clarify_count

            return updates

        except Exception as exc:
            self.logger.exception("node=decide session=%s error=%s", session_id, exc)
            fallback_answer = (
                "I ran into an internal error while deciding how to respond. "
                "Please try rephrasing your question."
            )
            return {
                "decision": "abstain",
                "answer_text": fallback_answer,
                "clarification_question": "",
                "awaiting_clarification": False,
                "interpreted_question": self._safe_strip(state.get("effective_question")),
            }

    def finalize(self, state: AgentState) -> AgentState:
        messages = state.get("messages", [])
        rag_response = state.get("rag_response", {})
        retrieved = state.get("retrieved_chunks", [])
        self.logger.info(
            "node=finalize session=%s decision=%s retrieved=%d avg_similarity=%.3f",
            state.get("session_id", "unknown"),
            state.get("decision"),
            len(retrieved),
            state.get("avg_similarity", 0.0),
        )
        try:
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
        except Exception as exc:
            self.logger.exception(
                "node=finalize session=%s metrics_generation_failed: %s",
                state.get("session_id", "unknown"),
                exc,
            )
            fallback_metrics = dict(rag_response.get("metrics", {}) or {})
            metrics = {
                **fallback_metrics,
                "route_metrics": dict(fallback_metrics.get("route_metrics", {"decision": state.get("decision")})),
            }

        # Update persistent metadata for next turn
        decision = state.get("decision")
        interpreted_question = state.get("interpreted_question", "")
        last_question = state.get("last_question", "")
        if decision == "clarification":
            awaiting_clarification = True
            last_clarification = state.get("clarification_question", "")
            topic_hint = last_question or interpreted_question
            next_last_question = last_question
        else:
            awaiting_clarification = False
            last_clarification = ""
            next_last_question = interpreted_question
            topic_hint = interpreted_question

        sources = self.chat_agent._extract_sources_from_rag(rag_response)
        decision = state.get("decision")
        retrieval_error = getattr(self.rag, "last_retrieval_error", None)
        route_metrics = metrics.get("route_metrics") or {}
        generated_by = "answer_llm"

        if state.get("frustration_triggered"):
            generated_by = "frustration_handler"
        elif decision == "clarification":
            generated_by = "clarification_guard"
        elif decision == "abstain":
            if route_metrics.get("decision") == "error" or retrieval_error:
                generated_by = "retrieval_error_handler"
            elif not route_metrics.get("above_threshold", False):
                generated_by = "router_guard"
            else:
                generated_by = "answer_guard"

        route_metrics["generated_by"] = generated_by
        route_metrics.setdefault("decision", decision)
        metrics["generated_by"] = generated_by
        metrics["route_metrics"] = route_metrics

        if decision == "abstain" and isinstance(metrics.get("context_utilization"), dict):
            metrics["context_utilization"] = "0%"

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
            "generated_by": generated_by,
        }
        self.logger.info(
            "node=finalize session=%s generated_by=%s answer_len=%d",
            state.get("session_id", "unknown"),
            generated_by,
            len(response["answer"]),
        )

        if state.get("appended_history"):
            response["rephrased_input"] = state.get("effective_question", "")
        if state.get("clarification_question"):
            response["clarification_question"] = state.get("clarification_question")

        if retrieval_error and decision != "clarification":
            self.logger.warning(
                "node=finalize session=%s retrieval_error=%s",
                state.get("session_id", "unknown"),
                retrieval_error,
            )
            response["answer"] = (
                "I ran into a connection issue while retrieving information. "
                "Please try again in a moment or adjust your question."
            )
            response["generated_by"] = "retrieval_error_handler"
            metrics["generated_by"] = "retrieval_error_handler"
            metrics["route_metrics"]["decision"] = "error"
            metrics["route_metrics"]["retrieval_error"] = retrieval_error
            metrics["route_metrics"]["generated_by"] = "retrieval_error_handler"
            awaiting_clarification = False
            last_clarification = ""

        updates: AgentState = {
            "metrics": metrics,
            "response": response,
            "awaiting_clarification": awaiting_clarification,
            "last_clarification": last_clarification,
            "topic_hint": topic_hint,
            "messages": [{"role": "assistant", "content": response["answer"]}],
        }

        updates["last_question"] = next_last_question

        # reset last retrieval error for next turn
        if hasattr(self.rag, "last_retrieval_error"):
            self.rag.last_retrieval_error = None

        return updates

    # Helpers ------------------------------------------------------------

    def invoke(self, state: AgentState) -> AgentState:
        return self.graph.invoke(state)

    @staticmethod
    def _safe_strip(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return ""
        try:
            return str(value).strip()
        except Exception:
            return ""
