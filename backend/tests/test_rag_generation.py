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
Test RAG generation directly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_rag_generation():
    """Test RAG generation directly"""
    print("🔍 Testing RAG Generation")
    print("=" * 40)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Test query
        query = "what is tier?"
        print(f"\n🔍 Query: '{query}'")
        print("-" * 50)
        
        # Retrieve documents first
        nodes = rag.retrieve_documents(query, n_results=3)
        print(f"Retrieved {len(nodes)} chunks")
        
        # Format context
        context_parts = []
        for i, node in enumerate(nodes):
            cid = f"C{i+1}"
            text = node.get("text", "")
            score = node.get("similarity_score", 0.0)
            context_parts.append(f"{cid}: {text}")
            print(f"  Chunk {i+1}: similarity={score:.4f}")
        
        context = "\n\n".join(context_parts)
        print(f"\nContext length: {len(context)}")
        
        # Test RAG generation
        print("\n🔍 Testing RAG generation...")
        response = rag.generate_response(query, nodes)
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        if response and isinstance(response, dict):
            print(f"Answer: {response.get('answer', 'N/A')}")
            print(f"Answer type: {response.get('answer_type', 'N/A')}")
            print(f"Confidence: {response.get('confidence', 'N/A')}")
        else:
            print("❌ No valid response generated")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_generation()
