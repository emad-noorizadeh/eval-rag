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

#!/usr/bin/env python3
"""
Debug script to test conversation context handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent import create_chat_agent
import json

def test_conversation_context():
    """Test conversation context handling"""
    print("Creating chat agent...")
    agent = create_chat_agent()
    
    # Test first question
    print("\n=== Test 1: what is tier? ===")
    result1 = agent.chat(
        message="what is tier",
        session_id="test-session-1",
        conversation_history=[]
    )
    print(f"Response: {result1['response']}")
    
    # Test follow-up response
    print("\n=== Test 2: yes (clarification response) ===")
    conversation_history = [
        {"role": "user", "content": "what is tier", "timestamp": "2024-01-01T00:00:00Z"},
        {"role": "assistant", "content": result1['response'], "timestamp": "2024-01-01T00:00:00Z"}
    ]
    
    print(f"Conversation history: {conversation_history}")
    print(f"Last assistant message: {conversation_history[-1]['content']}")
    print(f"Contains clarification: {'I need to clarify your question:' in conversation_history[-1]['content']}")
    
    result2 = agent.chat(
        message="yes",
        session_id="test-session-1",
        conversation_history=conversation_history
    )
    print(f"Response: {result2['response']}")
    
    # Test with more explicit conversation history
    print("\n=== Test 3: yes with explicit conversation history ===")
    conversation_history = [
        {"text": "what is tier", "isUser": True, "timestamp": "2024-01-01T00:00:00Z"},
        {"text": result1['response'], "isUser": False, "timestamp": "2024-01-01T00:00:00Z"}
    ]
    
    result3 = agent.chat(
        message="yes",
        session_id="test-session-1",
        conversation_history=conversation_history
    )
    print(f"Response: {result3['response']}")

if __name__ == "__main__":
    test_conversation_context()
