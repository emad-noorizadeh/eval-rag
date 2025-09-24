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
Graph Utilities for Router Graph

This module provides utility functions for the LangGraph-based router system, including conversation
analysis, question processing, and context formatting. These utilities support the intelligent
routing and clarification mechanisms in the chat agent.

Key Features:
- Conversation analysis (clarification detection, follow-up identification)
- Question intent extraction and classification
- LLM prompt generation for clarification and rephrasing
- Context formatting and text processing utilities
- Key term extraction for better matching

Author: Emad Noorizadeh
"""

from typing import List, Dict, Any, Optional
import re


def is_clarification_response(messages: List[Dict[str, str]]) -> bool:
    """
    Check if the last assistant message was a clarification question.
    
    This function analyzes the conversation history to determine if the most recent assistant
    message was asking for clarification. It looks for common clarification phrases and patterns
    that indicate the assistant is seeking more specific information from the user.
    
    Logic:
    1. Iterate through messages in reverse order (most recent first)
    2. Find the last assistant message (excluding the current user message)
    3. Check if the message contains any clarification phrases
    4. Return True if clarification patterns are found
    
    Clarification Phrases Detected:
    - "could you clarify", "can you clarify", "what do you mean"
    - "could you be more specific", "can you be more specific"
    - "what exactly", "which specific", "are you asking about"
    - "do you mean", "are you referring to", "could you provide more details"
    
    Args:
        messages: List of conversation messages with 'role' and 'content' keys
        
    Returns:
        True if the last assistant message was a clarification question, False otherwise
        
    Example:
        >>> messages = [{"role": "user", "content": "what is tier?"}, 
        ...             {"role": "assistant", "content": "Could you clarify which tier you're asking about?"}]
        >>> is_clarification_response(messages)
        True
    """
    if len(messages) < 2:
        return False
    
    last_assistant_msg = ""
    for msg in reversed(messages[:-1]):  # Exclude current user message
        if msg.get("role") == "assistant":
            last_assistant_msg = msg.get("content", "")
            break
    
    clarification_phrases = [
        "could you clarify", "can you clarify", "what do you mean",
        "could you be more specific", "can you be more specific",
        "what exactly", "which specific", "are you asking about",
        "do you mean", "are you referring to", "could you provide more details"
    ]
    
    return any(phrase in last_assistant_msg.lower() for phrase in clarification_phrases)


def is_yes_no_response(message: str) -> bool:
    """
    Check if a message is a yes/no response.
    
    Args:
        message: The user message
        
    Returns:
        True if the message is a yes/no response
    """
    message_lower = message.strip().lower()
    yes_responses = ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "correct", "right"]
    no_responses = ["no", "n", "nope", "nah", "incorrect", "wrong", "not"]
    
    return message_lower in yes_responses or message_lower in no_responses


def is_follow_up_question(message: str) -> bool:
    """
    Check if a message is a follow-up question.
    
    Args:
        message: The user message
        
    Returns:
        True if the message appears to be a follow-up question
    """
    follow_up_indicators = [
        "what about", "how about", "and", "also", "additionally",
        "furthermore", "moreover", "what else", "anything else",
        "can you tell me more", "tell me more", "more details"
    ]
    
    message_lower = message.lower()
    return any(indicator in message_lower for indicator in follow_up_indicators)


def extract_question_intent(message: str) -> Dict[str, Any]:
    """
    Extract the intent and type of a question through pattern analysis.
    
    This function analyzes a user message to determine its question type, intent, and complexity.
    It uses pattern matching and keyword detection to classify questions into different categories
    that can help the router make better decisions about how to handle the query.
    
    Logic:
    1. Analyze question starters (what, how, why, when, where, who, which, can, could, would, should)
    2. Detect intent keywords (define, explain, compare, example, benefit, advantage)
    3. Assess complexity based on message length
    4. Determine if the message is actually a question
    
    Question Types Detected:
    - factual: "what", "which", "who" questions
    - explanatory: "how", "why" questions  
    - temporal_spatial: "when", "where" questions
    - capability: "can", "could", "would", "should" questions
    - list: messages containing "list" or "all"
    - numeric: questions about amounts, costs, quantities
    
    Intent Categories:
    - definition: "define", "what is", "what are"
    - explanation: "explain", "how does", "how do"
    - comparison: "compare", "difference", "vs", "versus"
    - example: "example", "example of", "for instance"
    - evaluation: "benefit", "advantage", "pros", "cons"
    
    Args:
        message: The user message to analyze
        
    Returns:
        Dictionary containing:
        - question_type: Type of question (factual, explanatory, etc.)
        - intent: Intent category (definition, explanation, etc.)
        - complexity: Complexity level (simple, medium, complex)
        - word_count: Number of words in the message
        - is_question: Boolean indicating if it's actually a question
        
    Example:
        >>> extract_question_intent("What is the gold tier?")
        {'question_type': 'factual', 'intent': 'definition', 'complexity': 'simple', 'word_count': 4, 'is_question': True}
    """
    message_lower = message.lower().strip()
    
    # Question type detection
    question_type = "unknown"
    if message_lower.startswith(("what", "which", "who")):
        question_type = "factual"
    elif message_lower.startswith(("how", "why")):
        question_type = "explanatory"
    elif message_lower.startswith(("when", "where")):
        question_type = "temporal_spatial"
    elif message_lower.startswith(("can", "could", "would", "should")):
        question_type = "capability"
    elif "list" in message_lower or "all" in message_lower:
        question_type = "list"
    elif any(word in message_lower for word in ["how much", "how many", "cost", "price", "amount"]):
        question_type = "numeric"
    
    # Intent detection
    intent = "unknown"
    if any(word in message_lower for word in ["define", "definition", "what is", "what are"]):
        intent = "definition"
    elif any(word in message_lower for word in ["explain", "how does", "how do"]):
        intent = "explanation"
    elif any(word in message_lower for word in ["compare", "difference", "vs", "versus"]):
        intent = "comparison"
    elif any(word in message_lower for word in ["example", "example of", "for instance"]):
        intent = "example"
    elif any(word in message_lower for word in ["benefit", "advantage", "pros", "cons"]):
        intent = "evaluation"
    
    # Complexity detection
    complexity = "simple"
    if len(message.split()) > 10:
        complexity = "complex"
    elif len(message.split()) > 5:
        complexity = "medium"
    
    return {
        "question_type": question_type,
        "intent": intent,
        "complexity": complexity,
        "word_count": len(message.split()),
        "is_question": message.strip().endswith("?") or any(word in message_lower for word in ["what", "how", "why", "when", "where", "who", "which"])
    }


def create_clarification_prompt(question: str, context: str) -> str:
    """
    Create a prompt for generating clarification questions.
    
    Args:
        question: The user's question
        context: Available context
        
    Returns:
        Formatted prompt for clarification generation
    """
    return f"""You are a helpful assistant. The user asked: "{question}"

Based on the available context, generate a specific clarification question that helps narrow down what the user is looking for.

Available context:
{context}

Generate a single, clear clarification question that will help you provide a better answer. The question should be:
1. Specific and focused
2. Easy to understand
3. Helpful for narrowing down the scope
4. Professional and friendly

Clarification question:"""


def create_rephrasing_prompt(question: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    Create a prompt for rephrasing questions in context.
    
    Args:
        question: The current question
        conversation_history: Previous conversation messages
        
    Returns:
        Formatted prompt for question rephrasing
    """
    history_text = ""
    if conversation_history:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
    
    return f"""You are a helpful assistant that rephrases questions to be more specific and clear.

Current question: "{question}"

Recent conversation history:
{history_text}

Rephrase the current question to be more specific and clear, taking into account the conversation context. If the question is already clear and complete, return it unchanged.

Rules:
1. If the question is vague, make it more specific
2. If it's a follow-up question, incorporate context from the conversation
3. If it's already clear, return it unchanged
4. Keep the original intent and meaning
5. Make it a complete, standalone question

Rephrased question:"""


def format_context_for_llm(context: str, max_length: int = 2000) -> str:
    """
    Format context for LLM consumption with length limits.
    
    Args:
        context: The raw context
        max_length: Maximum length in characters
        
    Returns:
        Formatted context string
    """
    if len(context) <= max_length:
        return context
    
    # Truncate and add ellipsis
    truncated = context[:max_length-3]
    # Try to break at a sentence boundary
    last_period = truncated.rfind('.')
    if last_period > max_length * 0.8:  # If we can break at a reasonable point
        return truncated[:last_period+1] + "..."
    else:
        return truncated + "..."


def extract_key_terms(text: str) -> List[str]:
    """
    Extract key terms from text for better matching.
    
    Args:
        text: Input text
        
    Returns:
        List of key terms
    """
    # Remove common words and extract meaningful terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    words = re.findall(r'\b\w+\b', text.lower())
    key_terms = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in key_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    return unique_terms
