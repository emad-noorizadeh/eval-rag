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
Test the chunks format being sent to frontend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from chat_agent_v2 import ChatAgentV2
from session_manager import session_manager
import json

def test_chunks_format():
    """Test the chunks format being sent to frontend"""
    print("🧪 Testing Chunks Format")
    print("=" * 40)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Create chat agent V2
        print("Creating ChatAgentV2...")
        chat_agent_v2 = ChatAgentV2(rag, model_manager, session_manager)
        
        # Test question
        print("\nTesting question: 'what is tier?'")
        response = chat_agent_v2.chat(
            message="what is tier?",
            session_id="test-chunks-format",
            conversation_history=[]
        )
        
        print(f"Answer: {response.get('answer', 'N/A')[:100]}...")
        print(f"Answer type: {response.get('metrics', {}).get('answer_type', 'N/A')}")
        
        # Check chunks format
        chunks = response.get('metrics', {}).get('chunks_retrieved', [])
        print(f"\nChunks retrieved: {len(chunks)}")
        
        if chunks:
            print("\nFirst chunk format:")
            print(json.dumps(chunks[0], indent=2))
            
            # Check required fields
            required_fields = ['id', 'text', 'similarity_score', 'chunk_index', 'text_length']
            missing_fields = [field for field in required_fields if field not in chunks[0]]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print("✅ All required fields present")
        else:
            print("❌ No chunks retrieved")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chunks_format()
