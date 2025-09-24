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
Test the working flow with good questions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from chat_agent_v2 import ChatAgentV2
from session_manager import session_manager

def test_working_flow():
    """Test the working flow with good questions"""
    print("🧪 Testing Working Flow")
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
        
        # Test 1: Good question that should be answered
        print("\n1. Testing good question: 'what is tier?'")
        response1 = chat_agent_v2.chat(
            message="what is tier?",
            session_id="test-working-flow",
            conversation_history=[]
        )
        
        print(f"   Answer: {response1.get('answer', 'N/A')[:100]}...")
        print(f"   Answer type: {response1.get('metrics', {}).get('answer_type', 'N/A')}")
        print(f"   Confidence: {response1.get('metrics', {}).get('confidence', 'N/A')}")
        
        # Get the actual session ID from the response
        actual_session_id = response1.get('session_id', 'test-working-flow')
        print(f"   Session ID: {actual_session_id}")
        
        # Test 2: Follow-up question
        print("\n2. Testing follow-up: 'what are the requirements?'")
        response2 = chat_agent_v2.chat(
            message="what are the requirements?",
            session_id=actual_session_id,
            conversation_history=[
                {"text": "what is tier?", "isUser": True, "timestamp": "2024-01-01T00:00:00Z"},
                {"text": response1.get('answer', ''), "isUser": False, "timestamp": "2024-01-01T00:00:01Z"}
            ]
        )
        
        print(f"   Answer: {response2.get('answer', 'N/A')[:100]}...")
        print(f"   Answer type: {response2.get('metrics', {}).get('answer_type', 'N/A')}")
        print(f"   Confidence: {response2.get('metrics', {}).get('confidence', 'N/A')}")
        
        # Test 3: Another good question
        print("\n3. Testing another question: 'how do I enroll?'")
        response3 = chat_agent_v2.chat(
            message="how do I enroll?",
            session_id=actual_session_id,
            conversation_history=[
                {"text": "what is tier?", "isUser": True, "timestamp": "2024-01-01T00:00:00Z"},
                {"text": response1.get('answer', ''), "isUser": False, "timestamp": "2024-01-01T00:00:01Z"},
                {"text": "what are the requirements?", "isUser": True, "timestamp": "2024-01-01T00:00:02Z"},
                {"text": response2.get('answer', ''), "isUser": False, "timestamp": "2024-01-01T00:00:03Z"}
            ]
        )
        
        print(f"   Answer: {response3.get('answer', 'N/A')[:100]}...")
        print(f"   Answer type: {response3.get('metrics', {}).get('answer_type', 'N/A')}")
        print(f"   Confidence: {response3.get('metrics', {}).get('confidence', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_working_flow()
