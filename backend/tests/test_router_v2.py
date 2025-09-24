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
Test script for the new router architecture
"""
import requests
import json
import uuid

def test_router_v2():
    """Test the new router architecture"""
    base_url = "http://localhost:9000"
    session_id = str(uuid.uuid4())
    
    print("🧪 Testing New Router Architecture V2")
    print("=" * 50)
    
    # Test 1: Initial vague question
    print("\n📝 Test 1: Initial vague question")
    print("User: 'what is tier?'")
    
    response1 = requests.post(f"{base_url}/chat-v2", json={
        "message": "what is tier?",
        "session_id": session_id
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"Bot: {data1['answer']}")
        print(f"Answer Type: {data1['metrics']['answer_type']}")
        print(f"Confidence: {data1['metrics']['confidence']}")
        print(f"Clarification Question: {data1['metrics']['clarification_question']}")
    else:
        print(f"❌ Error: {response1.status_code} - {response1.text}")
        return
    
    # Test 2: User responds to clarification
    print("\n📝 Test 2: User responds to clarification")
    print("User: 'yes'")
    
    response2 = requests.post(f"{base_url}/chat-v2", json={
        "message": "yes",
        "session_id": session_id
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"Bot: {data2['answer']}")
        print(f"Answer Type: {data2['metrics']['answer_type']}")
        print(f"Confidence: {data2['metrics']['confidence']}")
        print(f"Rephrased Input: {data2['metrics']['rephrased_input']}")
        print(f"Route Decision: {data2['metrics']['route_decision']}")
    else:
        print(f"❌ Error: {response2.status_code} - {response2.text}")
        return
    
    # Test 3: Follow-up question
    print("\n📝 Test 3: Follow-up question")
    print("User: 'what is the minimum balance?'")
    
    response3 = requests.post(f"{base_url}/chat-v2", json={
        "message": "what is the minimum balance?",
        "session_id": session_id
    })
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"Bot: {data3['answer']}")
        print(f"Answer Type: {data3['metrics']['answer_type']}")
        print(f"Confidence: {data3['metrics']['confidence']}")
        print(f"Rephrased Input: {data3['metrics']['rephrased_input']}")
        print(f"Route Decision: {data3['metrics']['route_decision']}")
    else:
        print(f"❌ Error: {response3.status_code} - {response3.text}")
        return
    
    print("\n✅ Router V2 Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_router_v2()
