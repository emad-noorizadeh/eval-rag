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
RAG (Retrieval-Augmented Generation) Class
Author: Emad Noorizadeh
"""

import json
from typing import List, Dict, Any, Optional
from collections import defaultdict
from model_manager import ModelManager
from index_builder import IndexBuilder
from utils.rag_utils import format_context_with_metadata
from retrieval_service import RetrievalService, RetrievalConfig, RetrievalMethod
from prompts import get_rag_main_prompt, get_rag_simple_prompt
from config.config import get_config

class RAG:
    """Retrieval-Augmented Generation system"""
    
    def __init__(self, model_manager: ModelManager, index_builder: IndexBuilder, 
                 retrieval_method: RetrievalMethod = RetrievalMethod.SEMANTIC):
        self.model_manager = model_manager
        self.index_builder = index_builder
        self.retrieval_method = retrieval_method
        
        # Initialize retrieval service
        self.retrieval_service = RetrievalService(model_manager, index_builder)
        
        # Define the prompt template for structured response + metrics
        self.prompt_template = get_rag_main_prompt()

    
    
    def retrieve_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query using the configured retrieval method
        
        Args:
            query: Search query
            n_results: Number of documents to retrieve
        
        Returns:
            List of retrieved documents with metadata
        """
        # Create retrieval config (simplified for semantic only)
        retrieval_config = RetrievalConfig(
            method=self.retrieval_method,
            top_k=n_results,
            similarity_threshold=0.45
        )
        
        # Use retrieval service
        retrieval_result = self.retrieval_service.retrieve(query, retrieval_config)
        
        # Convert to the format expected by the rest of the RAG system
        documents = []
        for chunk in retrieval_result.chunks:
            doc = {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "text": chunk["text"],
                "score": chunk["score"],
                "metadata": chunk["metadata"]
            }
            documents.append(doc)
        
        return documents
    
    def _format_context_from_nodes(self, nodes: List[Dict[str, Any]]) -> tuple:
        """
        Format retrieved documents into context chunks with enhanced source and metadata information
        
        Args:
            nodes: List of retrieved document nodes
            
        Returns:
            Tuple of (context_str, debug_meta, valid_ids)
        """
        return format_context_with_metadata(nodes)
    
    def build_prompt(self, context: str, question: str, valid_chunk_ids: str) -> str:
        """
        Build the complete prompt using the template
        
        Args:
            context: Formatted context string
            question: User question
            valid_chunk_ids: Comma-separated list of valid chunk IDs
            
        Returns:
            Complete prompt string
        """
        return self.prompt_template.format_map(
            defaultdict(str, context=context, question=question, valid_chunk_ids=valid_chunk_ids)
        )
    
    def generate_response(self, question: str, retrieved: List[Dict[str, Any]], 
                         conversation_snippet: str = "", topic_hint: str = "") -> Dict[str, Any]:
        """
        Generate a structured response using the new guarded prompt with conversation context
        
        Args:
            question: User question
            retrieved: Retrieved documents for context
            conversation_snippet: Last 3 turns of conversation (non-factual)
            topic_hint: Focus topic hint from clarification (non-factual)
        
        Returns:
            Dictionary containing response and metadata
        """
        if not retrieved:
            return self._create_empty_response(question)
        
        try:
            # 1) Format grounding context
            context_lines, ids = [], []
            for i, ch in enumerate(retrieved, 1):
                cid = f"C{i}"
                ids.append(cid)
                context_lines.append(f"{cid}: {ch.get('text','')}")
            context = "\n\n".join(context_lines)
            valid_ids = ", ".join(ids) if ids else ""

            # 2) Assemble prompt using new guarded template
            from prompts import get_rag_main_prompt
            prompt = get_rag_main_prompt().format(
                conversation_snippet=conversation_snippet or "(none)",
                topic_hint=topic_hint or "(none)",
                context=context or "(no context)",
                question=question,
                valid_chunk_ids=valid_ids or "[]"
            )

            # 3) Call LLM, parse, enforce
            if self.model_manager.get_openai_client():
                response_text = self.model_manager.generate_text([{"role": "user", "content": prompt}])
                data = self._parse_json_response(response_text) or {}
                
                # Validate evidence IDs using utility
                from utils.conversation_utils import validate_evidence_ids
                if not validate_evidence_ids(data.get("evidence") or [], ids):
                    data["abstained"] = True
                    data["answer"] = ""
                    data["clarifying_question"] = data.get("clarifying_question") or "I need more specific details to answer."
                    data["confidence"] = "Low"
                
                return {
                    "answer": data.get("answer",""),
                    "sources": retrieved,
                    "metrics": data
                }
            else:
                return self._create_fallback_response(question, retrieved)
                
        except Exception as e:
            print(f"Error generating structured response: {e}")
            return self._create_fallback_response(question, retrieved)
    
    def retrieve_documents_union_if_needed(self, original_query: str, hint_query: str, n_results: int, use_union: bool):
        """Union retrieval helper called by router's retrieve"""
        if use_union and hint_query:
            return self.retrieval_service.retrieve_union(original_query, hint_query, n_results)
        return self.retrieval_service.retrieve_semantic(original_query, n_results)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from the model
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            Parsed JSON response with defaults
        """
        try:
            # Try to find JSON in the response
            response_text = response_text.strip()
            
            # Look for JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx + 1]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {response_text[:200]}...")
            
            # Return default structure
            return {
                "answer": "I apologize, but I encountered an error processing your request.",
                "evidence": [],
                "missing": "Error in response parsing",
                "confidence": "Low",
                "faithfulness_score": 0.0,
                "completeness_score": 0.0,
                "answer_type": "abstain",
                "abstained": True,
                "reasoning_notes": f"JSON parsing error: {str(e)}"
            }
    
    def _create_empty_response(self, query: str) -> Dict[str, Any]:
        """Create response when no documents are retrieved"""
        return {
            "answer": "I couldn't find any relevant documents in the database. Please upload some documents first, or try rephrasing your question.",
            "sources": [],
            "metrics": {
                "chunks_retrieved": [],
                "confidence": "Low",
                "faithfulness_score": 0.0,
                "completeness_score": 0.0,
                "missing_information": ["No relevant documents found"],
                "answer_type": "abstain",
                "abstained": True,
                "reasoning_notes": "No documents retrieved for query"
            }
        }
    
    def _create_fallback_response(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create fallback response when model is not available"""
        if retrieved_docs:
            response = f"I found {len(retrieved_docs)} relevant documents, but I need a language model to generate a proper response. Here are the relevant sources:\n\n"
            for i, doc in enumerate(retrieved_docs, 1):
                response += f"{i}. {doc['text'][:200]}...\n"
        else:
            response = "I couldn't find any relevant documents in the database. Please upload some documents first, or try rephrasing your question."
        
        return {
            "answer": response,
            "sources": retrieved_docs,
            "metrics": {
                "chunks_retrieved": [],
                "confidence": "Low",
                "faithfulness_score": 0.0,
                "completeness_score": 0.0,
                "missing_information": ["Model not available"],
                "answer_type": "abstain",
                "abstained": True,
                "reasoning_notes": "Fallback response due to model unavailability"
            }
        }
    
    
    def query(self, query: str, n_results: int = 5, 
              conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve + generate
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            conversation_history: Previous conversation messages
        
        Returns:
            Complete RAG response with sources and metrics
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve_documents(query, n_results)
        
        # Generate response
        return self.generate_response(query, retrieved_docs, conversation_history)
