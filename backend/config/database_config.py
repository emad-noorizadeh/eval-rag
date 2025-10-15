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
import shutil
from datetime import datetime
from pathlib import Path
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
        self.collection_reset_due_to_dimension_change = False
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure database directory exists
            os.makedirs(self.db_path, exist_ok=True)
            
            # Use config collection name if not provided
            if self.collection_name is None:
                from . import get_collection_name
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
            self._log_embedding_shape()
            
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise
    
    def _get_expected_embedding_dimension(self) -> Optional[int]:
        """Return the expected embedding dimension from configuration, if known."""
        try:
            from . import get_config
        except Exception:
            return None
        
        model_name = get_config("models", "embedding_model")
        if not model_name:
            return None
        
        # Known embedding dimensions for common OpenAI models
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(model_name)
    
    def _get_backup_root(self) -> Path:
        """Determine backup directory for Chroma data."""
        backup_path = None
        try:
            from . import get_config
            backup_path = get_config("database", "backup_path")
        except Exception:
            backup_path = None
        
        if not backup_path:
            backup_path = f"{self.db_path}_backup"
        
        return Path(backup_path)
    
    def _reinitialize_collection(self):
        """Recreate collection, vector store, and storage context."""
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
    
    def _handle_embedding_dimension_mismatch(self, sample_count: int, found_dim: int, expected_dim: int):
        """Reset the collection when stored embeddings have the wrong dimension."""
        print("⚠️  Resetting Chroma collection due to embedding dimension mismatch...")
        backup_path = None
        try:
            src_path = Path(self.db_path)
            if src_path.exists():
                backup_root = self._get_backup_root()
                backup_root.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup_path = backup_root / f"{self.collection_name}_dim{found_dim}_backup_{timestamp}"
                shutil.copytree(src_path, backup_path)
                print(f"📦 Backed up existing Chroma database to {backup_path}")
        except Exception as backup_err:
            print(f"⚠️  Could not backup Chroma database before reset: {backup_err}")
            backup_path = None
        
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            print(f"🗑️  Removed mismatched collection '{self.collection_name}' (dimension {found_dim})")
        except Exception as delete_err:
            print(f"✗ Failed to delete mismatched collection automatically: {delete_err}")
            print("✗ Please delete the collection manually and rebuild the index.")
            return
        
        self._reinitialize_collection()
        self.collection_reset_due_to_dimension_change = True
        
        if backup_path:
            print(f"ℹ️  Previous collection data backed up to: {backup_path}")
        if sample_count:
            print("⚠️  The collection is now empty. Re-run your indexing workflow to regenerate embeddings.")
        else:
            print("ℹ️  Collection metadata reset. Add documents before querying.")
    
    def _log_embedding_shape(self):
        """Inspect a sample of embeddings in Chroma and report their dimensions."""
        if not self.chroma_collection:
            print("⚠️  Chroma collection not initialized; cannot inspect embeddings")
            return
        
        try:
            sample = self.chroma_collection.peek()
            embeddings = (sample or {}).get("embeddings")
            if embeddings is None or (hasattr(embeddings, "__len__") and len(embeddings) == 0):
                # Fallback: explicit get call in case peek omits embeddings
                sample = self.chroma_collection.get(limit=5, include=["embeddings"])
                embeddings = (sample or {}).get("embeddings")
            
            if embeddings is None or (hasattr(embeddings, "__len__") and len(embeddings) == 0):
                print("ℹ️  No embeddings available in collection to inspect yet")
                return
            
            if hasattr(embeddings, "tolist"):
                embeddings = embeddings.tolist()
            
            first_vector = embeddings[0]
            if hasattr(first_vector, "tolist"):
                first_vector = first_vector.tolist()
            vector_dim = len(first_vector) if first_vector is not None else 0
            vector_count = len(embeddings)
            expected_dim = self._get_expected_embedding_dimension()
            
            if expected_dim is not None:
                if vector_dim == expected_dim:
                    print(f"✓ Chroma embedding sample: {vector_count}x{vector_dim} (expected {expected_dim})")
                else:
                    print(f"⚠️  Chroma embedding sample: {vector_count}x{vector_dim} (expected {expected_dim})")
                    print("⚠️  Stored embeddings dimension does not match expected configuration")
                    self._handle_embedding_dimension_mismatch(vector_count, vector_dim, expected_dim)
            else:
                print(f"ℹ️  Chroma embedding sample: {vector_count}x{vector_dim}")
        except Exception as e:
            print(f"⚠️  Could not inspect Chroma embeddings: {e}")
    
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
