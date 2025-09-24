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
Test the clarification loop issue
"""
import requests
import json

def test_clarification_loop():
    """Test the clarification loop by simulating the conversation"""
    print("🧪 Testing Clarification Loop")
    print("=" * 40)
    
    session_id = "test-clarification-session"
    
    try:
        # First message: "what is tier?"
        print("1. Sending: 'what is tier?'")
        response1 = requests.post(
            "http://localhost:9000/chat-v2",
            json={
                "message": "what is tier?",
                "conversation_history": [],
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   Response: {data1.get('answer', 'N/A')[:100]}...")
            print(f"   Answer type: {data1.get('metrics', {}).get('answer_type', 'N/A')}")
            
            # Second message: "yes"
            print("\n2. Sending: 'yes'")
            response2 = requests.post(
                "http://localhost:9000/chat-v2",
                json={
                    "message": "yes",
                    "conversation_history": [
                        {"text": "what is tier?", "isUser": True, "timestamp": "2024-01-01T00:00:00Z"},
                        {"text": data1.get('answer', ''), "isUser": False, "timestamp": "2024-01-01T00:00:01Z"}
                    ],
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   Response: {data2.get('answer', 'N/A')[:100]}...")
                print(f"   Answer type: {data2.get('metrics', {}).get('answer_type', 'N/A')}")
                print(f"   Rephrased: {data2.get('metrics', {}).get('ingest_metrics', {}).get('processed_question', 'N/A')}")
                
                # Check if it's still asking for clarification
                if data2.get('metrics', {}).get('answer_type') == 'clarification':
                    print("   ❌ Still asking for clarification - LOOP DETECTED!")
                else:
                    print("   ✅ Properly answered the question")
            else:
                print(f"   ❌ Error: {response2.status_code}")
        else:
            print(f"   ❌ Error: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_clarification_loop()
