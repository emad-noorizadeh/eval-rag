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
Test the new structured RAG system with JSON response + metrics
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_new_rag_system():
    """Test the new structured RAG system"""
    print("=== Testing New Structured RAG System ===\n")
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager, collection_name="new_rag_test")
        
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
        print("\n🤖 Initializing new RAG system...")
        rag = RAG(model_manager, index_builder)
        
        # Test queries
        test_queries = [
            "what is gold tier",
            "what are the benefits of Preferred Rewards",
            "how much do I need for Platinum tier"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"Query {i}: {query}")
            print('='*80)
            
            # Get RAG response
            response = rag.query(query, n_results=3)
            
            print(f"📝 Answer:")
            print(f"{response.get('response', 'No response')}")
            
            print(f"\n📊 Metrics:")
            metrics = response.get('metrics', {})
            print(f"  - Confidence: {metrics.get('confidence', 'N/A')}")
            print(f"  - Faithfulness Score: {metrics.get('faithfulness_score', 'N/A')}")
            print(f"  - Completeness Score: {metrics.get('completeness_score', 'N/A')}")
            print(f"  - Answer Type: {metrics.get('answer_type', 'N/A')}")
            print(f"  - Abstained: {metrics.get('abstained', 'N/A')}")
            print(f"  - Missing: {metrics.get('missing', 'N/A')}")
            print(f"  - Evidence: {metrics.get('evidence', [])}")
            print(f"  - Context Utilization: {len(metrics.get('context_utilization', []))} chunks")
            print(f"  - Reasoning: {metrics.get('reasoning_notes', 'N/A')}")
            
            print(f"\n📚 Sources ({len(response.get('sources', []))}):")
            for j, source in enumerate(response.get('sources', []), 1):
                print(f"  {j}. Similarity: {source.get('similarity', 'N/A'):.3f}")
                print(f"     Text: {source.get('text', 'No text')[:100]}...")
        
        print(f"\n✅ New RAG system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_rag_system()
