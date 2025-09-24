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
Centralized LLM Prompts Management

This module contains all LLM prompts used throughout the RAG system.
This provides a single location to view, manage, and update all prompts.

Categories:
- RAG System Prompts
- Router & Conversation Prompts  
- Metadata Extraction Prompts
- Utility Prompts
"""

from typing import List, Dict, Any


# =============================================================================
# RAG SYSTEM PROMPTS
# =============================================================================

def get_rag_main_prompt() -> str:
    """
    Context-aware, no-rewrite RAG prompt.
    Uses three lanes:
      - Conversation (non-factual): last 3 turns max
      - Topic hint (non-factual): short anchor for pronouns/acks
      - Grounding context (factual): retrieved chunks w/ IDs

    Requires strict JSON with an extra "interpreted_question".
    """
    return (
        "You are a financial assistant.\n"
        "You must base all factual statements ONLY on the Grounding context.\n"
        "Conversation and Topic hint are for disambiguation and tone ONLY; they are NOT sources of facts.\n"
        "If Grounding context is insufficient for the user request, abstain.\n\n"

        "----- Conversation (non-factual; up to 3 turns) -----\n"
        "{conversation_snippet}\n\n"

        "----- Topic hint (non-factual) -----\n"
        "{topic_hint}\n\n"

        "----- Grounding context (factual; cite chunk IDs) -----\n"
        "{context}\n\n"

        "----- User message -----\n"
        "{question}\n\n"

        "INTERPRETATION RULES:\n"
        "- If the user message is an acknowledgement (e.g., 'yes', 'ok', 'that one'), interpret it as confirming the Topic hint.\n"
        "- Do NOT extract facts from Conversation or Topic hint.\n"
        "- Use ONLY Grounding context for facts and cite valid chunk IDs.\n"
        "- If a needed fact is missing from Grounding, abstain and include a clarifying question.\n\n"

        "OUTPUT JSON (single line, strict JSON):\n"
        "{{\n"
        "  \"answer\": \"\",\n"
        "  \"evidence\": [],\n"
        "  \"missing\": \"\",\n"
        "  \"confidence\": \"\",\n"
        "  \"faithfulness_score\": 0.0,\n"
        "  \"completeness_score\": 0.0,\n"
        "  \"answer_type\": \"\",\n"
        "  \"abstained\": false,\n"
        "  \"reasoning_notes\": \"\",\n"
        "  \"clarifying_question\": \"\",\n"
        "  \"interpreted_question\": \"\"\n"
        "}}\n\n"
        "Cite evidence ONLY from these chunk IDs: {valid_chunk_ids}. "
        "Do not invent new IDs. Return exactly one JSON object on one line."
    )


def get_focus_clarification_prompt(question: str, short_history: str) -> str:
    """
    Ask a single clarification AND propose a concise focus topic.
    Return strict JSON.
    """
    return f"""You are helping to clarify an ambiguous user question.

Short recent history (non-factual):
{short_history}

User message: "{question}"

Rules:
- Ask exactly ONE specific clarification question.
- Also propose a concise "focus_topic" (<= 8 words) that names the likely subject the user means.
- Do NOT include any facts; no brand-new claims. This is only a targeting aid.
- JSON only, one line.

Return JSON:
{{"clarification_question": "...", "focus_topic": "..."}}"""


def get_rag_simple_prompt(question: str, context: str) -> str:
    """
    Simple RAG prompt for basic Q&A without metrics.
    
    Used by the simple chat mode for straightforward question answering.
    """
    return f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:"""


# =============================================================================
# ROUTER & CONVERSATION PROMPTS
# =============================================================================

def get_question_rephrasing_prompt(question: str, context: str, topic_context: str) -> str:
    """
    Prompt for rephrasing user questions to be more specific and complete.
    
    This prompt helps convert vague or follow-up questions into clear,
    specific questions that can be better answered by the RAG system.
    """
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
    
    return f"""You are a helpful assistant that rephrases user questions to be more specific and complete based on conversation context.

CONVERSATION HISTORY (up to 5 turns):
{context}

CURRENT USER QUESTION: "{question}"

CONTEXT: {topic_context}

REPHRASING RULES:
1. ONLY rephrase if the question is clearly a follow-up to the previous conversation context.
2. If the question appears to be about a NEW topic, return it unchanged.
3. If the question is already clear and specific, return it unchanged.
4. If the question looks complete and doesn't have reference or coreference to previous conversation, return it unchanged.
5. Only rephrase single-word questions that clearly refer to something mentioned in the previous conversation.
6. Do NOT add context from previous conversation unless it's clearly related.

EXAMPLES OF REPHRASING:
{examples}

SPECIFIC INSTRUCTIONS:
- If the question is already clear and specific (like "What is la prada?"), return it unchanged
- If the question looks complete and doesn't have reference or coreference to previous conversation (like "What is the capital of France?"), return it unchanged
- If the question appears to be about a new topic (like "what is tier?" after discussing Villas de la Prada), return it unchanged
- Only rephrase when the connection to previous context is OBVIOUS and CLEAR
- Do NOT force connections between unrelated topics
- When in doubt, return the original question unchanged
- Return ONLY the rephrased question, no explanations or additional text

REPHRASED QUESTION:"""


def get_clarification_prompt(question: str, context: str) -> str:
    """
    Prompt for generating clarification questions when user input is vague.
    
    This helps the system ask for more specific information when the user's
    question is too broad or unclear to answer effectively.
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


def get_rephrasing_prompt_legacy(question: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    Legacy rephrasing prompt for backward compatibility.
    
    This is the older version of the rephrasing prompt used in graph_utils.py.
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


# =============================================================================
# METADATA EXTRACTION PROMPTS
# =============================================================================

def get_metadata_extraction_prompt(text: str) -> str:
    """
    Comprehensive metadata extraction prompt for document analysis.
    
    This prompt extracts structured metadata from documents including
    entities, categories, sentiment, and other document properties.
    """
    return f"""
Extract comprehensive metadata from the following document text. Provide your response as a JSON object with the specified fields.

Document Text:
{text}

Please extract and return the following metadata in JSON format:

{{
    "title": "Main title or headline of the document",
    "summary": "Brief 2-3 sentence summary of the document content",
    "categories": ["category1", "category2", "category3"],
    "entities": {{
        "people": ["person1", "person2"],
        "organizations": ["org1", "org2"],
        "locations": ["location1", "location2"],
        "products": ["product1", "product2"],
        "technologies": ["tech1", "tech2"]
    }},
    "sentiment": "positive|negative|neutral",
    "language": "detected language code (e.g., 'en', 'es', 'fr')",
    "topics": ["topic1", "topic2", "topic3"],
    "key_phrases": ["phrase1", "phrase2", "phrase3"],
    "document_type": "article|report|manual|email|legal|financial|technical|other",
    "confidence_scores": {{
        "overall": 0.95,
        "categories": 0.90,
        "entities": 0.85,
        "sentiment": 0.80
    }}
}}

Guidelines:
- Be precise and concise
- Categories should be relevant and specific
- Extract only clear, unambiguous entities
- Confidence scores should reflect your certainty (0.0 to 1.0)
- If information is not available, use null
- Keep lists to maximum 5 items each
- Focus on the most important information

Respond with only the JSON object, no additional text.
"""


def get_document_type_prompt(text: str, url: str = "") -> str:
    """
    Prompt for extracting document type classification.
    
    Classifies documents into specific types like landing, disclosure, FAQ, etc.
    """
    return f"""Analyze the following document content and determine its type. Return ONLY one of these exact values: landing, disclosure, FAQ, terms, form, promo

Document URL: {url}
Document Content (first 2000 chars): {text[:2000]}

Rules:
- landing: Marketing or promotional pages
- disclosure: Legal disclosures, terms and conditions
- FAQ: Frequently asked questions
- terms: Terms of service, legal terms
- form: Application forms, registration forms
- promo: Promotional content, offers

Return only the type (e.g., "FAQ"):"""


def get_title_extraction_prompt(text: str, url: str = "") -> str:
    """
    Prompt for extracting document titles.
    
    Extracts the main title or headline from document content.
    """
    return f"""Extract the main title of this document. Return ONLY the title, no explanations.

Document URL: {url}
Document Content (first 1500 chars): {text[:1500]}

Rules:
- Extract the main title or headline
- If no clear title exists, return "Untitled Document"
- Keep it concise (under 100 characters)
- Don't include explanations or additional text

Title:"""


def get_product_entities_prompt(text: str) -> str:
    """
    Prompt for extracting product and service entities.
    
    Extracts product names, service names, and program names from documents.
    """
    return f"""Extract product names, service names, and program names from this document. Return ONLY a JSON array of strings.

Document Content (first 2000 chars): {text[:2000]}

Rules:
- Extract only actual product/service/program names mentioned in the document
- Do NOT invent or infer entities not explicitly mentioned
- Do NOT include generic terms like "banking", "services", "program"
- Return as JSON array: ["Product 1", "Service 2", "Program 3"]
- If none found, return: []

JSON array:"""


def get_categories_prompt(text: str, title: str = "") -> str:
    """
    Prompt for categorizing documents.
    
    Generates relevant categories for document classification.
    """
    return f"""Categorize this document. Return ONLY a JSON array of 2-4 relevant categories.

Document Title: {title}
Document Content (first 1500 chars): {text[:1500]}

Rules:
- Choose 2-4 most relevant categories
- Be specific and descriptive
- Use business/financial terminology when appropriate
- Return as JSON array: ["Category 1", "Category 2", "Category 3"]
- If unclear, return: ["General"]

JSON array:"""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_context_for_llm(context: str, max_length: int = 2000) -> str:
    """
    Format context for LLM consumption with length limits.
    
    Args:
        context: The context string to format
        max_length: Maximum length before truncation
        
    Returns:
        Formatted context string
    """
    if len(context) <= max_length:
        return context
    
    # Truncate and add ellipsis
    truncated = context[:max_length - 3]
    return truncated + "..."


def get_prompt_summary() -> Dict[str, Any]:
    """
    Get a summary of all available prompts.
    
    Returns:
        Dictionary with prompt categories and their descriptions
    """
    return {
        "rag_system": {
            "main_prompt": "Primary RAG prompt for structured responses with metrics",
            "simple_prompt": "Basic Q&A prompt without metrics"
        },
        "router_conversation": {
            "question_rephrasing": "Rephrases vague questions to be more specific",
            "clarification": "Generates clarification questions for vague input",
            "rephrasing_legacy": "Legacy rephrasing prompt for backward compatibility"
        },
        "metadata_extraction": {
            "comprehensive": "Extracts comprehensive document metadata",
            "document_type": "Classifies document types",
            "title_extraction": "Extracts document titles",
            "product_entities": "Extracts product/service entities",
            "categories": "Generates document categories"
        },
        "utilities": {
            "context_formatting": "Formats context for LLM consumption"
        }
    }


# =============================================================================
# PROMPT VALIDATION
# =============================================================================

def validate_prompt_template(template: str) -> bool:
    """
    Validate that a prompt template has required placeholders.
    
    Args:
        template: The prompt template to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_placeholders = ["{context}", "{question}"]
    return all(placeholder in template for placeholder in required_placeholders)


def get_prompt_usage_examples() -> Dict[str, str]:
    """
    Get usage examples for each prompt type.
    
    Returns:
        Dictionary with prompt types and their usage examples
    """
    return {
        "rag_main": "Used by RAG.generate_response() for structured answer generation",
        "question_rephrasing": "Used by RouterGraph._rephrase_question() for question enhancement",
        "clarification": "Used by RouterGraph.clarify() for generating clarification questions",
        "metadata_extraction": "Used by LLMMetadataExtractor for document analysis",
        "document_type": "Used by EnhancedMetadataExtractor for document classification",
        "title_extraction": "Used by EnhancedMetadataExtractor for title extraction",
        "product_entities": "Used by EnhancedMetadataExtractor for entity extraction",
        "categories": "Used by EnhancedMetadataExtractor for categorization"
    }
