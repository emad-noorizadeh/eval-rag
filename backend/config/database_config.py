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
Database Configuration for RAG System
Author: Emad Noorizadeh
"""

import os
import chromadb
from typing import Optional, Dict, Any
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage import StorageContext

class DatabaseConfig:
    """Manages database configuration and connections"""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = None):
        self.db_path = db_path
        self.collection_name = collection_name
        self.chroma_client = None
        self.chroma_collection = None
        self.vector_store = None
        self.storage_context = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure database directory exists
            os.makedirs(self.db_path, exist_ok=True)
            
            # Use config collection name if not provided
            if self.collection_name is None:
                from config import get_collection_name
                self.collection_name = get_collection_name()
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            
            # Get or create collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize LlamaIndex components
            self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            print(f"✓ Database initialized: {self.db_path}")
            print(f"✓ Collection: {self.collection_name}")
            
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise
    
    def get_chroma_client(self) -> chromadb.ClientAPI:
        """Get ChromaDB client"""
        if not self.chroma_client:
            raise ValueError("ChromaDB client not initialized")
        return self.chroma_client
    
    def get_chroma_collection(self) -> chromadb.Collection:
        """Get ChromaDB collection"""
        if not self.chroma_collection:
            raise ValueError("ChromaDB collection not initialized")
        return self.chroma_collection
    
    def get_vector_store(self) -> ChromaVectorStore:
        """Get LlamaIndex vector store"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        return self.vector_store
    
    def get_storage_context(self) -> StorageContext:
        """Get LlamaIndex storage context"""
        if not self.storage_context:
            raise ValueError("Storage context not initialized")
        return self.storage_context
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        if not self.chroma_collection:
            return {"error": "Collection not initialized"}
        
        coll = self.chroma_collection
        n_vectors = coll.count()  # this is your chunk count

        # derive document count by unique source/doc_id in metadatas
        unique_docs = set()
        batch = 1000
        offset = 0
        while offset < n_vectors:
            got = coll.get(include=["metadatas"], limit=batch, offset=offset)
            metas = (got or {}).get("metadatas", []) or []
            for m in metas:
                if not m:
                    continue
                src = m.get("source") or m.get("doc_id") or m.get("file_name")
                if src:
                    unique_docs.add(src)
            offset += batch

        return {
            "documents": len(unique_docs),     # unique sources
            "chunks": n_vectors,               # total vectors
            "collection_name": self.collection_name,
            "db_path": self.db_path,
            "capabilities": ["semantic"],
        }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        if not self.chroma_collection:
            raise ValueError("Collection not initialized")
        
        # Delete all documents
        all_docs = self.chroma_collection.get()
        if all_docs['ids']:
            self.chroma_collection.delete(ids=all_docs['ids'])
            print(f"✓ Cleared {len(all_docs['ids'])} documents from collection")
        else:
            print("ℹ Collection is already empty")
    
    def delete_document(self, doc_id: str):
        """Delete a specific document from the collection by finding all its chunks"""
        if not self.chroma_collection:
            raise ValueError("Collection not initialized")
        
        # Find all chunk IDs that belong to this document
        # We need to search by source, doc_id, or file_name in metadata
        chunk_ids_to_delete = []
        
        # Get all chunks to find matching ones
        result = self.chroma_collection.get(include=['metadatas'])
        
        for chunk_id, metadata in zip(result['ids'], result['metadatas']):
            # Check if this chunk belongs to the document we want to delete
            if (metadata.get('source') == doc_id or 
                metadata.get('doc_id') == doc_id or 
                metadata.get('file_name') == doc_id):
                chunk_ids_to_delete.append(chunk_id)
        
        if chunk_ids_to_delete:
            # Delete all chunks belonging to this document
            self.chroma_collection.delete(ids=chunk_ids_to_delete)
            print(f"✓ Deleted {len(chunk_ids_to_delete)} chunks for document: {doc_id}")
        else:
            print(f"⚠ No chunks found for document: {doc_id}")
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        if not self.chroma_collection:
            raise ValueError("Collection not initialized")
        
        try:
            result = self.chroma_collection.get(ids=[doc_id])
            if result['ids']:
                return {
                    "id": result['ids'][0],
                    "text": result['documents'][0],
                    "metadata": result['metadatas'][0]
                }
            return None
        except Exception as e:
            print(f"Error retrieving document {doc_id}: {e}")
            return None
    
    def list_documents(self, limit: int = 10) -> list:
        """List documents in the collection"""
        if not self.chroma_collection:
            raise ValueError("Collection not initialized")
        
        try:
            result = self.chroma_collection.get(limit=limit)
            documents = []
            for i in range(len(result['ids'])):
                documents.append({
                    "id": result['ids'][i],
                    "text": result['documents'][i][:100] + "..." if len(result['documents'][i]) > 100 else result['documents'][i],
                    "metadata": result['metadatas'][i]
                })
            return documents
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database"""
        try:
            if not self.chroma_client:
                return {"status": "error", "message": "ChromaDB client not initialized"}
            
            if not self.chroma_collection:
                return {"status": "error", "message": "Collection not initialized"}
            
            # Test basic operations
            count = self.chroma_collection.count()
            
            return {
                "status": "healthy",
                "database_path": self.db_path,
                "collection_name": self.collection_name,
                "document_count": count,
                "client_status": "connected"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {e}"
            }
