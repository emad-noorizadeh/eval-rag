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
RAG Utilities for metadata extraction and document processing
Author: Emad Noorizadeh
"""

import re
from typing import List, Dict, Any
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class MetadataExtractor:
    """Handles extraction of metadata from document content"""
    
    def __init__(self, config_getter):
        """
        Initialize metadata extractor with configuration getter function
        
        Args:
            config_getter: Function to get configuration values (e.g., get_config)
        """
        self.get_config = config_getter
    
    def extract_content_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from document content using configuration options"""
        # Get configuration options
        extract_headings = self.get_config("data", "metadata_extraction.extract_headings")
        extract_links = self.get_config("data", "metadata_extraction.extract_links")
        extract_dates = self.get_config("data", "metadata_extraction.extract_dates")
        extract_emails = self.get_config("data", "metadata_extraction.extract_emails")
        extract_urls = self.get_config("data", "metadata_extraction.extract_urls")
        extract_categories = self.get_config("data", "metadata_extraction.extract_categories")
        max_heading_lines = self.get_config("data", "metadata_extraction.max_heading_lines")
        max_category_lines = self.get_config("data", "metadata_extraction.max_category_lines")
        
        metadata = {}
        
        # Extract first line as potential title/headline
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line:
                metadata['title'] = first_line
                metadata['headline'] = first_line
                
                # Check if first line looks like a URL or link
                if extract_links and first_line.startswith('[') and '](' in first_line and ')' in first_line:
                    link_metadata = self._extract_link_metadata(first_line)
                    metadata.update(link_metadata)
                
                # Check if first line looks like a heading
                if extract_headings and first_line.startswith('#'):
                    heading_metadata = self._extract_heading_metadata(first_line)
                    metadata.update(heading_metadata)
        
        # Extract markdown headings (limit to prevent metadata overflow)
        if extract_headings:
            headings = self._extract_markdown_headings(lines, max_heading_lines)
            if headings:
                metadata['headings'] = headings[:5]  # Limit to 5 headings
                metadata['main_heading'] = headings[0]['text'] if headings else None
        
        # Extract potential categories or tags
        if extract_categories:
            categories = self._extract_categories(lines, max_category_lines)
            if categories:
                metadata['categories'] = list(set(categories))
        
        # Extract document structure info
        metadata.update(self._extract_document_structure(text, lines))
        
        # Extract potential dates
        if extract_dates:
            dates_metadata = self._extract_dates(text)
            metadata.update(dates_metadata)
        
        # Extract email addresses
        if extract_emails:
            emails = self._extract_emails(text)
            if emails:
                metadata['emails'] = emails[:5]  # Limit to 5 emails
        
        # Extract URLs
        if extract_urls:
            urls = self._extract_urls(text)
            if urls:
                metadata['urls'] = urls[:5]  # Limit to 5 URLs
        
        # Add processing timestamp
        metadata['processed_at'] = datetime.now().isoformat()
        
        # Convert complex metadata to ChromaDB-compatible format
        return self._convert_metadata_for_chromadb(metadata)
    
    def _extract_link_metadata(self, first_line: str) -> Dict[str, Any]:
        """Extract metadata from markdown link format"""
        link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', first_line)
        if link_match:
            return {
                'link_text': link_match.group(1),
                'link_url': link_match.group(2),
                'is_link': True
            }
        return {}
    
    def _extract_heading_metadata(self, first_line: str) -> Dict[str, Any]:
        """Extract metadata from markdown heading format"""
        return {
            'heading_level': len(first_line) - len(first_line.lstrip('#')),
            'heading_text': first_line.lstrip('#').strip(),
            'is_heading': True
        }
    
    def _extract_markdown_headings(self, lines: List[str], max_lines: int) -> List[Dict[str, Any]]:
        """Extract markdown headings from document lines"""
        headings = []
        for line in lines[:max_lines]:
            line = line.strip()
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                headings.append({
                    'level': level,
                    'text': heading_text[:100]  # Limit heading text length
                })
        return headings
    
    def _extract_categories(self, lines: List[str], max_lines: int) -> List[str]:
        """Extract categories from document content"""
        categories = []
        for line in lines[:max_lines]:
            line = line.strip().lower()
            if any(keyword in line for keyword in ['bank', 'financial', 'credit', 'loan', 'account']):
                categories.append('financial')
            if any(keyword in line for keyword in ['reward', 'bonus', 'deal', 'offer']):
                categories.append('rewards')
            if any(keyword in line for keyword in ['service', 'support', 'help']):
                categories.append('service')
        return categories
    
    def _extract_document_structure(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """Extract basic document structure information"""
        return {
            'line_count': len(lines),
            'word_count': len(text.split()),
            'char_count': len(text)
        }
    
    def _extract_dates(self, text: str) -> Dict[str, Any]:
        """Extract dates from document content"""
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\w+ \d{1,2}, \d{4}\b'  # Month DD, YYYY
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates_found.extend(matches)
        
        if dates_found:
            return {
                'dates_found': dates_found[:10],  # Limit to 10 dates
                'latest_date': max(dates_found) if dates_found else None
            }
        return {}
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from document content"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from document content"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def _convert_metadata_for_chromadb(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert complex metadata to ChromaDB-compatible format"""
        converted = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, type(None))):
                converted[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                if all(isinstance(item, (str, int, float)) for item in value):
                    converted[key] = ', '.join(str(item) for item in value)
                else:
                    # For complex lists, convert to JSON string
                    converted[key] = json.dumps(value)
            elif isinstance(value, dict):
                # Convert dicts to JSON string
                converted[key] = json.dumps(value)
            else:
                # Convert other types to string
                converted[key] = str(value)
        
        return converted


class DocumentProcessor:
    """Handles document processing and enhancement"""
    
    def __init__(self, config_getter):
        """
        Initialize document processor with configuration getter function
        
        Args:
            config_getter: Function to get configuration values (e.g., get_config)
        """
        self.get_config = config_getter
        self.metadata_extractor = MetadataExtractor(config_getter)
    
    def enhance_document_metadata(self, documents: List) -> List:
        """Enhance documents with extracted metadata from content"""
        enhanced_documents = []
        
        for doc in documents:
            # Extract metadata from document content
            content_metadata = self.metadata_extractor.extract_content_metadata(doc.text)
            
            # Merge with existing metadata
            enhanced_metadata = {**doc.metadata, **content_metadata}
            
            # Create enhanced document
            from llama_index.core import Document
            enhanced_doc = Document(
                text=doc.text,
                metadata=enhanced_metadata,
                id_=doc.id_
            )
            enhanced_documents.append(enhanced_doc)
        
        return enhanced_documents
    
    def should_extract_metadata(self) -> bool:
        """Check if metadata extraction is enabled"""
        return self.get_config("data", "extract_metadata")
    
    def should_use_recursive(self) -> bool:
        """Check if recursive directory traversal is enabled"""
        return self.get_config("data", "recursive")


def create_file_metadata_function():
    """Create a file metadata function for SimpleDirectoryReader"""
    def file_metadata(fname):
        return {
            "source": fname,
            "file_type": Path(fname).suffix,
            "file_name": Path(fname).name,
            "file_path": str(fname)
        }
    return file_metadata


def get_supported_extensions():
    """Get supported file extensions from configuration"""
    # This would need to be imported from config in actual usage
    return [".txt", ".md", ".pdf"]  # Default fallback


def validate_document_folder(folder_path: Path) -> None:
    """Validate that the folder path exists and is a directory"""
    if not folder_path.exists():
        raise ValueError(f"Folder path does not exist: {folder_path}")
    
    if not folder_path.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")


def get_document_files(folder_path: Path, file_extensions: List[str]) -> List[Path]:
    """Get list of document files in the folder"""
    files = []
    for ext in file_extensions:
        files.extend(folder_path.glob(f"**/*{ext}"))
    return files


def format_context_with_metadata(nodes: List[Dict[str, Any]]) -> tuple:
    """
    Format retrieved documents into context chunks with enhanced source and metadata information
    
    Args:
        nodes: List of retrieved document nodes
        
    Returns:
        Tuple of (context_str, debug_meta, valid_ids)
    """
    chunks = []
    debug_meta = []
    valid_ids = []
    
    # Group chunks by source for better organization
    source_groups = {}
    for i, node in enumerate(nodes):
        text = node.get("text", "")
        meta = node.get("metadata", {})
        source = meta.get("source") or meta.get("file_path") or meta.get("document_id") or "unknown"
        
        if source not in source_groups:
            source_groups[source] = []
        
        cid = f"C{i+1}"
        source_groups[source].append({
            "id": cid,
            "text": text,
            "metadata": meta,
            "score": node.get("score", 0.0)
        })
    
    # Format with source headers and metadata
    for source, source_chunks in source_groups.items():
        # Add source header with metadata
        source_metadata = []
        if source_chunks:
            first_meta = source_chunks[0]["metadata"]
            
            # Extract relevant metadata for source header
            if first_meta.get("category"):
                source_metadata.append(f"Category: {first_meta['category']}")
            if first_meta.get("sentiment"):
                source_metadata.append(f"Sentiment: {first_meta['sentiment']}")
            if first_meta.get("title"):
                source_metadata.append(f"Title: {first_meta['title']}")
            if first_meta.get("word_count"):
                source_metadata.append(f"Words: {first_meta['word_count']}")
        
        # Create source header
        source_header = f"📄 **Source: {source}**"
        if source_metadata:
            source_header += f" ({', '.join(source_metadata)})"
        
        chunks.append(source_header)
        
        # Add chunks for this source
        for chunk in source_chunks:
            cid = chunk["id"]
            text = chunk["text"]
            meta = chunk["metadata"]
            score = chunk["score"]
            
            # Add chunk-level metadata context
            chunk_metadata = []
            if meta.get("chunk_sentiment"):
                chunk_metadata.append(f"Sentiment: {meta['chunk_sentiment']}")
            if meta.get("chunk_category"):
                chunk_metadata.append(f"Category: {meta['chunk_category']}")
            if meta.get("has_headings"):
                chunk_metadata.append("Has Headings: Yes")
            if meta.get("contains_email"):
                chunk_metadata.append("Contains Email: Yes")
            
            # Format chunk with metadata
            chunk_text = f"{cid}: {text}"
            if chunk_metadata:
                chunk_text += f" [{', '.join(chunk_metadata)}]"
            
            chunks.append(chunk_text)
            valid_ids.append(cid)
            
            debug_meta.append({
                "rank": len(valid_ids),
                "source": source,
                "chars": len(text),
                "chunk_id": cid,
                "score": score,
                "metadata": meta
            })
        
        chunks.append("")  # Empty line between sources
    
    # Remove trailing empty lines
    while chunks and chunks[-1] == "":
        chunks.pop()
    
    context_str = "\n".join(chunks)
    return context_str, debug_meta, valid_ids


def filter_chunks_by_similarity(chunks: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """
    Filter chunks based on similarity threshold.
    
    Args:
        chunks: List of chunks with 'score' field
        threshold: Minimum similarity score to keep
        
    Returns:
        List of chunks that meet the similarity threshold
    """
    filtered_chunks = []
    for chunk in chunks:
        score = chunk.get("score", 0.0)
        if score >= threshold:
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def get_filtering_metrics(original_chunks: List[Dict[str, Any]], filtered_chunks: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
    """
    Get metrics about the filtering process.
    
    Args:
        original_chunks: Original list of chunks before filtering
        filtered_chunks: List of chunks after filtering
        threshold: Similarity threshold used
        
    Returns:
        Dictionary with filtering metrics
    """
    filtered_scores = [chunk.get("score", 0.0) for chunk in filtered_chunks]
    
    return {
        "threshold": threshold,
        "original_chunks": len(original_chunks),
        "filtered_chunks": len(filtered_chunks),
        "filtered_out_count": len(original_chunks) - len(filtered_chunks),
        "avg_filtered_score": sum(filtered_scores) / len(filtered_scores) if filtered_scores else 0.0,
        "min_filtered_score": min(filtered_scores) if filtered_scores else 0.0,
        "max_filtered_score": max(filtered_scores) if filtered_scores else 0.0
    }




