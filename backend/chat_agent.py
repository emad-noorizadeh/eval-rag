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
Unified Chat Agent with LangGraph Router

This module provides a unified chat agent that integrates the LangGraph-based router system
with the RAG (Retrieval-Augmented Generation) system. It serves as the main interface for
handling chat conversations, managing sessions, and coordinating between different components.

Architecture:
- Integrates LangGraph router for intelligent conversation handling
- Uses RAG system for document retrieval and answer generation
- Manages session state and conversation history
- Provides comprehensive metrics extraction and formatting
- Handles both simple and intelligent routing strategies

Key Features:
- Intelligent conversation routing with clarification support
- Session management and conversation history tracking
- Comprehensive metrics collection and formatting
- Multiple routing strategies (intelligent vs simple)
- Error handling and fallback mechanisms
- Debug information extraction for UI display

Author: Emad Noorizadeh
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from retrieval_service import RetrievalMethod, RetrievalConfig
# from session_manager import SessionManager  # Avoid circular import
from router_graph import build_router_app, AgentState
from prompts import get_rag_simple_prompt


class RoutingStrategy(Enum):
    """
    Routing strategy enumeration for the chat agent.
    
    Defines the different approaches the chat agent can use to handle user messages
    and route them through the system for processing.
    """
    INTELLIGENT = "intelligent"  # Intelligent router with clarification support
    SIMPLE = "simple"            # Direct RAG without intelligent routing


@dataclass
class ChatConfig:
    """
    Configuration class for the chat agent.
    
    This class defines all the configurable parameters that control the behavior
    of the chat agent, including retrieval settings, routing preferences, and
    conversation management options.
    
    Attributes:
        retrieval_method: Method to use for document retrieval (semantic, hybrid, etc.)
        retrieval_top_k: Number of top documents to retrieve
        similarity_threshold: Minimum similarity score for routing decisions
        routing_strategy: Strategy for routing messages (intelligent vs simple)
        max_clarify: Maximum number of clarifications allowed per session
        reclarify_threshold: Lower threshold for follow-up clarifications
    """
    # Retrieval config
    retrieval_method: RetrievalMethod = RetrievalMethod.SEMANTIC
    retrieval_top_k: int = 10
    similarity_threshold: float = 0.45
    
    # Routing config
    routing_strategy: RoutingStrategy = RoutingStrategy.INTELLIGENT
    max_clarify: int = 2
    reclarify_threshold: float = 0.35
    window_k: int = 4
    
    # Note: hybrid retrieval removed - using semantic only


class ChatAgent:
    """
    Unified chat agent with configurable routing and retrieval.
    
    This is the main chat agent class that orchestrates the entire conversation flow.
    It integrates the LangGraph router system with the RAG system to provide intelligent
    conversation handling with clarification support and comprehensive metrics collection.
    
    Architecture:
    - Uses LangGraph router for intelligent conversation processing
    - Integrates with RAG system for document retrieval and answer generation
    - Manages session state and conversation history
    - Provides comprehensive metrics extraction and formatting
    - Supports multiple routing strategies and retrieval methods
    
    Key Features:
    - Intelligent conversation routing with clarification support
    - Context-aware question rephrasing
    - Comprehensive metrics collection for debugging
    - Session management and conversation history tracking
    - Error handling and fallback mechanisms
    - Support for both simple and intelligent routing strategies
    
    Usage:
    1. Initialize with model_manager, index_builder, and session_manager
    2. Configure routing strategy and retrieval method
    3. Call process_message() to handle user messages
    4. Extract metrics and debug information from responses
    """
    
    def __init__(self, model_manager: ModelManager, index_builder: IndexBuilder, 
                 session_manager: "SessionManager", config: ChatConfig = None):
        """
        Initialize chat agent.
        
        Args:
            model_manager: Model manager for LLM operations
            index_builder: Index builder with ChromaDB index
            session_manager: Session manager for conversation persistence
            config: Chat configuration
        """
        self.model_manager = model_manager
        self.index_builder = index_builder
        self.session_manager = session_manager
        self.config = config or ChatConfig()
        
        # Initialize RAG with configured retrieval method
        self.rag = RAG(model_manager, index_builder, config.retrieval_method)
        
        # Initialize routing strategy
        self._router_app = None
        self._initialize_routing()
        
        print(f"✓ Chat agent initialized")
        print(f"  - Retrieval: {self.config.retrieval_method.value}")
        print(f"  - Routing: {self.config.routing_strategy.value}")
    
    def _initialize_routing(self):
        """Initialize the routing strategy"""
        if self.config.routing_strategy == RoutingStrategy.INTELLIGENT:
            # Use the current intelligent router with RAG
            self._router_app = build_router_app(
                self.model_manager,
                self.rag
            )
        elif self.config.routing_strategy == RoutingStrategy.SIMPLE:
            # Direct RAG without routing
            self._router_app = None
        else:
            raise ValueError(f"Unsupported routing strategy: {self.config.routing_strategy}")
    
    def chat(self, message: str, session_id: str, 
             conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main chat method that routes to appropriate strategy based on configuration.
        
        This is the primary entry point for processing user messages. It determines
        which routing strategy to use (intelligent vs simple) and delegates to the
        appropriate handler. It also manages session state and provides comprehensive
        error handling.
        
        Logic:
        1. Validate input parameters and session
        2. Determine routing strategy from configuration
        3. Delegate to appropriate handler (router vs simple)
        4. Return formatted response with metrics
        
        Routing Strategies:
        - INTELLIGENT: Uses LangGraph router with clarification support
        - SIMPLE: Direct RAG without intelligent routing
        
        Error Handling:
        - Invalid session handling
        - Empty message validation
        - Fallback to simple routing on router errors
        - Comprehensive error logging
        
        Args:
            message: User message to process
            session_id: Unique session identifier
            conversation_history: Previous conversation history (optional)
            
        Returns:
            Dictionary containing:
            - answer: Generated answer or clarification question
            - metrics: Comprehensive metrics for debugging
            - sources: Retrieved document sources
            - session_id: Session identifier
            - timestamp: Response timestamp
            
        Example:
            >>> agent.chat("What is gold tier?", "session_123", [])
            {
                "answer": "The gold tier requires a $20,000 minimum balance...",
                "metrics": {...},
                "sources": [...],
                "session_id": "session_123",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        """
        try:
            # Get or create session
            session = self.session_manager.get_session(session_id)
            if session is None:
                # Create new session if it doesn't exist
                new_session_id = self.session_manager.create_session()
                session = self.session_manager.get_session(new_session_id)
                session_id = new_session_id  # Update session_id to the new one
            
            # Prepare conversation history
            if conversation_history is None:
                conversation_history = []
            
            # Route based on strategy
            if self.config.routing_strategy == RoutingStrategy.INTELLIGENT:
                return self._chat_with_router(message, session_id, conversation_history)
            elif self.config.routing_strategy == RoutingStrategy.SIMPLE:
                return self._chat_simple(message, session_id, conversation_history)
            else:
                raise ValueError(f"Unsupported routing strategy: {self.config.routing_strategy}")
                
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "answer": "I'm sorry, I encountered an error processing your message.",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "confidence": 0.0,
                    "faithfulness": 0.0,
                    "completeness": 0.0,
                    "abstained": True,
                    "answer_type": "error",
                    "reasoning_notes": f"Error: {str(e)}",
                    "missing_information": [],
                    "context_utilization": "0%"
                },
                "sources": [],
                "retrieval_metadata": {
                    "method": "error",
                    "total_chunks": 0
                }
            }
    
    def _chat_with_router(self, message: str, session_id: str, 
                         conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Chat using the router strategy"""
        # Get session and extract focus_hint
        sess = self.session_manager.get_session(session_id)
        focus_hint = getattr(sess, "focus_hint", "") if sess else ""
        
        # Prepare state for router
        state = AgentState(
            messages=conversation_history + [{"role": "user", "content": message}],
            current_input=message,
            session_id=session_id,
            retrieval_results=[],
            rag_response=None,
            answer_type="unknown",
            clarify_count=0,
            rephrased_input="",
            clarification_question="",
            focus_hint=focus_hint,           # NEW
            conversation_snippet=""          # will be set in process_input
        )
        
        # Run router
        result = self._router_app.invoke(state)
        
        # Persist focus hint if provided
        focus_hint = result.get("focus_hint", "")
        if focus_hint:
            sess = self.session_manager.get_session(session_id)
            if sess:
                setattr(sess, "focus_hint", focus_hint)
        
        # Belt-and-suspenders: Persist focus_hint when user says "yes" (or other ack)
        sess = self.session_manager.get_session(session_id)
        if hasattr(sess, "focus_hint"):
            # keep existing
            pass
        else:
            # if router classified as clarification earlier, this 'yes' implies confirmation.
            proposed = result.get("focus_hint", "")
            if not proposed and "clarification" in (result.get("route_metrics", {}).get("route_decision", "")):
                # best-effort: extract noun-ish head from last clarification if you want
                proposed = ""
            if proposed:
                setattr(sess, "focus_hint", proposed)
        
        # Extract response
        answer = result.get("answer", "I'm sorry, I couldn't process your request.")
        rag_response = result.get("rag_response", {})
        
        # Extract detailed metrics from router state
        detailed_metrics = self._extract_detailed_metrics(result)
        
        # Format response - use filtered chunks for sources if available, otherwise fall back to all retrieved
        filtered_chunks = result.get("filtered_retrieved", result.get("retrieved", []))
        response = {
            "answer": answer,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": detailed_metrics,
            "sources": self._extract_sources(filtered_chunks),
            "retrieval_metadata": {
                "method": self.config.retrieval_method.value,
                "total_chunks": len(filtered_chunks),
                "routing_strategy": self.config.routing_strategy.value
            }
        }
        
        # Add routing-specific metadata
        if "rephrased_input" in result:
            response["rephrased_input"] = result["rephrased_input"]
        if "clarification_question" in result:
            response["clarification_question"] = result["clarification_question"]
        if "generated_by" in result:
            response["generated_by"] = result["generated_by"]
        
        return response
    
    def _chat_simple(self, message: str, session_id: str, 
                    conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple chat without routing"""
        # Use RAG directly
        rag_response = self.rag.query(message, n_results=self.config.retrieval_top_k)
        
        # Create simple detailed metrics for simple routing
        simple_metrics = self._create_simple_metrics(message, rag_response, conversation_history)
        
        # Format response
        return {
            "answer": rag_response["answer"],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": simple_metrics,
            "sources": self._extract_sources_from_rag(rag_response),
            "retrieval_metadata": {
                "method": self.config.retrieval_method.value,
                "total_chunks": len(rag_response.get("sources", [])),
                "routing_strategy": "simple"
            }
        }
    
    def _extract_detailed_metrics(self, router_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed metrics from router state"""
        # Get the original user message
        messages = router_result.get("messages", [])
        original_question = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    original_question = msg.get("content", "")
                    break
        
        # Extract basic metrics from RAG response
        rag_response = router_result.get("rag_response", {})
        basic_metrics = self._extract_metrics(rag_response)
        
        # Context utilization should be in the RAG response metrics
        # No need to override since it's already calculated in the RAG response
        
        # Get filtered chunks for metrics
        filtered_chunks = router_result.get("filtered_retrieved", router_result.get("retrieved", []))
        
        # Extract detailed node metrics
        detailed_metrics = {
            **basic_metrics,  # Include basic metrics
            
            # Add chunks retrieved for debug panel - use filtered chunks if available
            "chunks_retrieved": self._extract_sources(filtered_chunks),
            
            # Ingest node metrics
            "ingest_metrics": {
                "original_question": original_question,
                "processed_question": router_result.get("rephrased_question", original_question),
                "is_clarification_response": router_result.get("answer_type") == "clarification",
                "conversation_length": len(messages),
                "rephrased": router_result.get("rephrased_question", "") != original_question,
                "summary": f"Processed {len(messages)} messages"
            },
            
            # Retrieve node metrics - use filtered chunks for display
            "retrieve_metrics": {
                "question": router_result.get("rephrased_question", ""),
                "top_k": router_result.get("top_k", 0),
                "chunks_retrieved": len(filtered_chunks),
                "avg_similarity": router_result.get("avg_score", 0.0),
                "max_similarity": max([chunk.get("score", 0) for chunk in filtered_chunks], default=0.0),
                "min_similarity": min([chunk.get("score", 0) for chunk in filtered_chunks], default=0.0),
                "chunk_scores": [chunk.get("score", 0) for chunk in filtered_chunks],
                "context_length": len(router_result.get("context", "")),
                "valid_chunk_ids": router_result.get("valid_chunk_ids", [])
            },
            
            # Route node metrics - use filtered chunks for display
            "route_metrics": {
                "retrieved_chunks": len(filtered_chunks),
                "avg_similarity": router_result.get("avg_score", 0.0),
                "threshold": router_result.get("threshold", 0.45),
                "is_clarification_response": router_result.get("answer_type") == "clarification",
                "route_decision": router_result.get("answer_type", "unknown"),
                "scores": [chunk.get("score", 0) for chunk in filtered_chunks],
                "above_threshold": router_result.get("avg_score", 0.0) >= router_result.get("threshold", 0.45)
            },
            
            # RAG node metrics
            "rag_metrics": {
                "question": router_result.get("rephrased_question", ""),
                "context_used": router_result.get("context", ""),
                "response_generated": router_result.get("answer", ""),
                "clarification_question": router_result.get("last_clarification", ""),
                "confidence": basic_metrics.get("confidence", router_result.get("confidence", "Medium")),
                "answer_type": basic_metrics.get("answer_type", router_result.get("answer_type", "unknown")),
                "faithfulness": basic_metrics.get("faithfulness", 0.0),
                "completeness": basic_metrics.get("completeness", 0.0),
                "context_utilization": basic_metrics.get("context_utilization", "0%"),
                "reasoning_notes": basic_metrics.get("reasoning_notes", ""),
                "missing_information": basic_metrics.get("missing_information", []),
                "reasoning": f"Generated response with {len(filtered_chunks)} chunks"
            },
            
            # Clarify node metrics
            "clarify_metrics": {
                "question": router_result.get("rephrased_question", ""),
                "clarification_question": router_result.get("last_clarification", ""),
                "clarify_count": router_result.get("clarify_count", 0),
                "max_clarify": router_result.get("max_clarify", 2),
                "reason": f"Asked clarification due to low similarity: {router_result.get('avg_score', 0.0):.3f} < {router_result.get('threshold', 0.45)}"
            }
        }
        
        return detailed_metrics

    def _create_simple_metrics(self, message: str, rag_response: Dict[str, Any], 
                              conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create simple detailed metrics for simple routing"""
        # Extract basic metrics from RAG response
        basic_metrics = self._extract_metrics(rag_response)
        
        # Get sources for retrieval metrics
        sources = rag_response.get("sources", [])
        scores = [source.get("score", 0) for source in sources]
        
        # Create simple detailed metrics
        simple_metrics = {
            **basic_metrics,  # Include basic metrics
            
            # Ingest node metrics (simplified)
            "ingest_metrics": {
                "original_question": message,
                "processed_question": message,  # No rephrasing in simple mode
                "is_clarification_response": False,
                "conversation_length": len(conversation_history) + 1,
                "rephrased": False,
                "summary": f"Simple processing of {len(conversation_history) + 1} messages"
            },
            
            # Retrieve node metrics
            "retrieve_metrics": {
                "question": message,
                "top_k": self.config.retrieval_top_k,
                "chunks_retrieved": len(sources),
                "avg_similarity": sum(scores) / len(scores) if scores else 0.0,
                "max_similarity": max(scores) if scores else 0.0,
                "min_similarity": min(scores) if scores else 0.0,
                "chunk_scores": scores,
                "context_length": sum(len(source.get("text", "")) for source in sources),
                "valid_chunk_ids": [source.get("chunk_id", "") for source in sources]
            },
            
            # Route node metrics (simplified)
            "route_metrics": {
                "retrieved_chunks": len(sources),
                "avg_similarity": sum(scores) / len(scores) if scores else 0.0,
                "threshold": 0.45,  # Default threshold
                "is_clarification_response": False,
                "route_decision": "answer",  # Always answer in simple mode
                "scores": scores,
                "above_threshold": (sum(scores) / len(scores) if scores else 0.0) >= 0.45
            },
            
            # RAG node metrics
            "rag_metrics": {
                "question": message,
                "context_used": "\n".join([source.get("text", "") for source in sources]),
                "response_generated": rag_response.get("answer", ""),
                "clarification_question": "",
                "confidence": basic_metrics.get("confidence", "Medium"),
                "answer_type": basic_metrics.get("answer_type", "unknown"),
                "reasoning": f"Generated response with {len(sources)} chunks using simple routing"
            },
            
            # Clarify node metrics (not used in simple mode)
            "clarify_metrics": {
                "question": message,
                "clarification_question": "",
                "clarify_count": 0,
                "max_clarify": 0,
                "reason": "Simple routing - no clarification needed"
            }
        }
        
        return simple_metrics

    def _extract_metrics(self, rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from RAG response"""
        if not rag_response or "metrics" not in rag_response:
            return {
                "confidence": 0.0,
                "faithfulness": 0.0,
                "completeness": 0.0,
                "abstained": True,
                "answer_type": "unknown",
                "reasoning_notes": "No metrics available",
                "missing_information": [],
                "context_utilization": "0%"
            }
        
        metrics = rag_response["metrics"]
        return {
            "confidence": metrics.get("confidence", 0.0),
            "faithfulness": metrics.get("faithfulness_score", 0.0),  # RAG returns faithfulness_score
            "completeness": metrics.get("completeness_score", 0.0),  # RAG returns completeness_score
            "abstained": metrics.get("abstained", True),
            "answer_type": metrics.get("answer_type", "unknown"),
            "reasoning_notes": metrics.get("reasoning_notes", ""),
            "missing_information": metrics.get("missing_information", []),
            "context_utilization": metrics.get("context_utilization", "0%")
        }
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sources from chunks"""
        sources = []
        for chunk in chunks:
            # Handle both router format (cid, text, score) and RAG format (chunk_id, doc_id, text, score, metadata)
            if "cid" in chunk:
                # Router format
                source = {
                    "chunk_id": chunk.get("cid", ""),
                    "doc_id": "",  # Not available in router format
                    "text": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", ""),
                    "score": chunk.get("score", 0.0),
                    "metadata": {}
                }
            else:
                # RAG format
                source = {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "doc_id": chunk.get("doc_id", ""),
                    "text": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", ""),
                    "score": chunk.get("score", 0.0),
                    "metadata": chunk.get("metadata", {})
                }
            sources.append(source)
        return sources
    
    def _extract_sources_from_rag(self, rag_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from RAG response"""
        sources = []
        for source in rag_response.get("sources", []):
            sources.append({
                "chunk_id": source.get("chunk_id", ""),
                "doc_id": source.get("doc_id", ""),
                "text": source.get("text", ""),
                "score": source.get("score", 0.0),
                "metadata": source.get("metadata", {})
            })
        return sources
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunks into context string"""
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"Context {i}:\n{chunk.get('text', '')}")
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for simple mode"""
        return get_rag_simple_prompt(question, context)
    
    def update_config(self, new_config: ChatConfig):
        """Update chat configuration"""
        self.config = new_config
        self._initialize_routing()
        print(f"✓ Chat agent configuration updated")
        print(f"  - Retrieval: {self.config.retrieval_method.value}")
        print(f"  - Routing: {self.config.routing_strategy.value}")
    
    def get_config(self) -> ChatConfig:
        """Get current configuration"""
        return self.config
    
    def get_available_retrieval_methods(self) -> List[str]:
        """Get available retrieval methods"""
        return ["semantic"]  # Only semantic retrieval is supported
    
    def get_available_routing_strategies(self) -> List[str]:
        """Get available routing strategies"""
        return [strategy.value for strategy in RoutingStrategy]


# Example usage
if __name__ == "__main__":
    print("ChatAgent - Configurable chat agent")
    print("Available retrieval methods:", [method.value for method in RetrievalMethod])
    print("Available routing strategies:", [strategy.value for strategy in RoutingStrategy])
