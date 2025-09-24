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
Debug Retrieval Issues
Author: Emad Noorizadeh

Debug script to test retrieval step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder
from retrieval_service import RetrievalService, RetrievalConfig, RetrievalMethod

def debug_retrieval():
    """Debug retrieval step by step"""
    print("🔍 Debugging Retrieval System")
    print("=" * 50)
    
    # Initialize components
    print("1. Initializing components...")
    model_manager = ModelManager()
    index_builder = IndexBuilder(model_manager)
    retrieval_service = RetrievalService(model_manager, index_builder)
    
    # Check if index is built
    print("\n2. Checking index...")
    try:
        collection_info = index_builder.get_collection_info()
        print(f"   Collection: {collection_info.get('collection_name', 'Unknown')}")
        print(f"   Total docs: {collection_info.get('total_documents', 0)}")
    except Exception as e:
        print(f"   Error getting collection info: {e}")
        return
    
    # Test ChromaDB adapter directly
    print("\n3. Testing ChromaDB adapter...")
    try:
        chroma_adapter = retrieval_service._get_chroma_adapter()
        print("   ChromaDB adapter created successfully")
        
        # Test search
        results = chroma_adapter.search("Bank of America Preferred Rewards", top_k=5)
        print(f"   Search results: {len(results)} chunks")
        for i, (chunk_id, score) in enumerate(results[:3]):
            print(f"     {i+1}. {chunk_id}: {score:.4f}")
    except Exception as e:
        print(f"   Error with ChromaDB adapter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test retrieval service
    print("\n4. Testing retrieval service...")
    try:
        config = RetrievalConfig(
            method=RetrievalMethod.SEMANTIC,
            top_k=5,
            similarity_threshold=0.45
        )
        
        result = retrieval_service.retrieve("Bank of America Preferred Rewards", config)
        print(f"   Retrieval result: {len(result.chunks)} chunks")
        print(f"   Method: {result.method}")
        
        for i, chunk in enumerate(result.chunks[:3]):
            print(f"     {i+1}. {chunk['chunk_id']}: {chunk['score']:.4f}")
            print(f"        Text: {chunk['text'][:100]}...")
    except Exception as e:
        print(f"   Error with retrieval service: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test RAG retrieve_documents
    print("\n5. Testing RAG retrieve_documents...")
    try:
        from rag import RAG
        rag = RAG(model_manager, index_builder, RetrievalMethod.SEMANTIC)
        
        documents = rag.retrieve_documents("Bank of America Preferred Rewards", n_results=5)
        print(f"   RAG documents: {len(documents)} chunks")
        
        for i, doc in enumerate(documents[:3]):
            print(f"     {i+1}. {doc['chunk_id']}: {doc['score']:.4f}")
            print(f"        Text: {doc['text'][:100]}...")
    except Exception as e:
        print(f"   Error with RAG: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ Retrieval debugging complete!")

if __name__ == "__main__":
    debug_retrieval()
