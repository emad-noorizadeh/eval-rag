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
Test the new simplified router V3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from chat_agent_v2 import ChatAgentV2
from session_manager import session_manager

def test_router_v3():
    """Test the new simplified router"""
    print("🧪 Testing Router V3")
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
        
        # Test 1: Initial question
        print("\n1. Testing initial question: 'what is tier?'")
        response1 = chat_agent_v2.chat(
            message="what is tier?",
            session_id="test-session-v3",
            conversation_history=[]
        )
        
        print(f"   Answer: {response1.get('answer', 'N/A')[:100]}...")
        print(f"   Answer type: {response1.get('metrics', {}).get('answer_type', 'N/A')}")
        
        # Get the actual session ID from the response
        actual_session_id = response1.get('session_id', 'test-session-v3')
        print(f"   Session ID: {actual_session_id}")
        
        # Test 2: Clarification response
        print("\n2. Testing clarification response: 'yes'")
        response2 = chat_agent_v2.chat(
            message="yes",
            session_id=actual_session_id,
            conversation_history=[
                {"text": "what is tier?", "isUser": True, "timestamp": "2024-01-01T00:00:00Z"},
                {"text": response1.get('answer', ''), "isUser": False, "timestamp": "2024-01-01T00:00:01Z"}
            ]
        )
        
        print(f"   Answer: {response2.get('answer', 'N/A')[:100]}...")
        print(f"   Answer type: {response2.get('metrics', {}).get('answer_type', 'N/A')}")
        
        # Check if it's still asking for clarification
        if response2.get('metrics', {}).get('answer_type') == 'clarification':
            print("   ❌ Still asking for clarification - LOOP DETECTED!")
        else:
            print("   ✅ Properly answered the question")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_router_v3()
