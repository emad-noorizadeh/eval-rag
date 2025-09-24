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
LLM-Enhanced Metadata Extractor for RAG Systems
Author: Emad Noorizadeh

This module provides advanced metadata extraction using Large Language Models
for more accurate and context-aware document processing.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ExtractionMethod(Enum):
    """Available extraction methods"""
    REGEX_ONLY = "regex_only"
    LLM_ONLY = "llm_only"
    HYBRID = "hybrid"  # LLM + regex fallback
    ADAPTIVE = "adaptive"  # Choose based on content complexity

@dataclass
class ExtractionConfig:
    """Configuration for LLM metadata extraction"""
    method: ExtractionMethod = ExtractionMethod.HYBRID
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.1  # Low temperature for consistent extraction
    max_tokens: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    enable_structured_output: bool = True
    fallback_to_regex: bool = True
    confidence_threshold: float = 0.7

@dataclass
class ExtractedMetadata:
    """Structured metadata extraction result"""
    title: Optional[str] = None
    summary: Optional[str] = None
    categories: List[str] = None
    entities: Dict[str, List[str]] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    topics: List[str] = None
    key_phrases: List[str] = None
    document_type: Optional[str] = None
    confidence_scores: Dict[str, float] = None
    extraction_method: str = "unknown"
    processing_time: float = 0.0

class LLMMetadataExtractor:
    """
    Advanced metadata extractor using LLMs with fallback to regex methods
    """
    
    def __init__(self, config_getter, model_manager=None, config: ExtractionConfig = None):
        """
        Initialize LLM metadata extractor
        
        Args:
            config_getter: Function to get configuration values
            model_manager: ModelManager instance for LLM access
            config: Extraction configuration
        """
        self.get_config = config_getter
        self.model_manager = model_manager
        self.config = config or ExtractionConfig()
        self.regex_extractor = None  # Will be initialized if needed
        
        # Initialize regex extractor for fallback
        if self.config.fallback_to_regex:
            from utils.rag_utils import MetadataExtractor
            self.regex_extractor = MetadataExtractor(config_getter)
    
    def extract_metadata(self, text: str, use_llm: bool = None) -> ExtractedMetadata:
        """
        Extract metadata using the configured method
        
        Args:
            text: Document text to process
            use_llm: Override method selection (None = use config)
        
        Returns:
            ExtractedMetadata object with extracted information
        """
        start_time = datetime.now()
        
        # Determine extraction method
        if use_llm is None:
            use_llm = self._should_use_llm(text)
        
        try:
            if use_llm and self.model_manager:
                result = self._extract_with_llm(text)
            else:
                result = self._extract_with_regex(text)
        except Exception as e:
            print(f"⚠ LLM extraction failed: {e}")
            if self.config.fallback_to_regex and self.regex_extractor:
                print("🔄 Falling back to regex extraction...")
                result = self._extract_with_regex(text)
            else:
                raise e
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time
        
        return result
    
    def _should_use_llm(self, text: str) -> bool:
        """Determine if LLM extraction should be used based on content complexity"""
        if self.config.method == ExtractionMethod.REGEX_ONLY:
            return False
        elif self.config.method == ExtractionMethod.LLM_ONLY:
            return True
        elif self.config.method == ExtractionMethod.HYBRID:
            return True  # Always try LLM first in hybrid mode
        elif self.config.method == ExtractionMethod.ADAPTIVE:
            return self._is_complex_content(text)
        
        return True
    
    def _is_complex_content(self, text: str) -> bool:
        """Determine if content is complex enough to warrant LLM processing"""
        # Simple heuristics for content complexity
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # Use LLM for longer, more complex documents
        complexity_score = 0
        
        if word_count > 500:
            complexity_score += 1
        if line_count > 20:
            complexity_score += 1
        if any(keyword in text.lower() for keyword in ['analysis', 'research', 'study', 'report']):
            complexity_score += 1
        if len(re.findall(r'[.!?]', text)) > 10:  # Multiple sentences
            complexity_score += 1
        
        return complexity_score >= 2
    
    def _extract_with_llm(self, text: str) -> ExtractedMetadata:
        """Extract metadata using LLM"""
        if not self.model_manager:
            raise ValueError("ModelManager not available for LLM extraction")
        
        # Truncate text if too long for LLM context
        max_chars = 4000  # Leave room for prompt
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(text)
        
        try:
            # Get LLM response
            response = self.model_manager.generate_text(
                messages=[{"role": "user", "content": prompt}],
                model=self.config.model,
                temperature=self.config.temperature
            )
            
            # Parse LLM response
            return self._parse_llm_response(response, text)
            
        except Exception as e:
            print(f"❌ LLM extraction error: {e}")
            raise e
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a structured prompt for metadata extraction"""
        from prompts import get_metadata_extraction_prompt
        return get_metadata_extraction_prompt(text)
    
    def _parse_llm_response(self, response: str, original_text: str) -> ExtractedMetadata:
        """Parse LLM response into structured metadata"""
        try:
            # Clean response (remove markdown formatting if present)
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            
            # Create metadata object
            metadata = ExtractedMetadata(
                title=data.get('title'),
                summary=data.get('summary'),
                categories=data.get('categories', []),
                entities=data.get('entities', {}),
                sentiment=data.get('sentiment'),
                language=data.get('language'),
                topics=data.get('topics', []),
                key_phrases=data.get('key_phrases', []),
                document_type=data.get('document_type'),
                confidence_scores=data.get('confidence_scores', {}),
                extraction_method="llm"
            )
            
            # Validate confidence scores
            if metadata.confidence_scores:
                overall_confidence = metadata.confidence_scores.get('overall', 0.5)
                if overall_confidence < self.config.confidence_threshold:
                    print(f"⚠ Low confidence extraction: {overall_confidence}")
            
            return metadata
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse LLM response as JSON: {e}")
            print(f"Response: {response[:200]}...")
            # Fallback to regex extraction
            return self._extract_with_regex(original_text)
        except Exception as e:
            print(f"❌ Error parsing LLM response: {e}")
            return self._extract_with_regex(original_text)
    
    def _extract_with_regex(self, text: str) -> ExtractedMetadata:
        """Extract metadata using regex-based methods"""
        if not self.regex_extractor:
            raise ValueError("Regex extractor not available")
        
        # Use existing regex-based extraction
        regex_metadata = self.regex_extractor.extract_content_metadata(text)
        
        # Convert to structured format
        metadata = ExtractedMetadata(
            title=regex_metadata.get('title'),
            summary=None,  # Not available in regex extraction
            categories=regex_metadata.get('categories', '').split(', ') if regex_metadata.get('categories') else [],
            entities={},  # Not available in regex extraction
            sentiment=None,  # Not available in regex extraction
            language=None,  # Not available in regex extraction
            topics=[],  # Not available in regex extraction
            key_phrases=[],  # Not available in regex extraction
            document_type=None,  # Not available in regex extraction
            confidence_scores={'overall': 0.6},  # Lower confidence for regex
            extraction_method="regex"
        )
        
        return metadata
    
    def batch_extract(self, texts: List[str]) -> List[ExtractedMetadata]:
        """Extract metadata for multiple documents"""
        results = []
        for i, text in enumerate(texts):
            print(f"Processing document {i+1}/{len(texts)}...")
            try:
                result = self.extract_metadata(text)
                results.append(result)
            except Exception as e:
                print(f"❌ Failed to process document {i+1}: {e}")
                # Add empty result to maintain order
                results.append(ExtractedMetadata(extraction_method="failed"))
        
        return results
    
    def get_extraction_stats(self, results: List[ExtractedMetadata]) -> Dict[str, Any]:
        """Get statistics about extraction results"""
        if not results:
            return {}
        
        total = len(results)
        successful = len([r for r in results if r.extraction_method != "failed"])
        llm_count = len([r for r in results if r.extraction_method == "llm"])
        regex_count = len([r for r in results if r.extraction_method == "regex"])
        
        avg_confidence = 0
        if successful > 0:
            confidences = [r.confidence_scores.get('overall', 0) for r in results if r.confidence_scores]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        avg_processing_time = sum(r.processing_time for r in results) / total
        
        return {
            'total_documents': total,
            'successful_extractions': successful,
            'success_rate': successful / total,
            'llm_extractions': llm_count,
            'regex_extractions': regex_count,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time
        }


class HybridMetadataExtractor:
    """
    Hybrid metadata extractor that combines LLM and regex methods
    """
    
    def __init__(self, config_getter, model_manager=None):
        self.config_getter = config_getter
        self.model_manager = model_manager
        
        # Initialize both extractors
        self.llm_extractor = LLMMetadataExtractor(config_getter, model_manager)
        from utils.rag_utils import MetadataExtractor
        self.regex_extractor = MetadataExtractor(config_getter)
    
    def extract_metadata(self, text: str, strategy: str = "smart") -> Dict[str, Any]:
        """
        Extract metadata using hybrid approach
        
        Args:
            text: Document text
            strategy: "smart" (choose best method), "llm_first", "regex_first", "both"
        """
        if strategy == "smart":
            # Use LLM for complex content, regex for simple
            if self.llm_extractor._is_complex_content(text):
                return self._extract_with_llm(text)
            else:
                return self._extract_with_regex(text)
        
        elif strategy == "llm_first":
            try:
                return self._extract_with_llm(text)
            except:
                return self._extract_with_regex(text)
        
        elif strategy == "regex_first":
            try:
                return self._extract_with_regex(text)
            except:
                return self._extract_with_llm(text)
        
        elif strategy == "both":
            # Combine both methods
            llm_result = self._extract_with_llm(text)
            regex_result = self._extract_with_regex(text)
            return self._merge_results(llm_result, regex_result)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Extract using LLM and convert to dict format"""
        result = self.llm_extractor.extract_metadata(text, use_llm=True)
        return self._convert_to_dict(result)
    
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract using regex methods"""
        return self.regex_extractor.extract_content_metadata(text)
    
    def _convert_to_dict(self, metadata: ExtractedMetadata) -> Dict[str, Any]:
        """Convert ExtractedMetadata to dictionary format"""
        result = {
            'title': metadata.title,
            'summary': metadata.summary,
            'categories': metadata.categories if metadata.categories and isinstance(metadata.categories, list) else [],
            'sentiment': metadata.sentiment,
            'language': metadata.language,
            'document_type': metadata.document_type,
            'extraction_method': metadata.extraction_method,
            'confidence': metadata.confidence_scores.get('overall', 0.5) if metadata.confidence_scores else 0.5,
            'url': None,  # Will be set by the index builder if available
            'published_at': None,  # Will be set by the index builder if available
            'updated_at': None,  # Will be set by the index builder if available
            'effective_date': None,  # Will be set by the index builder if available
            'expires_at': None,  # Will be set by the index builder if available
            'geo_scope': 'unknown',  # Default value
            'currency': 'USD'  # Default value
        }
        
        # Add entities as separate fields
        if metadata.entities:
            for entity_type, entities in metadata.entities.items():
                if entities and isinstance(entities, list):
                    result[f'entities_{entity_type}'] = ', '.join(entities)
        
        # Add topics and key phrases
        if metadata.topics and isinstance(metadata.topics, list):
            result['topics'] = ', '.join(metadata.topics)
        if metadata.key_phrases and isinstance(metadata.key_phrases, list):
            result['key_phrases'] = ', '.join(metadata.key_phrases)
        
        return result
    
    def _merge_results(self, llm_result: ExtractedMetadata, regex_result: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM and regex results, preferring LLM for complex fields"""
        merged = dict(regex_result)  # Start with regex result
        
        # Override with LLM results where available
        if llm_result.title:
            merged['title'] = llm_result.title
        if llm_result.summary:
            merged['summary'] = llm_result.summary
        if llm_result.categories and isinstance(llm_result.categories, list):
            merged['categories'] = llm_result.categories
        if llm_result.sentiment:
            merged['sentiment'] = llm_result.sentiment
        if llm_result.document_type:
            merged['document_type'] = llm_result.document_type
        
        # Add LLM-specific fields
        merged['extraction_method'] = 'hybrid'
        merged['llm_confidence'] = llm_result.confidence_scores.get('overall', 0.5) if llm_result.confidence_scores else 0.5
        
        return merged
