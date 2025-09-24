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
Test RAG system with multiple questions
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_rag_questions():
    """Test RAG system with multiple questions"""
    print("=== Testing RAG System with Multiple Questions ===\n")
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager, collection_name="rag_multi_test")
        
        # Build index
        data_folder = "./data"
        print(f"📚 Building index from: {data_folder}")
        result = index_builder.build_index_from_folder(data_folder)
        if 'processed_files' in result and result['processed_files'] > 0:
            print(f"✅ Index built: {result['processed_files']} files, {result['total_chunks']} chunks")
        else:
            print("❌ Index build failed")
            return
        
        # Initialize RAG system
        rag = RAG(model_manager, index_builder)
        
        # Test questions
        questions = [
            "what is gold tier",
            "what are the benefits of Preferred Rewards",
            "how much do I need to maintain for Platinum tier",
            "what are the account fees",
            "how do I enroll in Preferred Rewards"
        ]
        
        for i, query in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"Question {i}: {query}")
            print('='*60)
            
            # Get RAG response
            response = rag.query(query, n_results=2)
            
            print(f"📝 Answer:")
            print(f"{response.get('response', 'No response')}")
            
            print(f"\n📚 Sources ({len(response.get('sources', []))}):")
            for j, source in enumerate(response.get('sources', []), 1):
                print(f"  {j}. Similarity: {source.get('similarity', 'N/A'):.3f}")
                print(f"     Text: {source.get('text', 'No text')[:100]}...")
        
        print(f"\n✅ All RAG tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_questions()
