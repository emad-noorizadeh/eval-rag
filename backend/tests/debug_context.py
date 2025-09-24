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
Debug what's in the retrieved context
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG

def debug_context():
    """Debug what's in the retrieved context"""
    print("🔍 Debugging Context")
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
        
        # Show the actual context that would be sent to the LLM
        context_str, debug_meta, valid_ids = rag._format_context_from_nodes(nodes)
        
        print(f"\n📋 Context that would be sent to LLM:")
        print(f"Valid chunk IDs: {valid_ids}")
        print(f"Context length: {len(context_str)}")
        print("\n" + "="*50)
        print(context_str)
        print("="*50)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_context()
