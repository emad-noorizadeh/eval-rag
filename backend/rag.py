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
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from .model_manager import ModelManager
from .index_builder import IndexBuilder
from .utils.rag_utils import format_context_with_metadata
from .retrieval_service import RetrievalService, RetrievalConfig, RetrievalMethod
from .prompts import get_rag_main_prompt, get_rag_simple_prompt
from .config.config import get_config

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
        self.last_retrieval_error: Optional[str] = None
        self.logger = logging.getLogger(__name__ + ".rag")

    
    
    def retrieve_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query using the configured retrieval method
        
        Args:
            query: Search query
            n_results: Number of documents to retrieve
        
        Returns:
            List of retrieved documents with metadata
        """
        self.logger.info("retrieve_documents: query='%s' top_k=%d", query[:160], n_results)
        self.last_retrieval_error = None
        try:
            retrieval_config = RetrievalConfig(
                method=self.retrieval_method,
                top_k=n_results,
                similarity_threshold=0.45
            )

            retrieval_result = self.retrieval_service.retrieve(query, retrieval_config)

            documents = []
            for chunk in retrieval_result.chunks:
                documents.append({
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "text": chunk["text"],
                    "score": chunk["score"],
                    "metadata": chunk["metadata"],
                })
            if retrieval_result.chunks:
                scores = [chunk["score"] for chunk in retrieval_result.chunks]
                self.logger.info(
                    "retrieve_documents: retrieved=%d avg_score=%.3f max_score=%.3f",
                    len(retrieval_result.chunks),
                    sum(scores) / len(scores),
                    max(scores),
                )
            else:
                self.logger.info("retrieve_documents: retrieved=0")
            return documents
        except Exception as exc:
            self.last_retrieval_error = str(exc)
            print(f"Retrieval error: {exc}")
            return []
    
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
            prompt_template = get_rag_main_prompt()
            base_prompt = prompt_template.format(
                conversation_snippet=conversation_snippet or "(none)",
                topic_hint=topic_hint or "(none)",
                context=context or "(no context)",
                question=question,
                valid_chunk_ids=valid_ids or "[]"
            )

            if not self.model_manager.get_openai_client():
                return self._create_fallback_response(
                    question,
                    retrieved,
                    reason="model_unavailable",
                )

            max_retry = get_config("models", "llm_max_retry")
            try:
                max_retry = int(max_retry)
            except (TypeError, ValueError):
                max_retry = 1
            max_retry = max(0, max_retry)

            attempt = 0
            current_prompt = base_prompt
            last_error = ""
            fallback_reason = ""
            last_response_text = ""

            scores = [chunk.get("score", 0.0) for chunk in retrieved]
            avg_similarity = sum(scores) / len(scores) if scores else 0.0
            similarity_threshold = get_config("chat_agent", "similarity_threshold") or 0.45
            try:
                similarity_threshold = float(similarity_threshold)
            except (TypeError, ValueError):
                similarity_threshold = 0.45

            while True:
                self.logger.info(
                    "generate_response: attempt=%d retrieved=%d avg_similarity=%.3f",
                    attempt + 1,
                    len(retrieved),
                    avg_similarity,
                )
                response_text = self.model_manager.generate_text([{"role": "user", "content": current_prompt}])
                last_response_text = response_text
                data = self._parse_json_response(response_text) or {}
                is_valid, normalized, error_msg = self._validate_response_schema(data)

                if is_valid:
                    data = normalized

                    from .utils.conversation_utils import validate_evidence_ids
                    if not validate_evidence_ids(data.get("evidence") or [], ids):
                        data["abstained"] = True
                        data["answer"] = ""
                        data["clarifying_question"] = data.get("clarifying_question") or "I need more specific details to answer."
                        data["confidence"] = "Low"

                    if data.get("abstained") and ids and avg_similarity >= similarity_threshold:
                        attempt += 1
                        if attempt > max_retry:
                            print("LLM abstained despite sufficient context; falling back")
                            self.logger.warning(
                                "generate_response: abstained despite sufficient context (attempt=%d)",
                                attempt,
                            )
                            fallback_reason = "abstained_after_retry"
                            self.logger.warning(
                                "generate_response: forced_fallback reason=%s excerpt='%s'",
                                fallback_reason,
                                self._truncate_for_log(last_response_text),
                            )
                            break
                        repair_reason = (
                            "Model abstained despite sufficient grounding context. "
                            "Provide a direct answer using only the supplied context."
                        )
                        current_prompt = self._build_repair_prompt(base_prompt, response_text, repair_reason)
                        continue

                    self.logger.info(
                        "generate_response: success attempt=%d answer_len=%d abstained=%s",
                        attempt + 1,
                        len(data.get("answer", "") or ""),
                        data.get("abstained"),
                    )
                    return {
                        "answer": data.get("answer", ""),
                        "sources": retrieved,
                        "metrics": data
                    }

                last_error = error_msg or "Schema validation failed"
                self.logger.warning(
                    "generate_response: schema_invalid attempt=%d error='%s'",
                    attempt + 1,
                    last_error,
                )
                attempt += 1
                if attempt > max_retry:
                    print(f"Schema validation failed after {attempt} attempts: {last_error}")
                    self.logger.error(
                        "generate_response: schema_failed attempts=%d last_error='%s'",
                        attempt,
                        last_error,
                    )
                    fallback_reason = "schema_validation_failed"
                    self.logger.warning(
                        "generate_response: forced_fallback reason=%s excerpt='%s'",
                        fallback_reason,
                        self._truncate_for_log(last_response_text),
                    )
                    break
                current_prompt = self._build_repair_prompt(base_prompt, response_text, last_error)

            if not fallback_reason:
                fallback_reason = "unknown"
            return self._create_fallback_response(
                question,
                retrieved,
                reason=fallback_reason,
                raw_response=last_response_text,
            )

        except Exception as e:
            print(f"Error generating structured response: {e}")
            self.logger.exception("generate_response: exception")
            return self._create_fallback_response(
                question,
                retrieved,
                reason="generation_exception",
                raw_response=str(e),
            )
    
    def retrieve_documents_union_if_needed(self, original_query: str, hint_query: str, n_results: int, use_union: bool):
        """Union retrieval helper called by router's retrieve"""
        self.last_retrieval_error = None
        try:
            if use_union and hint_query:
                return self.retrieval_service.retrieve_union(original_query, hint_query, n_results)
            return self.retrieval_service.retrieve_semantic(original_query, n_results)
        except Exception as exc:
            self.last_retrieval_error = str(exc)
            print(f"Retrieval error (union): {exc}")
            return []
    
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

    def _validate_response_schema(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Validate and normalize the LLM JSON output against the expected schema."""
        required_strings = [
            "answer",
            "missing",
            "confidence",
            "answer_type",
            "reasoning_notes",
            "clarifying_question",
            "interpreted_question"
        ]
        numeric_fields = ["faithfulness_score", "completeness_score"]
        normalized: Dict[str, Any] = {}
        errors = []

        for field in required_strings:
            value = data.get(field)
            if value is None:
                errors.append(f"Missing field '{field}'")
                continue
            if not isinstance(value, str):
                try:
                    value = str(value)
                except Exception:
                    errors.append(f"Field '{field}' must be a string")
                    continue
            normalized[field] = value

        # Evidence list
        evidence = data.get("evidence")
        if evidence is None:
            errors.append("Missing field 'evidence'")
        elif not isinstance(evidence, list):
            errors.append("Field 'evidence' must be a list")
        else:
            normalized["evidence"] = [str(item) for item in evidence]

        # Numeric fields
        for field in numeric_fields:
            value = data.get(field)
            if value is None:
                errors.append(f"Missing field '{field}'")
                continue
            try:
                normalized[field] = float(value)
            except (TypeError, ValueError):
                errors.append(f"Field '{field}' must be numeric")

        # Abstained is bool
        abstained = data.get("abstained")
        if abstained is None:
            errors.append("Missing field 'abstained'")
        else:
            if isinstance(abstained, bool):
                normalized["abstained"] = abstained
            elif isinstance(abstained, str) and abstained.lower() in {"true", "false"}:
                normalized["abstained"] = abstained.lower() == "true"
            else:
                errors.append("Field 'abstained' must be boolean")

        # Optional fields we still carry over if present
        normalized.setdefault("clarifying_question", "")
        normalized.setdefault("interpreted_question", "")

        if errors:
            return False, {}, "; ".join(errors)
        return True, normalized, ""

    def _build_repair_prompt(self, base_prompt: str, previous_output: str, error_msg: str) -> str:
        """Create a repair prompt instructing the LLM to fix schema issues."""
        schema_description = (
            "Expected JSON schema:\n"
            "{\n"
            "  \"answer\": string,\n"
            "  \"evidence\": array of strings,\n"
            "  \"missing\": string,\n"
            "  \"confidence\": string,\n"
            "  \"faithfulness_score\": number,\n"
            "  \"completeness_score\": number,\n"
            "  \"answer_type\": string,\n"
            "  \"abstained\": boolean,\n"
            "  \"reasoning_notes\": string,\n"
            "  \"clarifying_question\": string,\n"
            "  \"interpreted_question\": string\n"
            "}\n"
        )
        return (
            f"{base_prompt}\n\n"
            f"The previous response did not satisfy the required JSON schema.\n"
            f"Reason: {error_msg}\n"
            f"Previous response:\n{previous_output}\n\n"
            f"{schema_description}"
            "Return a corrected JSON object that follows this schema exactly."
        )
    
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
    
    def _create_fallback_response(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        reason: str = "model_unavailable",
        raw_response: str = "",
    ) -> Dict[str, Any]:
        """Create fallback response with reason-aware messaging."""
        reason = reason or "unknown"
        if retrieved_docs:
            header_map = {
                "model_unavailable": "I found {count} relevant documents, but I need a language model to generate a proper response.",
                "abstained_after_retry": "I found {count} relevant documents, but the language model abstained after multiple attempts.",
            }
            header = header_map.get(reason, "I found {count} relevant documents but could not generate an answer.")
            response_lines = [
                header.format(count=len(retrieved_docs)),
                "",
                "Here are the relevant sources:",
            ]
            for i, doc in enumerate(retrieved_docs, 1):
                preview = doc.get("text", "")[:200]
                response_lines.append(f"{i}. {preview}...")
            response = "\n".join(response_lines).strip()
        else:
            fallback_map = {
                "model_unavailable": "I couldn't find any relevant documents in the database. Please upload some documents first, or try rephrasing your question.",
                "abstained_after_retry": "I retrieved some context, but the language model kept abstaining even with retries. Please rephrase your question or adjust your guardrails.",
            }
            response = fallback_map.get(
                reason,
                "I couldn't generate a response due to an internal issue. Please try again.",
            )

        missing_info_map = {
            "model_unavailable": ["Model not available"],
            "abstained_after_retry": ["Model abstained after retries"],
            "schema_validation_failed": ["Model output could not be parsed"],
            "generation_exception": ["Error during answer generation"],
            "unknown": ["Unspecified fallback reason"],
        }
        reasoning_map = {
            "model_unavailable": "Fallback response because the language model client is not configured or reachable.",
            "abstained_after_retry": "Fallback response because the language model abstained despite sufficient context.",
            "schema_validation_failed": "Fallback response because the model did not produce valid JSON after retries.",
            "generation_exception": "Fallback response because an exception occurred while generating the answer.",
            "unknown": "Fallback response triggered for an unspecified reason.",
        }

        metrics = {
            "chunks_retrieved": [],
            "confidence": "Low",
            "faithfulness_score": 0.0,
            "completeness_score": 0.0,
            "missing_information": missing_info_map.get(reason, ["Unspecified fallback reason"]),
            "answer_type": "abstain",
            "abstained": True,
            "reasoning_notes": reasoning_map.get(reason, reasoning_map["unknown"]),
            "fallback_reason": reason,
        }
        if raw_response:
            metrics["raw_response_excerpt"] = self._truncate_for_log(raw_response)
        return {
            "answer": response,
            "sources": retrieved_docs,
            "metrics": metrics,
        }

    @staticmethod
    def _truncate_for_log(text: str, limit: int = 500) -> str:
        text = (text or "").replace("\n", " ").strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "..."
    
    
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
