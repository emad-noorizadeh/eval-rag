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
Test the UI fix by calling the chat-v2 endpoint
"""
import requests
import json

def test_ui_fix():
    """Test that the chat-v2 endpoint returns the correct response format"""
    print("🧪 Testing UI Fix")
    print("=" * 40)
    
    try:
        # Test the chat-v2 endpoint
        response = requests.post(
            "http://localhost:9000/chat-v2",
            json={
                "message": "what is tier?",
                "conversation_history": [],
                "session_id": "test-session-123"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received successfully")
            print(f"Answer: {data.get('answer', 'N/A')[:100]}...")
            print(f"Sources: {len(data.get('sources', []))}")
            print(f"Metrics available: {data.get('metrics') is not None}")
            
            # Check if the response has the expected structure
            if 'answer' in data:
                print("✅ 'answer' field present")
            else:
                print("❌ 'answer' field missing")
                
            if 'sources' in data:
                print("✅ 'sources' field present")
            else:
                print("❌ 'sources' field missing")
                
            if 'metrics' in data:
                print("✅ 'metrics' field present")
            else:
                print("❌ 'metrics' field missing")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ui_fix()
