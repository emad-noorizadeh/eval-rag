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
Test retrieval directly to debug similarity scores
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def test_retrieval():
    """Test retrieval directly"""
    print("🔍 Testing Retrieval Directly")
    print("=" * 40)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Test queries
        queries = [
            "what is tier?",
            "What are the different tier levels in the Bank of America Preferred Rewards program and what are their requirements?",
            "tier levels",
            "preferred rewards",
            "bank of america"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 50)
            
            # Retrieve documents
            nodes = rag.retrieve_documents(query, n_results=3)
            print(f"Retrieved {len(nodes)} chunks")
            
            for i, node in enumerate(nodes):
                text = node.get("text", "")
                similarity = node.get("similarity_score", 0.0)
                print(f"  Chunk {i+1}: similarity={similarity:.4f}")
                print(f"    Text: {text[:100]}...")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
