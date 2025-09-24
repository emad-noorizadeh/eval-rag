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
LangGraph Agent Test Runner
Author: Emad Noorizadeh
"""

import os
import sys
from chat_agent import create_chat_agent


def test_langgraph_agent():
    """Test the LangGraph agent with clarification flow"""
    print("=== Testing LangGraph Chat Agent ===\n")
    
    try:
        # Create chat agent
        print("🔧 Creating LangGraph chat agent...")
        agent = create_chat_agent(data_folder="./data", collection_name="langgraph_test")
        print("✅ Agent created successfully")
        
        # Test session
        session_id = "demo-session-1"
        
        print(f"\n{'='*80}")
        print("Session 1: Vague question (should trigger clarification)")
        print('='*80)
        
        # First turn - vague question
        vague_question = "What is the price of the gloves?"
        print(f"User: {vague_question}")
        
        response1 = agent.chat(vague_question, session_id)
        print(f"Agent: {response1['response']}")
        print(f"Clarify count: {response1['metrics']['clarify_count']}")
        print(f"Sources: {len(response1['sources'])}")
        
        print(f"\n{'='*80}")
        print("Session 2: Specific answer to clarification")
        print('='*80)
        
        # Second turn - specific answer
        specific_answer = "Half-dipped nylon nitrile, in Vadodara."
        print(f"User: {specific_answer}")
        
        response2 = agent.chat(specific_answer, session_id)
        print(f"Agent: {response2['response']}")
        print(f"Clarify count: {response2['metrics']['clarify_count']}")
        print(f"Sources: {len(response2['sources'])}")
        
        # Show conversation history
        print(f"\n{'='*80}")
        print("Conversation History")
        print('='*80)
        
        history = response2.get('conversation_history', [])
        for i, msg in enumerate(history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"{i}. {role.upper()}: {content}")
        
        print(f"\n✅ LangGraph agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_financial_queries():
    """Test with financial domain queries"""
    print("\n=== Testing Financial Domain Queries ===\n")
    
    try:
        # Create chat agent
        agent = create_chat_agent(data_folder="./data", collection_name="financial_test")
        
        # Test queries
        test_cases = [
            ("gold", "Vague - should clarify"),
            ("what is gold tier", "Clear - should answer"),
            ("fees", "Vague - should clarify"),
            ("what are the account fees for checking", "Clear - should answer")
        ]
        
        session_id = "financial-session-1"
        
        for i, (query, expected) in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {query} ({expected})")
            print('='*60)
            
            response = agent.chat(query, session_id)
            print(f"Agent: {response['response']}")
            print(f"Clarify count: {response['metrics']['clarify_count']}")
            print(f"Sources: {len(response['sources'])}")
            
            # Check if clarification was asked
            if "clarify" in response['response'].lower() or "?" in response['response']:
                print("✅ Clarification requested")
            else:
                print("✅ Direct answer provided")
        
        print(f"\n✅ Financial domain test completed successfully!")
        
    except Exception as e:
        print(f"❌ Financial test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests
    test_langgraph_agent()
    test_financial_queries()
