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
Test RAG directly with a good question
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_rag_direct():
    """Test RAG directly with a good question"""
    print("🔍 Testing RAG Direct")
    print("=" * 40)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Test query
        query = "What are the different tier levels in the Bank of America Preferred Rewards program and what are their requirements?"
        print(f"\n🔍 Query: '{query}'")
        print("-" * 50)
        
        # Retrieve documents first
        nodes = rag.retrieve_documents(query, n_results=3)
        print(f"Retrieved {len(nodes)} chunks")
        
        for i, node in enumerate(nodes):
            score = node.get("similarity_score", 0.0)
            print(f"  Chunk {i+1}: similarity={score:.4f}")
        
        # Test RAG generation
        print("\n🔍 Testing RAG generation...")
        response = rag.generate_response(query, nodes)
        
        print(f"\n📋 Full Response:")
        print(f"Answer: {response.get('answer', 'N/A')}")
        print(f"Answer Type: {response.get('metrics', {}).get('answer_type', 'N/A')}")
        print(f"Confidence: {response.get('metrics', {}).get('confidence', 'N/A')}")
        print(f"Clarification Question: {response.get('metrics', {}).get('clarification_question', 'N/A')}")
        print(f"Abstained: {response.get('metrics', {}).get('abstained', 'N/A')}")
        print(f"Reasoning: {response.get('metrics', {}).get('reasoning_notes', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_direct()
