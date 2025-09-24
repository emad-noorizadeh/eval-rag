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
Document Processors Package

This package contains all document processing and metadata extraction modules
for the RAG system. It provides a clean separation of concerns for document
handling, metadata extraction, and content processing.

Modules:
- enhanced_metadata_extractor: Advanced metadata extraction with LLM support
- llm_metadata_extractor: LLM-based metadata extraction with fallback methods
- enhanced_document_processor: Comprehensive document processing pipeline
- hybrid_metadata_extractor: Hybrid approach combining multiple extraction methods

Usage:
    from processors import EnhancedMetadataExtractor
    from processors import LLMMetadataExtractor
    from processors import EnhancedDocumentProcessor
"""

from .enhanced_metadata_extractor import EnhancedMetadataExtractor
from .llm_metadata_extractor import LLMMetadataExtractor, ExtractionMethod, ExtractionConfig
from .enhanced_document_processor import EnhancedDocumentProcessor
# HybridMetadataExtractor removed - using semantic only

__all__ = [
    "EnhancedMetadataExtractor",
    "LLMMetadataExtractor", 
    "ExtractionMethod",
    "ExtractionConfig",
    "EnhancedDocumentProcessor",
    # "HybridMetadataExtractor" removed
]
