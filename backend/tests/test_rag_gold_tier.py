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
Test RAG system with "what is gold tier" question
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime

from ..model_manager import ModelManager
from ..index_builder import IndexBuilder
from ..rag import RAG

def test_rag_gold_tier():
    """Test RAG system with gold tier question"""
    print("=== Testing RAG System with 'What is Gold Tier' ===\n")
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager, collection_name="rag_test")
        
        # Build index if needed
        data_folder = "./data"
        if os.path.exists(data_folder):
            print(f"📚 Building index from: {data_folder}")
            result = index_builder.build_index_from_folder(data_folder)
            if 'processed_files' in result and result['processed_files'] > 0:
                print(f"✅ Index built: {result['processed_files']} files, {result['total_chunks']} chunks")
            else:
                print("❌ Index build failed")
                return
        else:
            print(f"❌ Data folder not found: {data_folder}")
            return
        
        # Initialize RAG system
        print("\n🤖 Initializing RAG system...")
        rag = RAG(model_manager, index_builder)
        
        # Test query
        query = "what is gold tier"
        print(f"\n🔍 Query: '{query}'")
        print("-" * 50)
        
        # Get RAG response
        response = rag.query(query, n_results=3)
        
        print(f"📝 Response:")
        print(f"Answer: {response.get('response', 'No response')}")
        
        print(f"\n📊 Metrics:")
        print(f"  - Retrieved documents: {len(response.get('sources', []))}")
        print(f"  - Processing time: {response.get('processing_time', 'N/A')}")
        print(f"  - Model used: {response.get('model_used', 'N/A')}")
        
        print(f"\n📚 Sources:")
        for i, source in enumerate(response.get('sources', []), 1):
            print(f"  {i}. Similarity: {source.get('similarity', 'N/A'):.3f}")
            print(f"     Text: {source.get('text', 'No text')[:150]}...")
            print(f"     Source: {source.get('metadata', {}).get('source', 'Unknown')}")
        
        print(f"\n✅ RAG test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_gold_tier()
