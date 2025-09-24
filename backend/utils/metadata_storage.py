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
Metadata Storage Utility
Author: Emad Noorizadeh

Handles storage and retrieval of document metadata in JSON format.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

class MetadataStorage:
    """Handles document metadata storage and retrieval"""
    
    def __init__(self, index_folder: str = "index"):
        self.index_folder = Path(index_folder)
        self.metadata_file = self.index_folder / "document_metadata.json"
        self.index_folder.mkdir(exist_ok=True)
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load document metadata from JSON file"""
        if not self.metadata_file.exists():
            return {
                "documents": {},
                "last_updated": None,
                "total_documents": 0,
                "total_chunks": 0
            }
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {
                "documents": {},
                "last_updated": None,
                "total_documents": 0,
                "total_chunks": 0
            }
    
    def save_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Save document metadata to JSON file"""
        try:
            metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def add_document_metadata(self, filename: str, document_metadata: Dict[str, Any], chunks: List[Dict[str, Any]]) -> bool:
        """Add or update document metadata"""
        metadata = self.load_metadata()
        
        # Prepare chunk information (simplified)
        chunk_info = []
        for chunk in chunks:
            chunk_info.append({
                "chunk_id": chunk.get("chunk_id", ""),
                "token_count": chunk.get("token_count", 0),
                "first_line": chunk.get("first_line", "")
            })
        
        # Add document metadata
        metadata["documents"][filename] = {
            **document_metadata,
            "chunks": chunk_info,
            "chunk_count": len(chunk_info),
            "added_at": datetime.now().isoformat()
        }
        
        # Update totals
        metadata["total_documents"] = len(metadata["documents"])
        metadata["total_chunks"] = sum(doc.get("chunk_count", 0) for doc in metadata["documents"].values())
        
        # Add collection information
        if "collection_info" not in metadata:
            metadata["collection_info"] = {}
        
        metadata["collection_info"].update({
            "total_documents": metadata["total_documents"],
            "total_chunks": metadata["total_chunks"],
            "embedding_model": "text-embedding-3-small",
            "chunk_size": 1024,
            "chunk_overlap": 128,
            "last_updated": datetime.now().isoformat()
        })
        
        return self.save_metadata(metadata)
    
    def remove_document_metadata(self, filename: str) -> bool:
        """Remove document metadata"""
        metadata = self.load_metadata()
        
        if filename in metadata["documents"]:
            del metadata["documents"][filename]
            
            # Update totals
            metadata["total_documents"] = len(metadata["documents"])
            metadata["total_chunks"] = sum(doc.get("chunk_count", 0) for doc in metadata["documents"].values())
            
            # Update collection info
            if "collection_info" in metadata:
                metadata["collection_info"].update({
                    "total_documents": metadata["total_documents"],
                    "total_chunks": metadata["total_chunks"],
                    "last_updated": datetime.now().isoformat()
                })
            
            return self.save_metadata(metadata)
        
        return True
    
    def get_document_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific document"""
        metadata = self.load_metadata()
        return metadata["documents"].get(filename)
    
    def get_all_documents(self) -> Dict[str, Any]:
        """Get all document metadata"""
        return self.load_metadata()
    
    def clear_metadata(self) -> bool:
        """Clear all metadata"""
        try:
            if self.metadata_file.exists():
                os.remove(self.metadata_file)
            return True
        except Exception as e:
            print(f"Error clearing metadata: {e}")
            return False
    
    def update_chunk_info(self, filename: str, chunks: List[Dict[str, Any]]) -> bool:
        """Update chunk information for a document"""
        metadata = self.load_metadata()
        
        if filename not in metadata["documents"]:
            return False
        
        # Update chunk information
        chunk_info = []
        for chunk in chunks:
            chunk_info.append({
                "chunk_id": chunk.get("chunk_id", ""),
                "token_count": chunk.get("token_count", 0),
                "first_line": chunk.get("first_line", "")
            })
        
        metadata["documents"][filename]["chunks"] = chunk_info
        metadata["documents"][filename]["chunk_count"] = len(chunk_info)
        
        # Update total chunks
        metadata["total_chunks"] = sum(doc.get("chunk_count", 0) for doc in metadata["documents"].values())
        
        return self.save_metadata(metadata)
