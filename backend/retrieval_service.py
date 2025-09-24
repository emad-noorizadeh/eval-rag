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
Simplified Retrieval Service - Semantic Only
Author: Emad Noorizadeh

Provides semantic retrieval only using basic index builder.
"""

from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from index_builder import IndexBuilder
from model_manager import ModelManager


class RetrievalMethod(Enum):
    """Available retrieval methods"""
    SEMANTIC = "semantic"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval service"""
    method: RetrievalMethod = RetrievalMethod.SEMANTIC
    top_k: int = 5
    similarity_threshold: float = 0.45


@dataclass
class RetrievalResult:
    """Result from retrieval service"""
    chunks: List[Dict[str, Any]]
    method: str
    total_chunks: int
    metadata: Dict[str, Any]


class RetrievalService:
    """Simplified retrieval service for semantic search only"""
    
    def __init__(self, model_manager: ModelManager, index_builder: IndexBuilder):
        self.model_manager = model_manager
        self.index_builder = index_builder
    
    def retrieve(self, query: str, config: RetrievalConfig) -> RetrievalResult:
        """Retrieve documents using semantic similarity"""
        if config.method == RetrievalMethod.SEMANTIC:
            return self._retrieve_semantic(query, config)
        else:
            raise ValueError(f"Unsupported retrieval method: {config.method}")
    
    def _retrieve_semantic(self, query: str, config: RetrievalConfig) -> RetrievalResult:
        """Retrieve using semantic similarity with LlamaIndex retriever"""
        # Index is already initialized in IndexBuilder.__init__
        index = self.index_builder.index
        
        if not index:
            print("Warning: Index not initialized for semantic search")
            return RetrievalResult(
                chunks=[],
                method="semantic",
                total_chunks=0,
                metadata={"error": "Index not initialized"}
            )
        
        # Use LlamaIndex retriever directly (this gives proper similarity scores)
        retriever = index.as_retriever(similarity_top_k=config.top_k)
        retrieved_nodes = retriever.retrieve(query)
        
        # Convert to standardized format
        chunks = []
        for node in retrieved_nodes:
            chunk = {
                "chunk_id": node.node_id,
                "doc_id": node.metadata.get("doc_id", "") if node.metadata else "",
                "text": node.text,
                "score": float(node.score),  # This is the proper similarity score
                "metadata": node.metadata or {}
            }
            chunks.append(chunk)
        
        return RetrievalResult(
            chunks=chunks,
            method="semantic",
            total_chunks=len(chunks),
            metadata={
                "similarity_threshold": config.similarity_threshold,
                "top_k": config.top_k
            }
        )
    
    def get_method_info(self, method: RetrievalMethod) -> Dict[str, Any]:
        """Get information about a retrieval method"""
        info = {
            "method": method.value,
            "capabilities": []
        }
        
        if method == RetrievalMethod.SEMANTIC:
            info["description"] = "Semantic retrieval using embeddings"
            info["capabilities"] = [
                "Vector similarity", "Semantic search", "Embedding-based"
            ]
        
        return info

    def retrieve_semantic(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using semantic similarity only"""
        # Index is already initialized in IndexBuilder.__init__
        retriever = self.index_builder.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        out = []
        for n in nodes:
            out.append({
                "chunk_id": getattr(n, "node_id", getattr(n, "id_", "")),
                "doc_id": (n.metadata or {}).get("doc_id", ""),
                "text": n.text,
                "score": float(getattr(n, "score", 0.0)),
                "metadata": n.metadata or {}
            })
        return out

    def retrieve_union(self, q1: str, q2: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using union of two queries, keeping max score per chunk"""
        a = self.retrieve_semantic(q1, top_k)
        b = self.retrieve_semantic(q2, top_k) if q2 else []
        # Merge by chunk_id, keep max score
        by_id = {}
        for r in (a + b):
            cid = r["chunk_id"]
            if cid not in by_id or r["score"] > by_id[cid]["score"]:
                by_id[cid] = r
        # Return top_k by score
        return sorted(by_id.values(), key=lambda x: x["score"], reverse=True)[:top_k]
