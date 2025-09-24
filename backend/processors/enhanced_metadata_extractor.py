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
Enhanced Metadata Extractor with Document-Level and Chunk-Level Metadata
Author: Emad Noorizadeh

This module provides a sophisticated metadata extraction system that:
1. Extracts document-level metadata with LLM-based accuracy
2. Extracts chunk-level metadata with precise positioning
3. Uses reference-based linking between documents and chunks
4. Stores document metadata in a JSON file for efficient access
5. Uses strict LLM prompts to avoid hallucination
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

from model_manager import ModelManager
from prompts import (
    get_document_type_prompt, 
    get_title_extraction_prompt, 
    get_product_entities_prompt, 
    get_categories_prompt
)
from config.authority_scores import calculate_authority_score
from config import get_config


@dataclass
class DocumentMetadata:
    """Document-level metadata with comprehensive information"""
    # Core identifiers
    doc_id: str
    canonical_url: str
    domain: str
    
    # Document classification
    doc_type: str  # landing, disclosure, FAQ, terms, form, promo
    language: str  # e.g., "en"
    
    # Temporal information
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    effective_date: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Authority and scope
    authority_score: float = 0.0  # site trust / internal priority
    geo_scope: str = "US"  # US, state/city
    currency: str = "USD"
    
    # Content analysis
    product_entities: List[str] = None  # normalized names
    title: str = ""
    categories: List[str] = None
    
    # File information
    file_path: str = ""
    file_type: str = ""
    file_name: str = ""
    
    # Processing metadata
    created_at: str = ""
    updated_at_processing: str = ""
    
    def __post_init__(self):
        if self.product_entities is None:
            self.product_entities = []
        if self.categories is None:
            self.categories = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at_processing:
            self.updated_at_processing = datetime.now().isoformat()


@dataclass
class ChunkMetadata:
    """Chunk-level metadata with precise positioning and references"""
    # Core identifiers
    chunk_id: str
    doc_id: str  # Reference to document metadata
    
    # Positioning information
    section_path: List[str] = None  # e.g., ["Rewards built around you", "Eligibility", "Tiers"]
    start_line: int = 0
    end_line: int = 0
    start_char: int = 0
    end_char: int = 0
    
    # Content analysis
    token_count: int = 0
    has_numbers: bool = False
    has_currency: bool = False
    
    # Technical metadata
    embedding_version: str = "text-embedding-3-small"
    
    # Processing metadata
    created_at: str = ""
    
    def __post_init__(self):
        if self.section_path is None:
            self.section_path = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class EnhancedMetadataExtractor:
    """Enhanced metadata extractor with LLM-based accuracy and reference linking"""
    
    def __init__(self, model_manager: ModelManager, metadata_file_path: str = "index/metadata/document_metadata.json"):
        self.model_manager = model_manager
        self.metadata_file_path = Path(metadata_file_path)
        self.document_metadata: Dict[str, DocumentMetadata] = {}
        self._load_document_metadata()
    
    def _load_document_metadata(self):
        """Load document metadata from JSON file"""
        if self.metadata_file_path.exists():
            try:
                with open(self.metadata_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc_id, doc_data in data.items():
                        self.document_metadata[doc_id] = DocumentMetadata(**doc_data)
                print(f"✓ Loaded {len(self.document_metadata)} document metadata records")
            except Exception as e:
                print(f"⚠ Error loading document metadata: {e}")
                self.document_metadata = {}
        else:
            print("ℹ No existing document metadata found, starting fresh")
    
    def _save_document_metadata(self):
        """Save document metadata to JSON file"""
        try:
            data = {doc_id: asdict(doc_meta) for doc_id, doc_meta in self.document_metadata.items()}
            with open(self.metadata_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(self.document_metadata)} document metadata records")
        except Exception as e:
            print(f"✗ Error saving document metadata: {e}")
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def _extract_document_type_with_llm(self, text: str, url: str = "") -> str:
        """Extract document type using LLM with strict prompting"""
        prompt = get_document_type_prompt(text, url)

        try:
            response = self.model_manager.generate_text([
                {"role": "user", "content": prompt}
            ])
            doc_type = response.strip().lower()
            if doc_type in ["landing", "disclosure", "faq", "terms", "form", "promo"]:
                return doc_type
            else:
                return "landing"  # Default fallback
        except Exception as e:
            print(f"⚠ Error extracting document type: {e}")
            return "landing"
    
    def _extract_title_with_llm(self, text: str, url: str = "") -> str:
        """Extract accurate title using LLM"""
        prompt = get_title_extraction_prompt(text, url)

        try:
            response = self.model_manager.generate_text([
                {"role": "user", "content": prompt}
            ])
            title = response.strip()
            # Clean up common issues
            title = re.sub(r'^\[.*?\]\(.*?\)', '', title)  # Remove markdown links
            title = title.replace('"', '').replace("'", "").strip()
            return title if title and title != "Untitled Document" else "Untitled Document"
        except Exception as e:
            print(f"⚠ Error extracting title: {e}")
            return "Untitled Document"
    
    def _extract_product_entities_with_llm(self, text: str) -> List[str]:
        """Extract product entities using LLM with strict prompting"""
        prompt = get_product_entities_prompt(text)

        try:
            response = self.model_manager.generate_text([
                {"role": "user", "content": prompt}
            ])
            response = response.strip()
            
            # Handle empty or invalid responses
            if not response or response.lower() in ['[]', 'null', 'none']:
                return []
            
            # Try to parse JSON response
            try:
                entities = json.loads(response)
                if isinstance(entities, list):
                    return [str(entity).strip() for entity in entities if entity and str(entity).strip()]
                else:
                    return []
            except json.JSONDecodeError:
                # If not JSON, try to extract entities from text
                if '[' in response and ']' in response:
                    # Extract content between brackets
                    start = response.find('[')
                    end = response.rfind(']') + 1
                    json_part = response[start:end]
                    entities = json.loads(json_part)
                    if isinstance(entities, list):
                        return [str(entity).strip() for entity in entities if entity and str(entity).strip()]
                return []
        except Exception as e:
            print(f"⚠ Error extracting product entities: {e}")
            return []
    
    def _extract_categories_with_llm(self, text: str, title: str = "") -> List[str]:
        """Extract categories using LLM with strict prompting"""
        prompt = get_categories_prompt(text, title)

        try:
            response = self.model_manager.generate_text([
                {"role": "user", "content": prompt}
            ])
            response = response.strip()
            
            # Handle empty or invalid responses
            if not response or response.lower() in ['[]', 'null', 'none']:
                return ["General"]
            
            # Try to parse JSON response
            try:
                categories = json.loads(response)
                if isinstance(categories, list):
                    return [str(cat).strip() for cat in categories if cat and str(cat).strip()]
                else:
                    return ["General"]
            except json.JSONDecodeError:
                # If not JSON, try to extract categories from text
                if '[' in response and ']' in response:
                    # Extract content between brackets
                    start = response.find('[')
                    end = response.rfind(']') + 1
                    json_part = response[start:end]
                    categories = json.loads(json_part)
                    if isinstance(categories, list):
                        return [str(cat).strip() for cat in categories if cat and str(cat).strip()]
                return ["General"]
        except Exception as e:
            print(f"⚠ Error extracting categories: {e}")
            return ["General"]
    
    def _extract_dates_from_text(self, text: str) -> Dict[str, str]:
        """Extract dates from text using regex patterns"""
        dates = {}
        
        # Common date patterns
        date_patterns = {
            'published_at': [
                r'published[:\s]+(\d{4}-\d{2}-\d{2})',
                r'date[:\s]+(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})'
            ],
            'updated_at': [
                r'updated[:\s]+(\d{4}-\d{2}-\d{2})',
                r'last\s+updated[:\s]+(\d{4}-\d{2}-\d{2})',
                r'modified[:\s]+(\d{4}-\d{2}-\d{2})'
            ],
            'effective_date': [
                r'effective[:\s]+(\d{4}-\d{2}-\d{2})',
                r'effective\s+date[:\s]+(\d{4}-\d{2}-\d{2})'
            ],
            'expires_at': [
                r'expires[:\s]+(\d{4}-\d{2}-\d{2})',
                r'expiration[:\s]+(\d{4}-\d{2}-\d{2})',
                r'valid\s+until[:\s]+(\d{4}-\d{2}-\d{2})'
            ]
        }
        
        for date_type, patterns in date_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dates[date_type] = match.group(1)
                    break
        
        return dates
    
    def _calculate_authority_score(self, domain: str, doc_type: str) -> float:
        """Calculate authority score based on domain and document type"""
        return calculate_authority_score(domain, doc_type)
    
    def extract_document_metadata(self, text: str, file_path: str, url: str = "") -> DocumentMetadata:
        """Extract comprehensive document-level metadata"""
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        domain = self._extract_domain_from_url(url) if url else "local"
        
        # Extract basic information
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name
        file_type = file_path_obj.suffix
        
        # LLM-based extractions
        doc_type = self._extract_document_type_with_llm(text, url)
        title = self._extract_title_with_llm(text, url)
        product_entities = self._extract_product_entities_with_llm(text)
        categories = self._extract_categories_with_llm(text, title)
        
        # Date extraction
        dates = self._extract_dates_from_text(text)
        
        # Calculate authority score
        authority_score = self._calculate_authority_score(domain, doc_type)
        
        # Create document metadata
        doc_metadata = DocumentMetadata(
            doc_id=doc_id,
            canonical_url=url or f"file://{file_path}",
            domain=domain,
            doc_type=doc_type,
            language="en",  # Default to English
            published_at=dates.get('published_at'),
            updated_at=dates.get('updated_at'),
            effective_date=dates.get('effective_date'),
            expires_at=dates.get('expires_at'),
            authority_score=authority_score,
            geo_scope="US",  # Default to US
            currency="USD",  # Default to USD
            product_entities=product_entities,
            title=title,
            categories=categories,
            file_path=file_path,
            file_type=file_type,
            file_name=file_name
        )
        
        # Store in memory and save to file
        self.document_metadata[doc_id] = doc_metadata
        self._save_document_metadata()
        
        return doc_metadata
    
    def extract_chunk_metadata(self, text: str, doc_id: str, chunk_index: int, 
                              start_line: int = 0, end_line: int = 0,
                              start_char: int = 0, end_char: int = 0) -> ChunkMetadata:
        """Extract chunk-level metadata with precise positioning"""
        chunk_id = f"{doc_id}_chunk_{chunk_index}"
        
        # Analyze chunk content
        token_count = len(text.split())
        has_numbers = bool(re.search(r'\d+', text))
        has_currency = bool(re.search(r'\$[\d,]+\.?\d*|\d+\.\d+\s*(dollars?|USD)', text, re.IGNORECASE))
        
        # Extract section path (simplified - could be enhanced with LLM)
        section_path = self._extract_section_path(text)
        
        chunk_metadata = ChunkMetadata(
            chunk_id=chunk_id,
            doc_id=doc_id,
            section_path=section_path,
            start_line=start_line,
            end_line=end_line,
            start_char=start_char,
            end_char=end_char,
            token_count=token_count,
            has_numbers=has_numbers,
            has_currency=has_currency,
            embedding_version="text-embedding-3-small"
        )
        
        return chunk_metadata
    
    def _extract_section_path(self, text: str) -> List[str]:
        """Extract section path from chunk text"""
        # Look for headings in the text
        headings = []
        
        # Markdown headings
        heading_patterns = [
            r'^#+\s+(.+)$',  # Markdown headings
            r'^(.+)\n=+$',   # Underlined headings
            r'^(.+)\n-+$',   # Dashed headings
        ]
        
        for pattern in heading_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            headings.extend([match.strip() for match in matches])
        
        return headings[:3]  # Limit to 3 levels
    
    def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by ID"""
        return self.document_metadata.get(doc_id)
    
    def get_all_document_metadata(self) -> Dict[str, DocumentMetadata]:
        """Get all document metadata"""
        return self.document_metadata.copy()
    
    def update_document_metadata(self, doc_id: str, updates: Dict[str, Any]):
        """Update document metadata"""
        if doc_id in self.document_metadata:
            doc_meta = self.document_metadata[doc_id]
            for key, value in updates.items():
                if hasattr(doc_meta, key):
                    setattr(doc_meta, key, value)
            doc_meta.updated_at_processing = datetime.now().isoformat()
            self._save_document_metadata()
    
    def delete_document_metadata(self, doc_id: str):
        """Delete document metadata"""
        if doc_id in self.document_metadata:
            del self.document_metadata[doc_id]
            self._save_document_metadata()
    
    def export_metadata(self, output_file: str = "index/metadata/enhanced_metadata_export.json"):
        """Export all metadata to a JSON file"""
        export_data = {
            "document_metadata": {
                doc_id: {
                    "doc_id": doc.doc_id,
                    "canonical_url": doc.canonical_url,
                    "domain": doc.domain,
                    "doc_type": doc.doc_type,
                    "language": doc.language,
                    "title": doc.title,
                    "categories": doc.categories,
                    "product_entities": doc.product_entities,
                    "authority_score": doc.authority_score,
                    "geo_scope": doc.geo_scope,
                    "currency": doc.currency,
                    "file_path": doc.file_path,
                    "created_at": doc.created_at
                } for doc_id, doc in self.document_metadata.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported metadata to {output_file}")
        return export_data
