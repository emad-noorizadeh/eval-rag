# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Router Graph - Intelligent Chat Router with Clarification Support

This module implements a LangGraph-based intelligent router for handling chat conversations
with clarification support. The router uses a state machine approach to process user messages,
retrieve relevant context, and either provide answers or ask for clarification when needed.

Architecture:
- State-based processing with AgentState containing conversation history and routing signals
- Multiple processing nodes: ingest_user, retrieve, route_by_confidence, answer, clarify
- Intelligent rephrasing and context-aware question processing
- Clarification loop prevention with maximum retry limits
- Comprehensive metrics collection for debugging and analysis

Key Features:
- Context-aware question rephrasing using conversation history
- Similarity-based routing with configurable thresholds
- Intelligent clarification question generation
- Abstention handling when context is insufficient
- Comprehensive state management and metrics tracking

Author: Emad Noorizadeh
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal
from typing_extensions import Annotated
import operator
from langgraph.graph import StateGraph, END
from utils.utils_json import coerce_json
from utils.metric_utils import context_utilization_report_with_entities
from utils.conversation_utils import is_ack_or_coref, build_conversation_snippet
from utils.graph_utils import (
    is_clarification_response,
    create_clarification_prompt,
    create_rephrasing_prompt
)
from prompts import get_question_rephrasing_prompt, get_clarification_prompt


# ---- AgentState definition ----
class AgentState(TypedDict, total=False):
    """
    AgentState - Central state object for the LangGraph router system.
    
    This TypedDict defines the complete state that flows through all nodes in the router graph.
    It contains both persistent conversation memory and turn-local processing data that gets
    updated as the conversation progresses through different processing nodes.
    
    State Categories:
    1. Conversation Memory: Persistent chat history that accumulates over time
    2. Turn-Local Data: Processing data that gets overwritten each turn
    3. Configuration: Stable settings that can be set once at session start
    
    Usage:
    - Each node receives the current state and returns updates
    - LangGraph automatically merges updates using the Annotated types
    - State flows through: ingest_user → retrieve → route_by_confidence → (answer|clarify)
    """
    
    # Canonical chat memory - accumulates over time using operator.add
    messages: Annotated[List[Dict[str, str]], operator.add]   # [{"role":"user|assistant","content": "..."}]

    # Turn-local, overwritten each turn (for routing & logging)
    rephrased_question: str                   # Processed question after context-aware rephrasing
    retrieved: List[Dict[str, Any]]          # [{"cid": "C1", "text": "...", "score": 0.73}] - Retrieved chunks
    context: str                              # "C1: ...\n\nC2: ..." - Formatted context for LLM
    valid_chunk_ids: List[str]                # ["C1","C2",...] - Valid chunk identifiers
    avg_score: float                          # Average similarity score of retrieved chunks
    answer_type: str                          # "fact"|"numeric"|"list"|"inference"|"abstain"|"clarification"
    confidence: str                           # "High"|"Medium"|"Low" - Confidence level
    answer: str                               # Final answer sent to the user this turn
    last_clarification: str                   # Last clarification question asked (assistant side)
    clarify_count: int                        # Number of clarifications asked in current session
    rag_response: Optional[Dict[str, Any]]    # Full RAG response for metrics extraction

    # Config knobs (stable; you can set these once at session start)
    top_k: int                                # Number of chunks to retrieve
    threshold: float                          # Similarity threshold for routing decisions
    reclarify_threshold: float                # Threshold for asking follow-up clarifications
    max_clarify: int                          # Maximum number of clarifications allowed
    window_k: int                             # Number of (user,assistant) pairs to keep in messages window
    
    # New fields for context-aware processing
    focus_hint: str                           # Short anchor set during clarification
    conversation_snippet: str                 # Last 3 turns (user/assistant) for generation
    generated_by: str                         # Node name that generated the final response


class SimpleRouterApp:
    """
    Simplified router application with clear, linear processing logic.
    
    This class implements a streamlined LangGraph-based router that processes user messages
    through a series of well-defined nodes. It provides intelligent routing, clarification
    support, and comprehensive answer generation while maintaining simplicity and clarity.
    
    Architecture:
    - Linear processing flow: ingest_user → retrieve → route_by_confidence → (answer|clarify)
    - State-based processing with comprehensive state management
    - Intelligent rephrasing using conversation context
    - Similarity-based routing with configurable thresholds
    - Clarification loop prevention and management
    
    Key Features:
    - Context-aware question rephrasing
    - Intelligent clarification question generation
    - Similarity-based routing decisions
    - Comprehensive metrics collection
    - Error handling and fallback mechanisms
    
    Usage:
    - Initialize with model_manager and rag instances
    - Call invoke() with AgentState to process messages
    - Returns updated state with answer and routing decisions
    """
    
    def __init__(self, model_manager, rag):
        self.model_manager = model_manager
        self.rag = rag
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the simplified router"""
        print("[BUILD] Building simplified router...")
        
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("process_input", self.process_input)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("decide", self.decide)
        graph.add_node("answer", self.answer)
        graph.add_node("clarify", self.clarify)
        
        # Set entry point
        graph.set_entry_point("process_input")
        
        # Add edges
        graph.add_edge("process_input", "retrieve")
        graph.add_edge("retrieve", "decide")
        graph.add_conditional_edges(
            "decide",
            lambda state: state.get("answer_type", "answer"),
            {
                "answer": "answer",
                "clarification": "clarify"
            }
        )
        graph.add_edge("answer", END)
        graph.add_edge("clarify", END)
        
        print("[BUILD] Simplified router built successfully")
        return graph.compile()
    
    def invoke(self, state, config=None):
        """Invoke the router"""
        return self.graph.invoke(state, config=config)
    
    def process_input(self, state: AgentState) -> AgentState:
        print(f"[PROCESS] === PROCESS INPUT START ===")

        messages = state.get("messages", [])
        user_msg = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""

        # Build conversation snippet using utility
        conversation_snippet = build_conversation_snippet(messages, turns=3)
        rephrased = user_msg  # no rewrite

        return {
            "rephrased_question": rephrased,
            "conversation_snippet": conversation_snippet
        }
    
    def retrieve(self, state: AgentState) -> AgentState:
        print(f"[RETRIEVE] === RETRIEVE START ===")
        question = state.get("rephrased_question", "")
        top_k = state.get("top_k", 3)
        focus_hint = state.get("focus_hint", "") or ""

        # Decide if we need augmentation: clarification response or pronoun-only/ack
        ack_like = is_ack_or_coref(question)
        use_union = bool(focus_hint) or ack_like

        if not self.rag:
            print(f"[RETRIEVE] No RAG instance")
            return {
                "retrieved": [],
                "context": "",
                "valid_chunk_ids": [],
                "avg_score": 0.0
            }

        try:
            # Use hint-assisted union retrieval when needed
            if hasattr(self.rag, 'retrieve_documents_union_if_needed'):
                nodes = self.rag.retrieve_documents_union_if_needed(
                    original_query=question,
                    hint_query=focus_hint if use_union else None,
                    n_results=top_k,
                    use_union=use_union
                )
            else:
                # Fallback to regular retrieval
                nodes = self.rag.retrieve_documents(question, n_results=top_k)
            
            print(f"[RETRIEVE] Retrieved {len(nodes)} chunks (union={use_union})")
            
            # Process chunks
            retrieved = []
            valid_chunk_ids = []
            context_parts = []
            scores = []
            
            for i, node in enumerate(nodes):
                cid = f"C{i+1}"
                text = node.get("text", "")
                score = node.get("score", 0.0)
                
                chunk = {
                    "cid": cid,
                    "text": text,
                    "score": score
                }
                retrieved.append(chunk)
                valid_chunk_ids.append(cid)
                context_parts.append(f"{cid}: {text}")
                scores.append(score)
            
            # Filter chunks by similarity threshold
            threshold = state.get("threshold", 0.45)
            from utils.rag_utils import filter_chunks_by_similarity, get_filtering_metrics
            filtered_retrieved = filter_chunks_by_similarity(retrieved, threshold)
            
            # Update context and scores based on filtered chunks
            filtered_context_parts = []
            filtered_scores = []
            filtered_valid_chunk_ids = []
            
            for i, chunk in enumerate(filtered_retrieved):
                cid = f"C{i+1}"
                filtered_context_parts.append(f"{cid}: {chunk['text']}")
                filtered_scores.append(chunk['score'])
                filtered_valid_chunk_ids.append(cid)
            
            context = "\n\n".join(filtered_context_parts)
            avg_score = sum(filtered_scores) / len(filtered_scores) if filtered_scores else 0.0
            
            print(f"[RETRIEVE] Original chunks: {len(retrieved)}, Filtered chunks: {len(filtered_retrieved)}")
            print(f"[RETRIEVE] Average similarity: {avg_score:.3f}")
            print(f"[RETRIEVE] Context length: {len(context)}")
            
            # Get filtering metrics
            filtering_metrics = get_filtering_metrics(retrieved, filtered_retrieved, threshold)
            
            return {
                "retrieved": filtered_retrieved,  # Return filtered chunks
                "context": context,
                "valid_chunk_ids": filtered_valid_chunk_ids,
                "avg_score": avg_score,
                "filtering_metrics": filtering_metrics
            }
            
        except Exception as e:
            print(f"[RETRIEVE] Error: {e}")
            return {
                "retrieved": [],
                "context": "",
                "valid_chunk_ids": [],
                "avg_score": 0.0
            }
    
    def decide(self, state: AgentState) -> AgentState:
        """
        Decide whether to answer or ask for clarification based on retrieval quality.
        
        This node implements the core routing logic that determines whether the retrieved
        context is sufficient to generate a good answer or if clarification is needed.
        It uses similarity scores and other heuristics to make this decision.
        
        Logic:
        1. Analyze the quality of retrieved context using similarity scores
        2. Check if this is a response to a previous clarification
        3. Apply routing rules based on similarity thresholds
        4. Route to either answer generation or clarification
        
        Routing Rules:
        - High similarity (>= threshold): Route to answer generation
        - Low similarity (< threshold): Route to clarification
        - Clarification response: Route to answer generation
        - Maximum clarifications reached: Route to answer generation (with abstention)
        
        Thresholds:
        - threshold: Primary similarity threshold for routing decisions
        - reclarify_threshold: Lower threshold for follow-up clarifications
        - max_clarify: Maximum number of clarifications allowed per session
        
        Args:
            state: Current agent state with retrieved context and similarity scores
            
        Returns:
            Updated state with routing decision (no direct routing, handled by LangGraph)
            
        Example:
            Input: Retrieved chunks with avg_score=0.3, threshold=0.45
            Output: Routes to clarification node
        """
        print(f"[DECIDE] === DECIDE START ===")
        
        avg_score = state.get("avg_score", 0.0)
        retrieved = state.get("retrieved", [])
        threshold = state.get("threshold", 0.45)
        clarify_count = state.get("clarify_count", 0)
        max_clarify = state.get("max_clarify", 2)
        
        print(f"[DECIDE] Average score: {avg_score:.3f}")
        print(f"[DECIDE] Threshold: {threshold}")
        print(f"[DECIDE] Retrieved chunks: {len(retrieved)}")
        print(f"[DECIDE] Clarify count: {clarify_count}/{max_clarify}")
        
        # If we've asked too many clarifications, just answer
        if clarify_count >= max_clarify:
            print(f"[DECIDE] Max clarifications reached ({clarify_count}/{max_clarify}), answering anyway")
            return {"answer_type": "answer"}
        
        # If we have good context, answer
        if retrieved and avg_score >= threshold:
            print(f"[DECIDE] Good context, will answer")
            return {"answer_type": "answer"}
        
        # Otherwise, ask for clarification
        print(f"[DECIDE] Poor context, will clarify")
        return {"answer_type": "clarification"}
    
    def answer(self, state: AgentState) -> AgentState:
        """
        Generate a comprehensive answer using the RAG system with proper abstention logic.
        
        This node handles the actual answer generation using the retrieved context and the
        RAG system. It implements sophisticated abstention logic that can either provide
        a direct answer, ask for clarification, or abstain from answering based on the
        LLM's confidence and the quality of the retrieved context.
        
        Logic:
        1. Call the RAG system to generate a response with metrics
        2. Extract answer, confidence, and abstention information
        3. Apply abstention logic based on LLM response and clarification count
        4. Calculate context utilization and other metrics
        5. Return appropriate response or clarification question
        
        Abstention Logic:
        - If LLM abstains and has clarification question: Return clarification
        - If LLM abstains and no clarification: Return "cannot answer" message
        - If LLM provides answer: Return the answer with metrics
        - Respect maximum clarification limits
        
        Metrics Calculated:
        - Context utilization percentage
        - Confidence, faithfulness, completeness scores
        - Answer type classification
        - Reasoning notes and missing information
        
        Args:
            state: Current agent state with retrieved context and question
            
        Returns:
            Updated state with:
            - answer: Generated answer or clarification question
            - answer_type: Type of response (fact, clarification, abstain)
            - confidence: Confidence level (High, Medium, Low)
            - rag_response: Full RAG response with metrics
            
        Example:
            Input: Question + retrieved context about Bank of America tiers
            Output: "The gold tier requires a $20,000 minimum balance..." with metrics
        """
        print(f"[ANSWER] === ANSWER START ===")
        
        question = state.get("rephrased_question", "")
        context = state.get("context", "")
        retrieved = state.get("retrieved", [])
        clarify_count = state.get("clarify_count", 0)
        
        print(f"[ANSWER] Question: '{question}'")
        print(f"[ANSWER] Context length: {len(context)}")
        print(f"[ANSWER] Retrieved chunks: {len(retrieved)}")
        print(f"[ANSWER] Clarify count: {clarify_count}")
        
        if not self.model_manager or not retrieved:
            return {
                "answer": "This question cannot be answered with the available information.",
                "answer_type": "abstain",
                "confidence": "Low",
                "clarify_count": clarify_count
            }
        
        try:
            # Chunks are already filtered in the retrieve function
            print(f"[ANSWER] Using {len(retrieved)} filtered chunks for generation")
            
            # If no chunks available, return abstention
            if not retrieved:
                print(f"[ANSWER] No chunks available, abstaining")
                return {
                    "answer": "I don't have enough relevant information to answer this question accurately.",
                    "answer_type": "abstain",
                    "confidence": "Low",
                    "clarify_count": clarify_count,
                    "filtered_retrieved": []
                }
            
            # Use the RAG's generate_response method with conversation context and filtered chunks
            response = self.rag.generate_response(
                question=question,
                retrieved=retrieved,
                conversation_snippet=state.get("conversation_snippet", ""),
                topic_hint=state.get("focus_hint", "")
            )
            
            if response and "answer" in response:
                answer = response["answer"]
                metrics = response.get("metrics", {})
                answer_type = metrics.get("answer_type", "answer")
                confidence = metrics.get("confidence", "Medium")
                abstained = metrics.get("abstained", False)
                clarifying_question = metrics.get("clarifying_question", "")
                
                # Calculate context utilization metrics from filtered contexts
                retrieved_contexts = [chunk["text"] for chunk in retrieved]
                if retrieved_contexts:
                    # Use the new advanced context utilization function with question parameter
                    context_utilization_metrics = context_utilization_report_with_entities(
                        question=question,
                        answer=answer,
                        retrieved_contexts=retrieved_contexts,
                        use_bm25_for_best=True,
                        use_embed_alignment=True,  # Enable sentence transformers
                        use_spacy_ner=True,  # Enable spaCy NER
                        spacy_model="en_core_web_sm"
                    )
                    # Update the metrics with the calculated context utilization and filtering info
                    metrics["context_utilization"] = context_utilization_metrics
                    # Get filtering metrics from the retrieve function
                    filtering_metrics = state.get("filtering_metrics", {})
                    metrics["similarity_filtering"] = filtering_metrics
                    response["metrics"] = metrics
                else:
                    context_utilization_metrics = {
                        "precision_token": None,
                        "recall_context": None,
                        "numeric_match": None,
                        "entity_match": {"overall": None, "by_type": {}, "unsupported": []},
                        "per_sentence": [],
                        "qr_alignment": {
                            "cosine_tfidf": None, "answer_covers_question": None,
                            "cosine_embed": None, "answer_covers_question_sem": None
                        },
                        "unsupported_terms": [],
                        "unsupported_terms_per_sentence": [],
                        "unsupported_numbers": [],
                        "summary": "N/A (No context snippets provided)"
                    }
                    metrics["context_utilization"] = context_utilization_metrics
                    # Get filtering metrics from the retrieve function
                    filtering_metrics = state.get("filtering_metrics", {})
                    metrics["similarity_filtering"] = filtering_metrics
                    response["metrics"] = metrics
                
                print(f"[ANSWER] Generated answer: {answer[:100]}...")
                print(f"[ANSWER] Type: {answer_type}, Confidence: {confidence}")
                print(f"[ANSWER] Abstained: {abstained}")
                print(f"[ANSWER] Clarifying question: {clarifying_question}")
                print(f"[ANSWER] Context utilization: {context_utilization_metrics.get('summary', 'N/A')}")
                
                # Apply abstain logic
                if abstained:
                    max_clarify = state.get("max_clarify", 2)
                    if clarify_count < max_clarify and clarifying_question and clarifying_question.strip():
                        # If abstained but has clarification question and haven't hit max, return the clarification
                        print(f"[ANSWER] Abstained with clarification: {clarifying_question}")
                        return {
                            "answer": clarifying_question,
                            "answer_type": "clarification",
                            "confidence": "Low",
                            "last_clarification": clarifying_question,
                            "clarify_count": clarify_count + 1,
                            "rag_response": response,  # Include full RAG response for metrics
                            "filtered_retrieved": retrieved,  # Include filtered chunks
                            "generated_by": "answer_node"  # Node that generated this response
                        }
                    else:
                        # If abstained but no clarification or max clarifications reached, return error message
                        print(f"[ANSWER] Abstained without clarification or max clarifications reached")
                        return {
                            "answer": "This question cannot be answered with the available information.",
                            "answer_type": "abstain",
                            "confidence": "Low",
                            "clarify_count": clarify_count,
                            "rag_response": response,  # Include full RAG response for metrics
                            "filtered_retrieved": retrieved,  # Include filtered chunks
                            "generated_by": "answer_node"  # Node that generated this response
                        }
                else:
                    # Normal answer - return full RAG response for metrics extraction
                    return {
                        "answer": answer,
                        "answer_type": answer_type,
                        "confidence": confidence,
                        "clarify_count": clarify_count,
                        "rag_response": response,  # Include full RAG response for metrics
                        "filtered_retrieved": retrieved,  # Include filtered chunks
                        "generated_by": "answer_node"  # Node that generated this response
                    }
            else:
                return {
                    "answer": "This question cannot be answered with the available information.",
                    "answer_type": "abstain",
                    "confidence": "Low",
                    "clarify_count": clarify_count,
                    "generated_by": "answer_node"  # Node that generated this response
                }
                
        except Exception as e:
            print(f"[ANSWER] Error: {e}")
            return {
                "answer": "This question cannot be answered with the available information.",
                "answer_type": "abstain",
                "confidence": "Low",
                "clarify_count": clarify_count
            }
    
    def clarify(self, state: AgentState) -> AgentState:
        print(f"[CLARIFY] === CLARIFY START ===")
        question = state.get("rephrased_question", "")
        # Use last 3 turns only
        short_history = state.get("conversation_snippet", "")

        if not self.model_manager:
            clarification_question = "Could you clarify the specific program or tier you mean?"
            focus_topic = ""
        else:
            from prompts import get_focus_clarification_prompt
            prompt = get_focus_clarification_prompt(question, short_history)
            raw = self._call_llm(prompt)
            data = coerce_json(raw) or {}
            clarification_question = data.get("clarification_question") or "Could you clarify the specific topic you mean?"
            focus_topic = data.get("focus_topic", "").strip()

        # store focus hint in state (ChatAgent will persist in session)
        clarify_count = state.get("clarify_count", 0)
        mock = {
            "answer": clarification_question,
            "metrics": {
                "answer_type": "clarification",
                "confidence": "Low",
                "abstained": True,
                "context_utilization": {"summary": "N/A (clarification)"},
                "faithfulness": 0.0,
                "completeness": 0.0,
                "reasoning_notes": "Clarification needed",
                "missing_information": ["Specific program/topic"]
            }
        }
        return {
            "answer": clarification_question,
            "answer_type": "clarification",
            "confidence": "Low",
            "last_clarification": clarification_question,
            "clarify_count": clarify_count + 1,
            "rag_response": mock,
            "focus_hint": focus_topic,  # <- NEW
            "generated_by": "clarify_node"  # Node that generated this response
        }
    
    def _is_clarification_response(self, messages: List[Dict[str, str]]) -> bool:
        """Check if the last assistant message was a clarification"""
        return is_clarification_response(messages)
    
    def _create_specific_question_from_clarification(self, messages: List[Dict[str, str]], last_clarification: str = "") -> str:
        """Create a specific question from a clarification response"""
        # Use the last clarification if available
        clarification_text = last_clarification or ""
        
        # Find the last clarification question from messages if not provided
        if not clarification_text:
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    clarification_text = msg.get("content", "")
                    break
        
        clarification_text = clarification_text.lower()
        
        if "tier" in clarification_text:
            return "What are the different tier levels in the Bank of America Preferred Rewards program and what are their requirements?"
        elif "benefits" in clarification_text:
            return "What are the benefits of the Bank of America Preferred Rewards program?"
        elif "enroll" in clarification_text:
            return "How do I enroll in the Bank of America Preferred Rewards program?"
        elif "balance" in clarification_text:
            return "What are the balance requirements for Bank of America Preferred Rewards tiers?"
        elif "preferred rewards" in clarification_text.lower():
            return "What are the different tier levels in the Bank of America Preferred Rewards program and what are their requirements?"
        
        # Fallback
        return "What are the different tier levels in the Bank of America Preferred Rewards program and what are their requirements?"
    
    
    
    def _rephrase_question(self, question: str, messages: List[Dict[str, str]], state: AgentState) -> str:
        """Intelligently rephrase questions based on comprehensive conversation context"""
        if not messages or len(messages) < 2:
            return question
        
        # Get up to 5 turns of conversation history with response metadata
        recent_messages = messages[-10:] if len(messages) >= 10 else messages  # 5 turns = 10 messages (user + assistant)
        
        # Build conversation context with metadata
        conversation_context = []
        for i in range(0, len(recent_messages), 2):
            if i + 1 < len(recent_messages):
                user_msg = recent_messages[i]['content']
                assistant_msg = recent_messages[i + 1]['content']
                
                # Try to get response metadata from state (if available)
                response_metadata = ""
                if i + 1 < len(recent_messages):
                    # This is a simplified approach - in a real implementation, you'd store metadata with each response
                    if "clarification" in assistant_msg.lower() or "clarify" in assistant_msg.lower():
                        response_metadata = " [Response Type: Clarification]"
                    elif "cannot be answered" in assistant_msg.lower() or "insufficient" in assistant_msg.lower():
                        response_metadata = " [Response Type: Abstained]"
                    elif len(assistant_msg) > 100:  # Likely a detailed answer
                        response_metadata = " [Response Type: Detailed Answer]"
                    else:
                        response_metadata = " [Response Type: Brief Answer]"
                
                conversation_context.append(f"User: {user_msg}")
                conversation_context.append(f"Assistant: {assistant_msg}{response_metadata}")
        
        context = "\n".join(conversation_context)
        
        # Use a very conservative rephrasing approach
        topic_context = "This conversation covers various topics based on the documents and context provided."
        examples = """
Case 1 - Single word follow-up that clearly refers to previous context:
- Context: User asked "what is the Villas de la Prada project?" and got detailed answer
- User says: "units"
- Rephrase to: "How many units are in the Villas de la Prada project?"

Case 2 - Already clear question:
- User says: "What is la prada?"
- Keep as: "What is la prada?"

Case 3 - Complete question without reference to previous context:
- User says: "What is the capital of France?" (complete question, no reference to previous conversation)
- Keep as: "What is the capital of France?"

Case 4 - New topic question (different from previous context):
- User says: "what is tier?" (after discussing Villas de la Prada)
- Keep as: "what is tier?" (don't add unrelated context)

Case 5 - Vague question that clearly refers to previous context:
- User says: "tell me more" (after getting specific answer)
- Rephrase to: "Tell me more about [the specific topic from context]"
"""
        
        prompt = get_question_rephrasing_prompt(question, context, topic_context)

        try:
            rephrased = self._call_llm(prompt)
            return rephrased.strip() if rephrased else question
        except Exception as e:
            print(f"[REPHRASE] Error: {e}")
            return question
    
    def _create_clarification_prompt(self, question: str, context: str) -> str:
        """Create a prompt for generating clarification questions"""
        return get_clarification_prompt(question, context)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a text prompt"""
        if not self.model_manager:
            return ""
        
        try:
            response = self.model_manager.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return "Could you please be more specific about what you're looking for?"


def build_router_app(model_manager, rag) -> SimpleRouterApp:
    """Build the simplified router application"""
    return SimpleRouterApp(model_manager, rag)
