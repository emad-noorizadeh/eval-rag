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
RAG Testing Interface Backend
Author: Emad Noorizadeh
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

# Disable all telemetry and external logging
from disable_telemetry import (
    disable_all_telemetry, 
    configure_local_logging_only, 
    disable_network_telemetry,
    disable_all_external_connections,
    create_network_monitor
)
disable_all_telemetry()
configure_local_logging_only()
disable_network_telemetry()
disable_all_external_connections()
create_network_monitor()

# Enable URL guardrail to block all external requests
from url_guardrail import block_external_requests, create_network_monitor as create_url_monitor
block_external_requests()
create_url_monitor()

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import uvicorn
import os
from datetime import datetime

# Import our modular components
from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from chat_agent import ChatAgent, ChatConfig, RetrievalMethod, RoutingStrategy
from session_manager import session_manager
from config import config, get_config

app = FastAPI(title="RAG API", version="1.0.0", description="RAG Testing Interface by Emad Noorizadeh")

# Initialize components
print("Initializing RAG system components...")
print("Loading configuration...")
config.print_config()

model_manager = ModelManager()

# Use basic IndexBuilder for semantic retrieval
from index_builder import IndexBuilder
index_builder = IndexBuilder(model_manager)

rag = RAG(model_manager, index_builder)

# Initialize unified chat agent with configuration
chat_config = ChatConfig(
    retrieval_method=RetrievalMethod(get_config("chat_agent", "retrieval_method")),
    routing_strategy=RoutingStrategy(get_config("chat_agent", "routing_strategy")),
    retrieval_top_k=get_config("chat_agent", "retrieval_top_k"),
    similarity_threshold=get_config("chat_agent", "similarity_threshold"),
    max_clarify=get_config("chat_agent", "max_clarify"),
    reclarify_threshold=get_config("chat_agent", "reclarify_threshold"),
    window_k=get_config("chat_agent", "window_k")
)

chat_agent = ChatAgent(model_manager, index_builder, session_manager, chat_config)

# Note: ChatAgent is now created per-session in session_manager
print("✓ RAG system initialized successfully")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config("api", "cors_origins"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Document(BaseModel):
    text: str
    metadata: Optional[dict] = None

class Query(BaseModel):
    query: str
    n_results: int = 5

class QueryResponse(BaseModel):
    results: List[dict]
    query: str

class ChatMessage(BaseModel):
    text: str
    isUser: bool
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage]
    session_id: Optional[str] = None

class SessionCreateRequest(BaseModel):
    data_folder: Optional[str] = None
    collection_name: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    remaining_time: int
    timeout_minutes: int

class RAGMetrics(BaseModel):
    # LangGraph agent metrics
    clarify_count: int = 0
    threshold: float = 0.45
    top_k: int = 3
    max_clarify: int = 2
    conversation_length: int = 0
    
    # Optional fields for backward compatibility
    chunks_retrieved: List[Dict[str, Any]] = []
    context_utilization: float = 0.0
    confidence: Union[float, str] = 0.0
    faithfulness_score: float = 0.0
    completeness_score: float = 0.0
    missing_information: List[str] = []
    answer_type: str = "unknown"
    abstained: bool = False
    reasoning_notes: str = ""
    
    # Additional fields for enhanced debug panel
    ingest_metrics: Dict[str, Any] = {}
    retrieve_metrics: Dict[str, Any] = {}
    route_metrics: Dict[str, Any] = {}
    rag_metrics: Dict[str, Any] = {}
    clarify_metrics: Dict[str, Any] = {}
    
    # Node-specific fields
    final_node: str = "rag"
    rephrased_input: str = ""
    clarification_question: str = ""
    is_clarification_response: bool = False
    route_decision: str = "unknown"

class RAGAnalysis(BaseModel):
    answer: str = ""
    confidence: Union[float, str] = "Unknown"
    faithfulness_score: float = 0.0
    completeness_score: float = 0.0
    answer_type: str = "unknown"
    abstained: bool = False
    reasoning_notes: str = ""
    evidence: List[str] = []
    context_utilization: List[str] = []
    missing_information: List[str] = []

class AgentMetrics(BaseModel):
    clarify_count: int = 0
    threshold: float = 0.45
    top_k: int = 3
    max_clarify: int = 2
    conversation_length: int = 0
    is_clarification_response: bool = False
    route_decision: str = "unknown"

class DebugMetrics(BaseModel):
    ingest_metrics: Dict[str, Any] = {}
    retrieve_metrics: Dict[str, Any] = {}
    route_metrics: Dict[str, Any] = {}
    rag_metrics: Dict[str, Any] = {}
    clarify_metrics: Dict[str, Any] = {}

class ComprehensiveChatResponse(BaseModel):
    # Core response fields
    response: str
    sources: List[Dict[str, Any]]
    session_id: str
    conversation_history: List[Dict[str, Any]]
    
    # Node-specific fields
    final_node: str = "rag"
    rephrased_input: str = ""
    clarification_question: str = ""
    
    # Complete RAG analysis
    rag_analysis: RAGAnalysis
    
    # Chunks and retrieval data
    chunks_retrieved: List[Dict[str, Any]] = []
    
    # Agent flow metrics
    agent_metrics: AgentMetrics
    
    # Detailed node metrics for debug panel
    debug_metrics: DebugMetrics
    
    # Legacy format for backward compatibility
    metrics: RAGMetrics

class ChatResponse(BaseModel):
    response: str
    sources: List[dict]
    metrics: RAGMetrics

class ChunkingConfig(BaseModel):
    chunk_size: int
    chunk_overlap: int


@app.get("/")
async def root():
    return {"message": "RAG API is running"}

# Session Management Endpoints
@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest = None):
    """Create a new chat session"""
    try:
        session_id = session_manager.create_session()
        
        session_info = session_manager.get_session_info(session_id)
        
        return SessionResponse(
            session_id=session_id,
            created_at=session_info["created_at"],
            remaining_time=session_info["remaining_time"],
            timeout_minutes=session_info["timeout_minutes"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        session_info = session_manager.get_session_info(session_id)
        if session_info is None:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        return session_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/{session_id}/extend")
async def extend_session(session_id: str):
    """Extend session by updating last activity"""
    try:
        success = session_manager.extend_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        session_info = session_manager.get_session_info(session_id)
        return {
            "message": "Session extended successfully",
            "remaining_time": session_info["remaining_time"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """End a session"""
    try:
        success = session_manager.end_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session ended successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def get_active_sessions():
    """Get all active sessions (admin endpoint)"""
    try:
        sessions = session_manager.get_active_sessions()
        return {
            "active_sessions": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build-index")
async def build_index(folder_path: str = None):
    """Build index from text files in a folder (uses config default if no path provided)"""
    try:
        result = index_builder.build_index_from_folder(folder_path)
        return {
            "message": "Index built successfully",
            "stats": result,
            "folder_used": folder_path or get_config("data", "folder_path")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents", response_model=dict)
async def add_document(document: Document):
    """Add a document to the vector database"""
    try:
        # Use index builder to add document
        doc_id = index_builder.add_document(document.text, document.metadata)
        
        return {"message": "Document added successfully", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/file", response_model=dict)
async def add_document_from_file(file: UploadFile = File(...), filename: str = Form(None)):
    """Add a document from uploaded file to the vector database"""
    try:
        # Check file size
        max_size = get_config("data", "max_file_size_mb") * 1024 * 1024
        if file.size and file.size > max_size:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {get_config('data', 'max_file_size_mb')}MB")
        
        # Read file content
        content = await file.read()
        
        # Parse content based on file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension == '.pdf':
            # Parse PDF using PyMuPDF
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=content, filetype="pdf")
                text_parts = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_parts.append(page.get_text())
                text = "\n\n".join(text_parts)
                doc.close()
            except ImportError:
                raise HTTPException(status_code=500, detail="PDF parsing not available. Please install PyMuPDF: pip install PyMuPDF")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error parsing PDF: {str(e)}")
        else:
            # For text files (.txt, .md), decode as UTF-8
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text or PDF")
        
        # Create metadata
        display_filename = filename.strip() if filename and filename.strip() else file.filename
        metadata = {
            "filename": file.filename,
            "file_name": display_filename,  # Use custom filename if provided
            "file_size": len(content),
            "content_type": file.content_type,
            "uploaded_at": datetime.now().isoformat(),
            "page_count": len(text.split('\n\n')) if file_extension == '.pdf' else 1
        }
        
        # Save parsed text to data folder
        data_folder = get_config("data", "folder_path")
        os.makedirs(data_folder, exist_ok=True)
        
        # Create filename for saved text
        if filename and filename.strip():
            # Use custom filename provided by user
            base_name = filename.strip()
            saved_filename = f"{base_name}.txt"
        else:
            # Use original filename as fallback
            base_name = os.path.splitext(file.filename)[0]
            saved_filename = f"{base_name}_parsed.txt"
        
        saved_file_path = os.path.join(data_folder, saved_filename)
        
        # Save the parsed text
        with open(saved_file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Add file path to metadata
        metadata["saved_file_path"] = saved_file_path
        metadata["saved_filename"] = saved_filename
        
        # Add to index
        doc_id = index_builder.add_document(text, metadata)
        
        return {
            "message": "File parsed, saved to data folder, and added to index successfully", 
            "id": doc_id,
            "filename": file.filename,
            "saved_filename": saved_filename,
            "size": len(content),
            "text_length": len(text),
            "page_count": metadata["page_count"]
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be text-based (UTF-8 encoded)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(query: Query):
    """Query the vector database for similar documents using semantic retrieval"""
    try:
        # Use RAG system which properly uses RetrievalService with debugging
        results = rag.retrieve_documents(query.query, query.n_results)
        
        # Format results to match expected frontend format
        formatted_results = []
        for i, result in enumerate(results):
            # Get node ID for compatibility
            node_id = result.get('id', f"chunk_{i}")
            
            formatted_results.append({
                'id': node_id,
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'score': result.get('score', 0.0),
                'similarity_score': result.get('similarity_score', result.get('score', 0.0))
            })
        
        return QueryResponse(results=formatted_results, query=query.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=dict)
async def get_all_documents():
    """Get all documents from the database"""
    try:
        info = index_builder.get_collection_info()
        return {
            "count": info['total_documents'],
            "collection_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-files")
async def get_data_files():
    """Get list of files in the data folder"""
    try:
        data_folder = get_config("data", "folder_path")
        
        if not os.path.exists(data_folder):
            return {
                "files": [],
                "folder_path": data_folder,
                "error": "Data folder does not exist"
            }
        
        files = []
        for filename in os.listdir(data_folder):
            file_path = os.path.join(data_folder, filename)
            if os.path.isfile(file_path):
                # Get file stats
                stat = os.stat(file_path)
                file_info = {
                    "name": filename,
                    "path": file_path,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": os.path.splitext(filename)[1].lower()
                }
                files.append(file_info)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "files": files,
            "folder_path": data_folder,
            "total_files": len(files),
            "total_size_mb": round(sum(f["size_mb"] for f in files), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-files/{filename}")
async def get_file_content(filename: str):
    """Get content of a specific file from the data folder"""
    try:
        data_folder = get_config("data", "folder_path")
        file_path = os.path.join(data_folder, filename)
        
        # Security check - ensure file is within data folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(data_folder)):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get file stats
        stat = os.stat(file_path)
        
        return {
            "filename": filename,
            "content": content,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": os.path.splitext(filename)[1].lower(),
            "line_count": len(content.splitlines()),
            "word_count": len(content.split())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document from both index and data folder"""
    try:
        # First, get document metadata to find associated files
        try:
            document_info = index_builder.db_config.get_document(document_id)
            if not document_info:
                raise HTTPException(status_code=404, detail="Document not found")
        except Exception:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from index
        index_builder.delete_document(document_id)
        
        # Delete associated files from data folder
        deleted_files = []
        data_folder = get_config("data", "folder_path")
        
        # Check if there's a saved file path in metadata
        if document_info and "saved_file_path" in document_info:
            saved_file_path = document_info["saved_file_path"]
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
                deleted_files.append(os.path.basename(saved_file_path))
        
        # Also check for original filename patterns
        if document_info and "filename" in document_info:
            original_filename = document_info["filename"]
            base_name = os.path.splitext(original_filename)[0]
            
            # Look for parsed files with the same base name
            for filename in os.listdir(data_folder):
                if filename.startswith(base_name) and filename.endswith('_parsed.txt'):
                    file_path = os.path.join(data_folder, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files.append(filename)
        
        return {
            "message": f"Document {document_id} deleted successfully",
            "deleted_files": deleted_files,
            "files_deleted_count": len(deleted_files)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/file/{filename}")
async def delete_document_by_filename(filename: str):
    """Delete a document by filename from both index and data folder"""
    try:
        # Find document by filename in the index
        data_folder = get_config("data", "folder_path")
        file_path = os.path.join(data_folder, filename)
        
        # Security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(data_folder)):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Get document metadata to find matching documents
        all_metadata = index_builder.metadata_storage.get_all_documents()
        deleted_docs = []
        deleted_files = []
        
        # Search through document metadata to find matches
        for doc_filename, doc_metadata in all_metadata.get("documents", {}).items():
            if doc_filename == filename:
                # Delete from index using the filename as doc_id
                index_builder.delete_document(doc_filename)
                deleted_docs.append(doc_filename)
        
        # Also delete the original file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_files.append(filename)
        
        if not deleted_docs:
            raise HTTPException(status_code=404, detail="Document not found in index")
        
        return {
            "message": f"Document '{filename}' deleted successfully",
            "deleted_document_ids": deleted_docs,
            "deleted_files": deleted_files,
            "documents_deleted_count": len(deleted_docs),
            "files_deleted_count": len(deleted_files)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def clear_all_documents():
    """Clear all documents from both database and data folder"""
    try:
        # Get all files in data folder before clearing
        data_folder = get_config("data", "folder_path")
        files_before = []
        if os.path.exists(data_folder):
            files_before = os.listdir(data_folder)
        
        # Clear index
        index_builder.clear_index()
        
        # Clear data folder
        deleted_files = []
        if os.path.exists(data_folder):
            for filename in files_before:
                file_path = os.path.join(data_folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_files.append(filename)
        
        return {
            "message": "All documents cleared successfully",
            "deleted_files": deleted_files,
            "files_deleted_count": len(deleted_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chunking-config")
async def get_chunking_config():
    """Get current chunking configuration"""
    try:
        config = index_builder.get_chunking_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chunking-config")
async def update_chunking_config(config: ChunkingConfig):
    """Update chunking configuration"""
    try:
        index_builder.update_chunking_params(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        return {
            "message": "Chunking configuration updated successfully",
            "config": index_builder.get_chunking_config()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build-index")
async def build_index():
    """Build basic index for semantic retrieval"""
    try:
        result = index_builder.build_index_from_folder()
        return {
            "message": "Index built successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced metadata endpoints removed - using basic index builder

@app.get("/documents/{filename}/metadata")
async def get_document_metadata(filename: str):
    """Get enhanced metadata for a specific document by filename"""
    try:
        # Get metadata from storage
        metadata = index_builder.metadata_storage.get_document_metadata(filename)
        
        if metadata:
            # Convert chunk data to match frontend expectations
            chunks = []
            for chunk in metadata.get("chunks", []):
                chunks.append({
                    "chunk_id": chunk.get("chunk_id", ""),
                    "token_count": chunk.get("token_count", 0),
                    "first_line": chunk.get("first_line", "")
                })
            
            return {
                "document": {
                    "doc_id": metadata.get("doc_id", ""),
                    "title": metadata.get("title", filename),
                    "doc_type": metadata.get("doc_type", "document"),
                    "domain": metadata.get("domain", "unknown"),
                    "language": metadata.get("language", "en"),
                    "url": metadata.get("url"),
                    "published_at": metadata.get("published_at"),
                    "updated_at": metadata.get("updated_at"),
                    "effective_date": metadata.get("effective_date"),
                    "expires_at": metadata.get("expires_at"),
                    "geo_scope": metadata.get("geo_scope", "unknown"),
                    "currency": metadata.get("currency", "USD"),
                    "product_entities": metadata.get("product_entities", []),
                    "categories": metadata.get("categories", []),
                    "file_path": filename,
                    "file_type": filename.split('.')[-1] if '.' in filename else "unknown",
                    "file_name": filename,
                    "created_at": metadata.get("added_at", datetime.now().isoformat()),
                    "updated_at_processing": metadata.get("added_at", datetime.now().isoformat())
                },
                "chunks": chunks,
                "chunk_count": len(chunks),
                "message": "Enhanced metadata from extraction"
            }
        else:
            # Fallback to basic metadata if not found
            return {
                "document": {
                    "file_name": filename,
                    "file_type": filename.split('.')[-1] if '.' in filename else "unknown",
                    "status": "Document not found in metadata",
                    "title": filename,
                    "doc_type": "document",
                    "domain": "unknown",
                    "language": "en",
                    "url": None,
                    "geo_scope": "unknown",
                    "currency": "USD",
                    "published_at": None,
                    "updated_at": None,
                    "effective_date": None,
                    "expires_at": None,
                    "product_entities": [],
                    "categories": [],
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "extraction_method": "not_found"
                },
                "chunks": [],
                "chunk_count": 0,
                "message": "Document not found in metadata storage"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/metadata")
async def get_all_documents_metadata():
    """Get metadata for all documents"""
    try:
        all_metadata = index_builder.metadata_storage.get_all_documents()
        return all_metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collection/info")
async def get_collection_info():
    """Get collection/index information"""
    try:
        collection_info = index_builder.get_collection_info()
        metadata = index_builder.metadata_storage.get_all_documents()
        
        # Add collection info from metadata if available
        if "collection_info" in metadata:
            collection_info.update(metadata["collection_info"])
        
        return collection_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{filename}/content")
async def get_document_content(filename: str):
    """Get the raw content of a specific document"""
    try:
        data_folder = get_config("data", "folder_path")
        file_path = os.path.join(data_folder, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": filename,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """Unified chat endpoint with configurable retrieval and routing"""
    try:
        # Get conversation history from session
        session_data = session_manager.get_session(request.session_id)
        if session_data is None:
            # Create new session if it doesn't exist
            request.session_id = session_manager.create_session()
            session_data = session_manager.get_session(request.session_id)
        
        # Convert conversation history to the format expected by UnifiedChatAgent
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_history.append({
                    "role": "user" if msg.isUser else "assistant",
                    "content": msg.text,
                    "timestamp": msg.timestamp
                })
        
        # Process the chat using chat agent
        response = chat_agent.chat(
            message=request.message,
            session_id=request.session_id,
            conversation_history=conversation_history
        )
        
        return response
        
    except Exception as e:
        print(f"Error in chat-unified: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat-config")
async def get_chat_config():
    """Get current chat agent configuration"""
    try:
        config_data = chat_agent.get_config()
        
        # Get database configuration from index builder
        collection_info = index_builder.get_collection_info()
        
        return {
            "retrieval_method": config_data.retrieval_method.value,
            "routing_strategy": config_data.routing_strategy.value,
            "retrieval_top_k": config_data.retrieval_top_k,
            "similarity_threshold": config_data.similarity_threshold,
            "max_clarify": config_data.max_clarify,
            "reclarify_threshold": config_data.reclarify_threshold,
            "window_k": config_data.window_k,
            "available_retrieval_methods": chat_agent.get_available_retrieval_methods(),
            "available_routing_strategies": chat_agent.get_available_routing_strategies(),
            "db_path": collection_info.get("db_path", "Unknown"),
            "collection_name": collection_info.get("collection_name", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat-config")
async def update_chat_config(config_update: Dict[str, Any]):
    """Update chat agent configuration"""
    try:
        # Create new config with updated values
        current_config = chat_agent.get_config()
        
        # Update config fields
        if "retrieval_method" in config_update:
            current_config.retrieval_method = RetrievalMethod(config_update["retrieval_method"])
        if "routing_strategy" in config_update:
            current_config.routing_strategy = RoutingStrategy(config_update["routing_strategy"])
        if "retrieval_top_k" in config_update:
            current_config.retrieval_top_k = config_update["retrieval_top_k"]
        if "similarity_threshold" in config_update:
            current_config.similarity_threshold = config_update["similarity_threshold"]
        if "max_clarify" in config_update:
            current_config.max_clarify = config_update["max_clarify"]
        if "reclarify_threshold" in config_update:
            current_config.reclarify_threshold = config_update["reclarify_threshold"]
        if "window_k" in config_update:
            current_config.window_k = config_update["window_k"]
        
        # Update the chat agent
        chat_agent.update_config(current_config)
        
        return {"message": "Configuration updated successfully", "config": config_update}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# Index Management API
# =========================

@app.get("/index/status")
async def get_index_status():
    """Get current index status"""
    try:
        # Get basic index info from IndexBuilder
        collection_info = index_builder.get_collection_info()
        return {
            "exists": collection_info.get("total_documents", 0) > 0,
            "capabilities": ["semantic"],  # Only semantic retrieval supported
            "retrieval_support": {"semantic": True},
            "last_updated": None,  # Not tracked in simple version
            "total_documents": collection_info.get("total_documents", 0),
            "total_chunks": collection_info.get("total_chunks", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/index/compatibility/{retrieval_method}")
async def check_index_compatibility(retrieval_method: str):
    """Check if current index supports the specified retrieval method"""
    try:
        # Only semantic retrieval is supported
        if retrieval_method == "semantic":
            return {
                "is_compatible": True,
                "missing_capabilities": [],
                "can_enhance": False,
                "requires_rebuild": False,
                "message": "Semantic retrieval is fully supported"
            }
        else:
            return {
                "is_compatible": False,
                "missing_capabilities": [f"{retrieval_method} retrieval not supported"],
                "can_enhance": False,
                "requires_rebuild": False,
                "message": f"Only semantic retrieval is supported, not {retrieval_method}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/setup")
async def setup_index(request: Dict[str, Any]):
    """Setup index for semantic retrieval"""
    try:
        retrieval_method = request.get("retrieval_method", "semantic")
        overwrite = request.get("overwrite", False)
        source_folder = request.get("source_folder", "data")
        
        # Only support semantic retrieval
        if retrieval_method != "semantic":
            raise HTTPException(status_code=400, detail=f"Only semantic retrieval is supported, not {retrieval_method}")
        
        # Clear existing index if overwrite requested
        if overwrite:
            index_builder.clear_index()
        
        # Build index from source folder
        result = index_builder.build_index_from_folder(source_folder)
        
        return {
            "success": True,
            "message": "Index built successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/index/compatibility-matrix")
async def get_compatibility_matrix():
    """Get compatibility matrix for all retrieval methods"""
    try:
        # Only semantic retrieval is supported
        return {
            "semantic": {
                "supported": True,
                "capabilities": ["vector_similarity"],
                "description": "Semantic retrieval using vector embeddings"
            },
            "hybrid": {
                "supported": False,
                "capabilities": [],
                "description": "Hybrid retrieval not supported in simplified system"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/add-documents")
async def add_documents_to_index(request: Dict[str, Any]):
    """Add documents to existing index"""
    try:
        documents = request.get("documents", [])
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        # Add each document to the index
        added_count = 0
        for doc_text in documents:
            if doc_text.strip():  # Only add non-empty documents
                index_builder.add_document(doc_text)
                added_count += 1
        
        return {"success": True, "message": f"Added {added_count} documents to index"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/index")
async def delete_index(request: Dict[str, Any] = None):
    """Delete the current index"""
    try:
        from scripts.delete_index import delete_index_api
        
        collection_name = None
        if request:
            collection_name = request.get("collection_name")
        
        result = delete_index_api(collection_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=get_config("api", "host"), 
        port=get_config("api", "port")
    )
