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
Test RAG system with clarification questions for vague queries
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_rag_clarification():
    """Test RAG system with clarification questions for vague queries"""
    print("=== Testing RAG Clarification Questions ===\n")
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager, collection_name="rag_clarification_test")
        
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
        
        # Test queries - including vague ones that should trigger clarification
        test_queries = [
            "gold",  # Vague - should ask for clarification
            "fees",  # Vague - should ask for clarification
            "benefits",  # Vague - should ask for clarification
            "what is gold tier",  # Clear - should work
            "what are the account fees for checking"  # Clear - should work
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"Query {i}: '{query}'")
            print('='*80)
            
            # Get RAG response
            response = rag.query(query, n_results=3)
            
            print(f"📝 Response:")
            print(f"{response.get('response', 'No response')}")
            
            # Check for clarification question
            clarification = response.get('clarification_question', '')
            if clarification:
                print(f"\n❓ Clarification Question:")
                print(f"{clarification}")
            
            print(f"\n📊 Metrics:")
            metrics = response.get('metrics', {})
            print(f"  - Confidence: {metrics.get('confidence', 'N/A')}")
            print(f"  - Answer Type: {metrics.get('answer_type', 'N/A')}")
            print(f"  - Abstained: {metrics.get('abstained', 'N/A')}")
            print(f"  - Evidence: {metrics.get('evidence', [])}")
            print(f"  - Context Utilization: {len(metrics.get('context_utilization', []))} chunks")
            print(f"  - Reasoning: {metrics.get('reasoning_notes', 'N/A')}")
            
            # Show sources if any
            sources = response.get('sources', [])
            if sources:
                print(f"\n📚 Sources ({len(sources)}):")
                for j, source in enumerate(sources, 1):
                    print(f"  {j}. Similarity: {source.get('similarity', 'N/A'):.3f}")
                    print(f"     Text: {source.get('text', 'No text')[:100]}...")
        
        print(f"\n✅ RAG clarification test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_clarification()
