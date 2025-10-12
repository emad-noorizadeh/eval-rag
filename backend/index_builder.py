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
Index Builder for RAG System using LlamaIndex
Author: Emad Noorizadeh
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
import hashlib
from datetime import datetime
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
# Settings import removed - using direct component passing instead
from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config, get_data_folder, get_database_path, get_collection_name, get_chunking_params
from utils.rag_utils import DocumentProcessor, create_file_metadata_function, validate_document_folder
# Hybrid metadata extractor removed - using semantic only
from processors.enhanced_document_processor import EnhancedDocumentProcessor as NewEnhancedDocumentProcessor
from processors.llm_metadata_extractor import HybridMetadataExtractor
from utils.metadata_storage import MetadataStorage

# Tokenizer functionality removed - using word-count-based chunking only

# Disable default tokenizer in LlamaIndex settings
def _disable_llamaindex_tokenizer():
    """Disable the default tokenizer in LlamaIndex to prevent tiktoken usage"""
    try:
        # Set a dummy tokenizer that doesn't require web access
        def dummy_tokenizer(text: str) -> List[int]:
            return list(range(len(text.split())))
        
        # Override the default tokenizer
        Settings.tokenizer = dummy_tokenizer
        print("✅ Disabled LlamaIndex default tokenizer")
    except Exception as e:
        print(f"⚠️  Could not disable LlamaIndex tokenizer: {e}")

# Call this at module level
_disable_llamaindex_tokenizer()

def _get_word_count_splitter(chunk_size: int, chunk_overlap: int):
    """Get a word-count-based splitter instead of tokenizer"""
    def word_count_split(text: str) -> List[str]:
        """Split text by word count instead of tokens"""
        if not text:
            return []
        
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            # Calculate end position with overlap
            end = min(start + chunk_size, len(words))
            
            # Get chunk text
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - chunk_overlap
            if start >= len(words):
                break
        
        return chunks
    
    return word_count_split

# Configurable encoder removed - using word-count-based chunking only

def _token_hist(name: str, texts: List[str], encode):
    """Log token histogram for observability"""
    if not texts:
        print(f"{name}: (no chunks)")
        return
    sizes = [len(t.split()) for t in texts]
    print(f"{name} tokens — min:{min(sizes)}, max:{max(sizes)}, avg:{sum(sizes)/len(sizes):.1f}, n={len(sizes)}")

class IndexBuilder:
    """Builds and manages vector indices from text files using LlamaIndex"""
    
    def __init__(self, model_manager: ModelManager, collection_name: str = None, 
                 db_path: str = None, chunk_size: int = None, chunk_overlap: int = None):
        self.model_manager = model_manager
        
        # Normalize config
        self.collection_name = collection_name or get_collection_name()
        self.chunk_size = int(chunk_size or get_config("chunking", "chunk_size") or 1024)
        self.chunk_overlap = int(chunk_overlap or get_config("chunking", "chunk_overlap") or 128)
        
        # DB + vector store
        db_path = db_path or get_database_path()
        self.db_config = DatabaseConfig(db_path=db_path, collection_name=self.collection_name)
        
        # Embedder & configurable splitter
        self.embed_model = self.model_manager.get_embedding_model()
        
        # Use SentenceSplitter by default (no tokenizer needed)
        use_sentence_splitter = get_config("chunking", "use_sentence_splitter")
        if use_sentence_splitter is None:  # Default to True if not set
            use_sentence_splitter = True
        
        if use_sentence_splitter:
            # Use LlamaIndex SentenceSplitter (no tokenizer needed)
            self.node_parser = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            print(f"✅ Using SentenceSplitter chunking (chunk_size: {self.chunk_size}, overlap: {self.chunk_overlap})")
        else:
            # Use word-count-based splitting as fallback
            from utils.chunking_utils import get_word_count_splitter
            
            word_count_ratio = get_config("chunking", "word_count_ratio") or 0.75
            word_chunk_size = int(self.chunk_size * word_count_ratio)
            word_chunk_overlap = int(self.chunk_overlap * word_count_ratio)
            
            # Create a custom splitter that uses word count
            from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
            
            class WordCountSplitter(MetadataAwareTextSplitter):
                def __init__(self, chunk_size: int, chunk_overlap: int, **kwargs):
                    super().__init__(**kwargs)
                    self._chunk_size = chunk_size
                    self._chunk_overlap = chunk_overlap
                
                def split_text(self, text: str) -> List[str]:
                    return get_word_count_splitter(self._chunk_size, self._chunk_overlap)(text)
                
                def split_text_metadata_aware(self, text: str, metadata: dict = None, **kwargs) -> List[str]:
                    """Split text with metadata awareness (required by base class)"""
                    return self.split_text(text)
            
            self.node_parser = WordCountSplitter(
                chunk_size=word_chunk_size,
                chunk_overlap=word_chunk_overlap
            )
            print(f"✅ Using word-count-based chunking (chunk_size: {word_chunk_size} words, ratio: {word_count_ratio})")
        
        # processors (simplified)
        self.document_processor = DocumentProcessor(get_config)
        self.enhanced_processor = NewEnhancedDocumentProcessor(model_manager)
        
        # Enhanced metadata extraction using LLM
        self.metadata_extractor = HybridMetadataExtractor(get_config, model_manager)
        
        # Metadata storage
        self.metadata_storage = MetadataStorage("index")
        
        # NEW: build one persistent vector store & storage context now
        self.vector_store = self.db_config.get_vector_store()           # returns ChromaVectorStore bound to persistent collection
        self.storage_context = self.db_config.get_storage_context()     # bound to same collection

        # Bind an index to that store; no nodes yet
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context,
            embed_model=self.embed_model,
        )
    
    # Index is now initialized in __init__ - no lazy initialization needed
    
    
    def build_index_from_folder(self, folder_path: str = None, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Build index from all text files in a folder using LlamaIndex
        
        Args:
            folder_path: Path to folder containing text files (uses config default if None)
            file_extensions: List of file extensions to process (uses config default if None)
        
        Returns:
            Dictionary with build statistics
        """
        folder_path = folder_path or get_data_folder()
        file_extensions = file_extensions or get_config("data", "supported_extensions")
        folder_path = Path(folder_path)
        validate_document_folder(folder_path)

        try:
            recursive = self.document_processor.should_use_recursive()
            extract_metadata = self.document_processor.should_extract_metadata()

            # Get filtered document files (excludes .DS_Store and other system files)
            from utils.rag_utils import get_document_files
            document_files = get_document_files(folder_path, file_extensions)
            
            if not document_files:
                print(f"⚠️  No supported documents found in {folder_path}")
                return {
                    "success": False,
                    "message": "No supported documents found",
                    "documents_processed": 0,
                    "chunks_created": 0
                }
            
            print(f"📄 Found {len(document_files)} documents to process:")
            for doc_file in document_files:
                print(f"  - {doc_file.name}")
            
            # Load documents using SimpleDirectoryReader with file list
            reader = SimpleDirectoryReader(
                input_files=[str(f) for f in document_files],
                file_metadata=create_file_metadata_function()
            )
            documents = reader.load_data()

            if extract_metadata:
                documents = self.document_processor.enhance_document_metadata(documents)

            print(f"Loaded {len(documents)} documents from {folder_path}")

            # Extract enhanced metadata for each document before indexing
            document_metadata_map = {}
            for doc in documents:
                # Use file_name from metadata, fallback to source, then to doc ID
                filename = doc.metadata.get("file_name", doc.metadata.get("source", f"doc_{doc.id_}"))
                if filename and filename != "unknown":
                    try:
                        # Extract enhanced metadata from raw document text
                        enhanced_metadata = self.metadata_extractor.extract_metadata(doc.text)
                        document_metadata_map[filename] = enhanced_metadata
                        print(f"Extracted metadata for {filename}")
                    except Exception as e:
                        print(f"Error extracting metadata for {filename}: {e}")
                        # Use basic metadata as fallback
                        document_metadata_map[filename] = {
                            "title": filename,
                            "doc_type": "document",
                            "domain": "unknown",
                            "language": "en",
                            "authority_score": 0.5,
                            "geo_scope": "unknown",
                            "currency": "USD",
                            "product_entities": [],
                            "categories": [],
                            "headings": [],
                            "links": [],
                            "dates": [],
                            "emails": [],
                            "urls": [],
                            "sentiment": "neutral",
                            "confidence": 0.0,
                            "extraction_method": "basic"
                        }

            # 1) Pre-split into nodes (token-aware)
            nodes = self.node_parser.get_nodes_from_documents(documents)
            print(f"Splitter produced {len(nodes)} nodes")

            # 2) Assign stable IDs + enrich metadata BEFORE insertion
            # Use simple word count instead of tokenizer
            def word_count_encoder(text: str) -> int:
                return len(text.split())
            
            for i, n in enumerate(nodes):
                src = (n.metadata or {}).get("file_name") or (n.metadata or {}).get("source") or f"doc_{i}"
                content_hash = hashlib.sha1((n.text or "").encode("utf-8")).hexdigest()[:8]
                stable_id = f"{src}__chunk_{i}__{content_hash}"
                n.id_ = stable_id
                n.metadata = dict(n.metadata or {})
                n.metadata.update({
                    "source": src,
                    "chunk_id": stable_id,
                    "doc_id": n.metadata.get("doc_id") or src,
                    "word_count": word_count_encoder(n.text or ""),
                    "first_line": (n.text or "").splitlines()[0][:160] if (n.text or "").strip() else ""
                })

            # 3) INSERT nodes into the already-bound index (LlamaIndex will embed)
            print("Inserting nodes into persistent Chroma-backed index...")
            self.index.insert_nodes(nodes)   # <— this actually writes to Chroma
            print("Insert complete.")

            # (Optional) persist storage context (good hygiene)
            try:
                self.storage_context.persist()
            except Exception:
                pass

            # Report counts from Chroma (not docstore)
            collection_size = self.db_config.get_chroma_collection().count()
            print(f"Chroma collection vectors: {collection_size}")

            # Optional: quick visibility
            _token_hist("Chunk", [n.text for n in nodes if getattr(n, "text", None)], word_count_encoder)

            # Chunk IDs and metadata are already set before insertion - no post-processing needed
            
            # Save document metadata with chunk information
            try:
                # Group chunks by source for metadata JSON (using the nodes we already have)
                doc_chunks = {}
                for n in nodes:
                    src = (n.metadata or {}).get("source", "unknown")
                    doc_chunks.setdefault(src, []).append({
                        "chunk_id": n.id_,
                        "text": n.text,
                        "token_count": n.metadata.get("token_count", 0),
                        "first_line": n.metadata.get("first_line", ""),
                        "score": 0.0  # Will be updated during retrieval
                    })
                
                # Persist per-doc metadata + chunks
                for filename, meta in document_metadata_map.items():
                    chunks = doc_chunks.get(filename, [])
                    self.metadata_storage.add_document_metadata(filename, meta, chunks)
                    print(f"Saved metadata for {filename} with {len(chunks)} chunks")
                
                print(f"Metadata saved to index/document_metadata.json")
            except Exception as e:
                print(f"Error saving metadata: {e}")
            
            return {
                "processed_files": len(documents),
                "total_chunks": collection_size,
                "errors": [],
                "collection_size": collection_size
            }

        except Exception as e:
            raise ValueError(f"Error building index: {str(e)}")
    
    def build_enhanced_index_from_folder(self, folder_path: str = None, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Build index with enhanced metadata extraction and reference linking
        
        Args:
            folder_path: Path to folder containing text files (uses config default if None)
            file_extensions: List of file extensions to process (uses config default if None)
        
        Returns:
            Dictionary with build statistics and enhanced metadata info
        """
        # Use configuration defaults if not provided
        folder_path = folder_path or get_data_folder()
        file_extensions = file_extensions or get_config("data", "supported_extensions")
        
        folder_path = Path(folder_path)
        validate_document_folder(folder_path)
        
        try:
            # Get configuration options
            recursive = self.document_processor.should_use_recursive()
            
            # Get filtered document files (excludes .DS_Store and other system files)
            from utils.rag_utils import get_document_files
            document_files = get_document_files(folder_path, file_extensions)
            
            if not document_files:
                print(f"⚠️  No supported documents found in {folder_path}")
                return {
                    "success": False,
                    "message": "No supported documents found",
                    "documents_processed": 0,
                    "chunks_created": 0,
                    "enhanced_metadata": {}
                }
            
            print(f"📄 Found {len(document_files)} documents to process:")
            for doc_file in document_files:
                print(f"  - {doc_file.name}")
            
            # Use LlamaIndex SimpleDirectoryReader with filtered file list
            reader = SimpleDirectoryReader(
                input_files=[str(f) for f in document_files],
                file_metadata=create_file_metadata_function()
            )
            documents = reader.load_data()
            
            print(f"Loaded {len(documents)} documents from {folder_path}")
            
            # Process documents with enhanced metadata extraction
            print("🔧 Processing documents with enhanced metadata extraction...")
            processed_docs, processing_stats = self.enhanced_processor.process_documents(
                documents, 
                chunk_size=self.chunk_size, 
                chunk_overlap=self.chunk_overlap
            )
            
            print(f"✅ Enhanced metadata extraction completed")
            print(f"   - Documents processed: {processing_stats['documents_processed']}")
            print(f"   - Chunks created: {processing_stats['chunks_created']}")
            print(f"   - Metadata extracted: {processing_stats['metadata_extracted']}")
            
            if processing_stats['errors']:
                print(f"   - Errors: {len(processing_stats['errors'])}")
                for error in processing_stats['errors']:
                    print(f"     ⚠ {error}")
            
            # Index is already initialized in __init__, just insert documents
            for doc in processed_docs:
                self.index.insert(doc)
            
            # Get collection info
            collection_size = self.db_config.get_chroma_collection().count()
            
            # Get enhanced processing stats
            enhanced_stats = self.enhanced_processor.get_processing_stats()
            
            return {
                "processed_files": len(processed_docs),
                "total_chunks": collection_size,
                "errors": processing_stats['errors'],
                "collection_size": collection_size,
                "enhanced_metadata": {
                    "total_documents": enhanced_stats['total_documents'],
                    "total_chunks": enhanced_stats['total_chunks'],
                    "documents_by_type": enhanced_stats['documents_by_type'],
                    "documents_by_domain": enhanced_stats['documents_by_domain'],
                    "chunks_with_numbers": enhanced_stats['chunks_with_numbers'],
                    "chunks_with_currency": enhanced_stats['chunks_with_currency'],
                    "average_authority_score": enhanced_stats['average_authority_score']
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error building enhanced index: {str(e)}")
    
    
    def add_document(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a single document to the index using LlamaIndex
        
        Args:
            text: Document text
            metadata: Optional metadata
        
        Returns:
            Document ID
        """
        if not text.strip():
            raise ValueError("Document text cannot be empty")
        
        # Create document ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        doc_metadata = dict(metadata or {})
        doc_metadata.update({
            "doc_id": doc_id,
            "source": doc_metadata.get("source", doc_id),   # ensure 'source' is present
            "added_at": str(datetime.now())
        })

        document = Document(text=text, metadata=doc_metadata, id_=doc_id)

        # Pre-split into nodes and insert them
        nodes = self.node_parser.get_nodes_from_documents([document])
        
        # Assign stable IDs and metadata
        def word_count_encoder(text: str) -> int:
            return len(text.split())
        
        for i, n in enumerate(nodes):
            # For uploaded files, use saved_filename if available, otherwise file_name or source
            src = (n.metadata or {}).get("saved_filename") or (n.metadata or {}).get("file_name") or (n.metadata or {}).get("source") or f"doc_{i}"
            content_hash = hashlib.sha1((n.text or "").encode("utf-8")).hexdigest()[:8]
            stable_id = f"{src}__chunk_{i}__{content_hash}"
            n.id_ = stable_id
            n.metadata = dict(n.metadata or {})
            n.metadata.update({
                "source": src,
                "chunk_id": stable_id,
                "doc_id": n.metadata.get("doc_id") or src,
                "word_count": word_count_encoder(n.text or ""),
                "first_line": (n.text or "").splitlines()[0][:160] if (n.text or "").strip() else ""
            })
        
        # Insert nodes into the persistent index
        self.index.insert_nodes(nodes)
        
        # Extract and save enhanced metadata for the added document
        try:
            # For uploaded files, use saved_filename if available, otherwise source or doc_id
            filename = doc_metadata.get("saved_filename") or doc_metadata.get("source", doc_id)
            enhanced_metadata = self.metadata_extractor.extract_metadata(text)
            
            # Build chunks from the nodes we just created
            doc_chunks = []
            for n in nodes:
                doc_chunks.append({
                    "chunk_id": n.id_,
                    "text": n.text,
                    "token_count": n.metadata.get("token_count", 0),
                    "first_line": n.metadata.get("first_line", ""),
                    "score": 0.0
                })
            
            # Save metadata
            self.metadata_storage.add_document_metadata(filename, enhanced_metadata, doc_chunks)
            print(f"Extracted and saved metadata for {filename}")
            
        except Exception as e:
            print(f"Error extracting metadata for added document: {e}")
        
        return doc_id
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for similar documents using LlamaIndex
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of search results
        """
        # Index is already initialized in __init__ - no need to check
        
        # Use retriever directly instead of query engine to avoid LLM dependency
        retriever = self.index.as_retriever(similarity_top_k=n_results)
        nodes = retriever.retrieve(query)
        
        # Format results
        formatted_results = []
        for node in nodes:
            # Handle both NodeWithScore and regular Node objects
            score = getattr(node, 'score', 0.0)
            node_id = getattr(node, 'node_id', getattr(node, 'id_', ''))
            text = getattr(node, 'text', '')
            metadata = getattr(node, 'metadata', {})
            
            formatted_results.append({
                "id": node_id,
                "text": text,
                "metadata": metadata,
                "score": score,
                "similarity_score": score
            })
        
        return formatted_results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        return self.db_config.get_collection_info()
    
    def clear_index(self):
        """Clear all documents from the index"""
        self.db_config.clear_collection()
        
        # Clear metadata storage
        self.metadata_storage.clear_metadata()
        
        # Reinitialize index (it's already bound to the persistent store)
        # No need to recreate - the index is already bound to the cleared collection
    
    def delete_document(self, doc_id: str):
        """Delete a specific document from the index"""
        # Get document info before deletion to find filename
        try:
            doc_info = self.db_config.get_document(doc_id)
            filename = doc_info.get("source", doc_id) if doc_info else doc_id
        except:
            filename = doc_id
        
        # Delete from index
        self.db_config.delete_document(doc_id)
        
        # Remove metadata
        self.metadata_storage.remove_document_metadata(filename)
    
    def update_chunking_params(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Update chunking parameters
        
        Args:
            chunk_size: New chunk size (optional)
            chunk_overlap: New chunk overlap (optional)
        """
        if chunk_size is not None:
            self.chunk_size = int(chunk_size)
        if chunk_overlap is not None:
            self.chunk_overlap = int(chunk_overlap)

        # Check which splitter to use
        use_sentence_splitter = get_config("chunking", "use_sentence_splitter")
        if use_sentence_splitter is None:
            use_sentence_splitter = True
        
        if use_sentence_splitter:
            # Use SentenceSplitter
            self.node_parser = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            print(f"✓ Chunking parameters updated: size={self.chunk_size}, overlap={self.chunk_overlap}")
            print(f"✓ Using SentenceSplitter chunking")
        else:
            # Use word-count-based splitter
            word_count_ratio = get_config("chunking", "word_count_ratio") or 0.75
            word_chunk_size = int(self.chunk_size * word_count_ratio)
            word_chunk_overlap = int(self.chunk_overlap * word_count_ratio)
            
            from llama_index.core.node_parser.interface import MetadataAwareTextSplitter
            from utils.chunking_utils import get_word_count_splitter
            
            class WordCountSplitter(MetadataAwareTextSplitter):
                def __init__(self, chunk_size: int, chunk_overlap: int, **kwargs):
                    super().__init__(**kwargs)
                    self._chunk_size = chunk_size
                    self._chunk_overlap = chunk_overlap
                
                def split_text(self, text: str) -> List[str]:
                    return get_word_count_splitter(self._chunk_size, self._chunk_overlap)(text)
                
                def split_text_metadata_aware(self, text: str, metadata: dict = None, **kwargs) -> List[str]:
                    return self.split_text(text)
            
            self.node_parser = WordCountSplitter(
                chunk_size=word_chunk_size,
                chunk_overlap=word_chunk_overlap
            )
            print(f"✓ Chunking parameters updated: size={self.chunk_size}, overlap={self.chunk_overlap}")
            print(f"✓ Word-count-based chunking: {word_chunk_size} words, ratio: {word_count_ratio}")
        
        print("ℹ Existing chunks in Chroma are unchanged; call rebuild_index() to re-chunk everything.")
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """Get current chunking configuration"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "llamaindex_defaults": {
                "chunk_size": 1024,
                "chunk_overlap": 20
            },
            "current_vs_defaults": {
                "chunk_size": f"{self.chunk_size} (default: 1024)",
                "chunk_overlap": f"{self.chunk_overlap} (default: 20)"
            }
        }
    
    def rebuild_index(self, folder_path: str = None, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Clear the Chroma collection and rebuild the index with current chunking params.
        Useful after update_chunking_params() to re-chunk everything deterministically.
        """
        print("🔄 Rebuilding index from scratch...")
        self.clear_index()
        return self.build_index_from_folder(folder_path=folder_path, file_extensions=file_extensions)
