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
Enhanced Document Processor with Reference-Based Metadata Linking
Author: Emad Noorizadeh

This module provides document processing that:
1. Uses the enhanced metadata extractor
2. Links chunks to document metadata via references
3. Maintains document-chunk relationships
4. Provides efficient metadata access
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from .enhanced_metadata_extractor import EnhancedMetadataExtractor, DocumentMetadata, ChunkMetadata
from model_manager import ModelManager
from config import get_config


class EnhancedDocumentProcessor:
    """Enhanced document processor with reference-based metadata linking"""
    
    def __init__(self, model_manager: ModelManager, metadata_file_path: str = "index/metadata/document_metadata.json"):
        self.model_manager = model_manager
        self.metadata_extractor = EnhancedMetadataExtractor(model_manager, metadata_file_path)
        self.chunk_metadata: Dict[str, ChunkMetadata] = {}
        self.chunks_file = "index/metadata/enhanced_chunks.json"
        self._load_chunk_metadata()
    
    def process_documents(self, documents: List[Document], chunk_size: int = 1024, 
                         chunk_overlap: int = 20) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Process documents with enhanced metadata extraction and reference linking
        
        Args:
            documents: List of LlamaIndex Document objects
            chunk_size: Size of chunks for splitting
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (processed_documents, processing_stats)
        """
        processed_docs = []
        processing_stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "metadata_extracted": 0,
            "errors": []
        }
        
        # Initialize chunk parser
        node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        for doc in documents:
            try:
                # Extract document-level metadata
                doc_metadata = self._extract_document_metadata(doc)
                processing_stats["metadata_extracted"] += 1
                
                # Process document into chunks
                chunks = self._process_document_into_chunks(doc, doc_metadata, node_parser)
                
                # Create enhanced document with reference metadata
                enhanced_doc = self._create_enhanced_document(doc, doc_metadata, chunks)
                processed_docs.append(enhanced_doc)
                
                processing_stats["documents_processed"] += 1
                processing_stats["chunks_created"] += len(chunks)
                
            except Exception as e:
                error_msg = f"Error processing document {doc.doc_id}: {str(e)}"
                processing_stats["errors"].append(error_msg)
                print(f"⚠ {error_msg}")
        
        # Save chunk metadata to file for persistence
        self._save_chunk_metadata()
        
        return processed_docs, processing_stats
    
    def _extract_document_metadata(self, doc: Document) -> DocumentMetadata:
        """Extract document-level metadata"""
        # Get file information from existing metadata
        file_path = doc.metadata.get("file_path", doc.metadata.get("source", ""))
        url = doc.metadata.get("canonical_url", "")
        
        # Extract comprehensive metadata
        doc_metadata = self.metadata_extractor.extract_document_metadata(
            text=doc.text,
            file_path=file_path,
            url=url
        )
        
        return doc_metadata
    
    def _process_document_into_chunks(self, doc: Document, doc_metadata: DocumentMetadata, 
                                    node_parser: SentenceSplitter) -> List[Dict[str, Any]]:
        """Process document into chunks with precise positioning"""
        chunks = []
        text = doc.text
        lines = text.split('\n')
        
        # Create chunks using the parser
        nodes = node_parser.get_nodes_from_documents([doc])
        
        # If no nodes were created (document too small), create a single chunk
        if not nodes:
            print(f"⚠ Document {doc.doc_id} is too small for chunking, creating single chunk")
            # Create a single node from the entire document
            from llama_index.core.schema import TextNode
            single_node = TextNode(
                text=text,
                id_=f"{doc.doc_id}_chunk_0",
                metadata=doc.metadata
            )
            nodes = [single_node]
        
        for i, node in enumerate(nodes):
            # Calculate positioning information
            start_char = text.find(node.text)
            end_char = start_char + len(node.text)
            
            # Calculate line positions
            start_line = text[:start_char].count('\n') + 1
            end_line = text[:end_char].count('\n') + 1
            
            # Extract chunk metadata
            chunk_metadata = self.metadata_extractor.extract_chunk_metadata(
                text=node.text,
                doc_id=doc_metadata.doc_id,
                chunk_index=i,
                start_line=start_line,
                end_line=end_line,
                start_char=start_char,
                end_char=end_char
            )
            
            # Store chunk metadata
            self.chunk_metadata[chunk_metadata.chunk_id] = chunk_metadata
            
            # Create chunk with reference to document metadata
            chunk_data = {
                "text": node.text,
                "chunk_id": chunk_metadata.chunk_id,
                "doc_id": doc_metadata.doc_id,  # Reference to document metadata
                "metadata": {
                    # Chunk-specific metadata
                    "chunk_id": chunk_metadata.chunk_id,
                    "doc_id": chunk_metadata.doc_id,
                    "section_path": chunk_metadata.section_path,
                    "start_line": chunk_metadata.start_line,
                    "end_line": chunk_metadata.end_line,
                    "start_char": chunk_metadata.start_char,
                    "end_char": chunk_metadata.end_char,
                    "token_count": chunk_metadata.token_count,
                    "has_numbers": chunk_metadata.has_numbers,
                    "has_currency": chunk_metadata.has_currency,
                    "embedding_version": chunk_metadata.embedding_version,
                    
                    # Reference to document metadata (not duplicated)
                    "doc_metadata_ref": doc_metadata.doc_id,
                    
                    # Essential document info for quick access (ChromaDB compatible)
                    "source": doc_metadata.file_path,
                    "title": self._sanitize_metadata_value(doc_metadata.title),
                    "doc_type": doc_metadata.doc_type,
                    "domain": doc_metadata.domain,
                    "authority_score": doc_metadata.authority_score,
                    "product_entities": json.dumps(doc_metadata.product_entities) if doc_metadata.product_entities else "[]",
                    "categories": json.dumps(doc_metadata.categories) if doc_metadata.categories else "[]"
                }
            }
            
            chunks.append(chunk_data)
        
        return chunks
    
    def _sanitize_metadata_value(self, value: Any) -> str:
        """Sanitize metadata value to ensure it's ChromaDB compatible and valid JSON if needed"""
        if value is None:
            return ""
        
        # Convert to string
        str_value = str(value)
        
        # Check if it looks like JSON but isn't valid JSON (like markdown links)
        if str_value.startswith('[') and not str_value.startswith('[['):
            # Check if it's actually valid JSON
            try:
                json.loads(str_value)
                return str_value  # It's valid JSON, keep as is
            except json.JSONDecodeError:
                # It's not valid JSON (like markdown links), escape it
                return json.dumps(str_value)
        
        # For other values, return as string
        return str_value
    
    def _create_enhanced_document(self, original_doc: Document, doc_metadata: DocumentMetadata, 
                                 chunks: List[Dict[str, Any]]) -> Document:
        """Create enhanced document with reference-based metadata"""
        # Create enhanced metadata that includes document-level info (ChromaDB compatible)
        enhanced_metadata = {
            # Document-level metadata
            "doc_id": doc_metadata.doc_id,
            "canonical_url": doc_metadata.canonical_url,
            "domain": doc_metadata.domain,
            "doc_type": doc_metadata.doc_type,
            "language": doc_metadata.language,
            "published_at": doc_metadata.published_at or "",
            "updated_at": doc_metadata.updated_at or "",
            "effective_date": doc_metadata.effective_date or "",
            "expires_at": doc_metadata.expires_at or "",
            "authority_score": doc_metadata.authority_score,
            "geo_scope": doc_metadata.geo_scope,
            "currency": doc_metadata.currency,
            "product_entities": json.dumps(doc_metadata.product_entities) if doc_metadata.product_entities else "[]",
            "title": self._sanitize_metadata_value(doc_metadata.title),
            "categories": json.dumps(doc_metadata.categories) if doc_metadata.categories else "[]",
            "file_path": doc_metadata.file_path,
            "file_type": doc_metadata.file_type,
            "file_name": doc_metadata.file_name,
            
            # Processing metadata
            "chunks_count": len(chunks),
            "created_at": doc_metadata.created_at,
            "updated_at_processing": doc_metadata.updated_at_processing
        }
        
        # Create enhanced document
        enhanced_doc = Document(
            text=original_doc.text,
            metadata=enhanced_metadata,
            id_=doc_metadata.doc_id
        )
        
        return enhanced_doc
    
    def get_chunk_metadata(self, chunk_id: str) -> Optional[ChunkMetadata]:
        """Get chunk metadata by ID"""
        return self.chunk_metadata.get(chunk_id)
    
    def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by ID"""
        return self.metadata_extractor.get_document_metadata(doc_id)
    
    def get_chunks_by_document(self, doc_id: str) -> List[ChunkMetadata]:
        """Get all chunks for a specific document"""
        return [chunk for chunk in self.chunk_metadata.values() if chunk.doc_id == doc_id]
    
    def search_chunks_by_criteria(self, criteria: Dict[str, Any]) -> List[ChunkMetadata]:
        """Search chunks by various criteria"""
        matching_chunks = []
        
        for chunk in self.chunk_metadata.values():
            match = True
            for key, value in criteria.items():
                if hasattr(chunk, key):
                    chunk_value = getattr(chunk, key)
                    if isinstance(value, list):
                        if not any(v in chunk_value for v in value):
                            match = False
                            break
                    else:
                        if chunk_value != value:
                            match = False
                            break
                else:
                    match = False
                    break
            
            if match:
                matching_chunks.append(chunk)
        
        return matching_chunks
    
    def _load_chunk_metadata(self):
        """Load chunk metadata from file if it exists"""
        try:
            if os.path.exists(self.chunks_file):
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chunk_id, chunk_data in data.items():
                        self.chunk_metadata[chunk_id] = ChunkMetadata(**chunk_data)
                print(f"✓ Loaded {len(self.chunk_metadata)} chunks from {self.chunks_file}")
        except Exception as e:
            print(f"⚠ Error loading chunk metadata: {e}")
            self.chunk_metadata = {}
    
    def _save_chunk_metadata(self):
        """Save chunk metadata to file"""
        try:
            data = {}
            for chunk_id, chunk in self.chunk_metadata.items():
                data[chunk_id] = {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "section_path": chunk.section_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "token_count": chunk.token_count,
                    "has_numbers": chunk.has_numbers,
                    "has_currency": chunk.has_currency,
                    "embedding_version": chunk.embedding_version,
                    "created_at": chunk.created_at
                }
            
            with open(self.chunks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(self.chunk_metadata)} chunks to {self.chunks_file}")
        except Exception as e:
            print(f"⚠ Error saving chunk metadata: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        doc_metadata = self.metadata_extractor.get_all_document_metadata()
        
        return {
            "total_documents": len(doc_metadata),
            "total_chunks": len(self.chunk_metadata),
            "documents_by_type": self._count_by_attribute(doc_metadata, "doc_type"),
            "documents_by_domain": self._count_by_attribute(doc_metadata, "domain"),
            "chunks_with_numbers": sum(1 for chunk in self.chunk_metadata.values() if chunk.has_numbers),
            "chunks_with_currency": sum(1 for chunk in self.chunk_metadata.values() if chunk.has_currency),
            "average_authority_score": sum(doc.authority_score for doc in doc_metadata.values()) / len(doc_metadata) if doc_metadata else 0
        }
    
    def _count_by_attribute(self, items: Dict[str, Any], attribute: str) -> Dict[str, int]:
        """Count items by a specific attribute"""
        counts = {}
        for item in items.values():
            value = getattr(item, attribute, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
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
                } for doc_id, doc in self.metadata_extractor.get_all_document_metadata().items()
            },
            "chunk_metadata": {
                chunk_id: {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "section_path": chunk.section_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "token_count": chunk.token_count,
                    "has_numbers": chunk.has_numbers,
                    "has_currency": chunk.has_currency,
                    "created_at": chunk.created_at
                } for chunk_id, chunk in self.chunk_metadata.items()
            },
            "processing_stats": self.get_processing_stats()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported metadata to {output_file}")
        return export_data
