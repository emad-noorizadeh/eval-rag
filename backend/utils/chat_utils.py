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
Chat Utilities for Chat Agent

This module provides utility functions for the chat agent system, including conversation formatting,
response creation, validation, and error handling. These utilities support the chat interface
and ensure consistent data formatting across the application.

Key Features:
- Conversation history formatting and validation
- Source extraction and formatting for display
- Session management utilities
- Error response formatting
- Message sanitization and type detection
- Response creation and standardization

Author: Emad Noorizadeh
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def format_conversation_history(messages: List[Dict[str, Any]], max_messages: int = 10) -> List[Dict[str, str]]:
    """
    Format conversation history for API consumption.
    
    Args:
        messages: List of conversation messages
        max_messages: Maximum number of messages to include
        
    Returns:
        Formatted conversation history
    """
    if not messages:
        return []
    
    # Take the last max_messages messages
    recent_messages = messages[-max_messages:]
    
    formatted = []
    for msg in recent_messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            formatted.append({
                "role": msg["role"],
                "content": str(msg["content"])
            })
    
    return formatted


def extract_sources_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract and format sources from retrieved chunks for display in the UI.
    
    This function normalizes chunk data from different sources (router format vs RAG format)
    into a consistent format for display in the frontend. It handles both the router's
    simplified format and the RAG's detailed format with metadata.
    
    Logic:
    1. Iterate through each chunk in the input list
    2. Detect format type based on available keys (cid vs chunk_id)
    3. Extract and format relevant fields for display
    4. Truncate text content for better UI presentation
    5. Return standardized source objects
    
    Format Handling:
    - Router format: {"cid": "C1", "text": "...", "score": 0.73}
    - RAG format: {"chunk_id": "chunk_123", "doc_id": "doc_456", "text": "...", "score": 0.73, "metadata": {...}}
    
    Args:
        chunks: List of retrieved chunks from either router or RAG system
        
    Returns:
        List of formatted source objects with standardized keys:
        - chunk_id: Unique identifier for the chunk
        - doc_id: Document identifier (empty for router format)
        - text: Truncated text content (200 chars max)
        - score: Similarity score
        - metadata: Additional metadata (empty dict for router format)
        
    Example:
        >>> chunks = [{"cid": "C1", "text": "Long text...", "score": 0.8}]
        >>> extract_sources_from_chunks(chunks)
        [{"chunk_id": "C1", "doc_id": "", "text": "Long text...", "score": 0.8, "metadata": {}}]
    """
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


def create_session_response(session_id: str, created_at: datetime, timeout_minutes: int = 30) -> Dict[str, Any]:
    """
    Create a session response object.
    
    Args:
        session_id: The session ID
        created_at: When the session was created
        timeout_minutes: Session timeout in minutes
        
    Returns:
        Session response dictionary
    """
    return {
        "session_id": session_id,
        "created_at": created_at.isoformat(),
        "remaining_time": f"{timeout_minutes}m",
        "timeout_minutes": timeout_minutes
    }


def validate_chat_request(message: str, session_id: str) -> Dict[str, Any]:
    """
    Validate a chat request.
    
    Args:
        message: The user message
        session_id: The session ID
        
    Returns:
        Validation result with success status and any errors
    """
    errors = []
    
    if not message or not message.strip():
        errors.append("Message cannot be empty")
    
    if not session_id or not session_id.strip():
        errors.append("Session ID is required")
    
    if len(message) > 1000:
        errors.append("Message is too long (max 1000 characters)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def format_error_response(error: str, session_id: str) -> Dict[str, Any]:
    """
    Format an error response.
    
    Args:
        error: Error message
        session_id: Session ID
        
    Returns:
        Formatted error response
    """
    return {
        "answer": f"I apologize, but I encountered an error: {error}",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "confidence": 0.0,
            "faithfulness": 0.0,
            "completeness": 0.0,
            "abstained": True,
            "answer_type": "error",
            "reasoning_notes": f"Error: {error}",
            "missing_information": [],
            "context_utilization": "N/A (Error occurred)"
        },
        "sources": [],
        "retrieval_metadata": {
            "method": "error",
            "total_chunks": 0,
            "routing_strategy": "error"
        }
    }


def create_metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of metrics for display.
    
    Args:
        metrics: Raw metrics dictionary
        
    Returns:
        Formatted metrics summary
    """
    return {
        "confidence": metrics.get("confidence", "Unknown"),
        "faithfulness": metrics.get("faithfulness", 0.0),
        "completeness": metrics.get("completeness", 0.0),
        "abstained": metrics.get("abstained", False),
        "answer_type": metrics.get("answer_type", "unknown"),
        "reasoning_notes": metrics.get("reasoning_notes", ""),
        "missing_information": metrics.get("missing_information", []),
        "context_utilization": metrics.get("context_utilization", "0%")
    }


def extract_retrieval_metadata(router_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract retrieval metadata from router result.
    
    Args:
        router_result: Router execution result
        config: Chat configuration
        
    Returns:
        Retrieval metadata dictionary
    """
    return {
        "method": config.get("retrieval_method", "semantic"),
        "total_chunks": len(router_result.get("retrieved", [])),
        "routing_strategy": config.get("routing_strategy", "intelligent"),
        "similarity_threshold": config.get("similarity_threshold", 0.45),
        "top_k": config.get("retrieval_top_k", 10)
    }


def create_chat_response(
    answer: str,
    session_id: str,
    metrics: Dict[str, Any],
    sources: List[Dict[str, Any]],
    retrieval_metadata: Dict[str, Any],
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized chat response.
    
    Args:
        answer: The generated answer
        session_id: Session ID
        metrics: RAG metrics
        sources: Retrieved sources
        retrieval_metadata: Retrieval metadata
        additional_data: Any additional data to include
        
    Returns:
        Formatted chat response
    """
    response = {
        "answer": answer,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "sources": sources,
        "retrieval_metadata": retrieval_metadata
    }
    
    if additional_data:
        response.update(additional_data)
    
    return response


def sanitize_message(message: str) -> str:
    """
    Sanitize user message for processing.
    
    Args:
        message: Raw user message
        
    Returns:
        Sanitized message
    """
    if not message:
        return ""
    
    # Remove excessive whitespace
    message = " ".join(message.split())
    
    # Truncate if too long
    if len(message) > 1000:
        message = message[:997] + "..."
    
    return message.strip()


def detect_message_type(message: str) -> str:
    """
    Detect the type of user message.
    
    Args:
        message: User message
        
    Returns:
        Message type (question, statement, command, etc.)
    """
    message_lower = message.lower().strip()
    
    if message_lower.endswith("?"):
        return "question"
    elif message_lower.startswith(("tell me", "explain", "describe")):
        return "request"
    elif message_lower.startswith(("show me", "list", "give me")):
        return "command"
    elif message_lower in ["yes", "no", "y", "n", "ok", "okay"]:
        return "confirmation"
    elif any(word in message_lower for word in ["thank", "thanks", "bye", "goodbye"]):
        return "courtesy"
    else:
        return "statement"
