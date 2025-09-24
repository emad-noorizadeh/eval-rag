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
Test Session Management System
Author: Emad Noorizadeh
"""

import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:9000"

def test_session_management():
    """Test the complete session management system"""
    print("=== Testing Session Management System ===\n")
    
    try:
        # Test 1: Create a session
        print("1. Creating a new session...")
        response = requests.post(f"{API_BASE}/sessions")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id[:8]}...")
            print(f"   Created at: {session_data['created_at']}")
            print(f"   Timeout: {session_data['timeout_minutes']} minutes")
            print(f"   Remaining time: {session_data['remaining_time']} seconds")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return
        
        # Test 2: Get session info
        print(f"\n2. Getting session info for {session_id[:8]}...")
        response = requests.get(f"{API_BASE}/sessions/{session_id}")
        if response.status_code == 200:
            session_info = response.json()
            print(f"✅ Session info retrieved:")
            print(f"   Session ID: {session_info['session_id'][:8]}...")
            print(f"   Created at: {session_info['created_at']}")
            print(f"   Last activity: {session_info['last_activity']}")
            print(f"   Remaining time: {session_info['remaining_time']} seconds")
        else:
            print(f"❌ Failed to get session info: {response.status_code}")
        
        # Test 3: Chat with the session
        print(f"\n3. Testing chat with session {session_id[:8]}...")
        chat_data = {
            "message": "What is gold tier?",
            "conversation_history": [],
            "session_id": session_id
        }
        
        response = requests.post(f"{API_BASE}/chat", json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Chat successful:")
            print(f"   Response: {chat_response['response'][:100]}...")
            print(f"   Sources: {len(chat_response['sources'])}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error: {response.text}")
        
        # Test 4: Extend session
        print(f"\n4. Extending session {session_id[:8]}...")
        response = requests.post(f"{API_BASE}/sessions/{session_id}/extend")
        if response.status_code == 200:
            extend_data = response.json()
            print(f"✅ Session extended:")
            print(f"   Remaining time: {extend_data['remaining_time']} seconds")
        else:
            print(f"❌ Failed to extend session: {response.status_code}")
        
        # Test 5: Get active sessions
        print(f"\n5. Getting all active sessions...")
        response = requests.get(f"{API_BASE}/sessions")
        if response.status_code == 200:
            sessions_data = response.json()
            print(f"✅ Active sessions: {sessions_data['active_sessions']}")
            for sid, info in sessions_data['sessions'].items():
                print(f"   Session {sid[:8]}...: {info['remaining_time']}s remaining")
        else:
            print(f"❌ Failed to get active sessions: {response.status_code}")
        
        # Test 6: Test multiple sessions
        print(f"\n6. Creating multiple sessions...")
        session_ids = [session_id]
        
        for i in range(2):
            response = requests.post(f"{API_BASE}/sessions")
            if response.status_code == 200:
                new_session = response.json()
                session_ids.append(new_session["session_id"])
                print(f"   Created session {i+2}: {new_session['session_id'][:8]}...")
        
        # Test 7: Chat with different sessions
        print(f"\n7. Testing chat with different sessions...")
        for i, sid in enumerate(session_ids):
            chat_data = {
                "message": f"Test message {i+1}",
                "conversation_history": [],
                "session_id": sid
            }
            
            response = requests.post(f"{API_BASE}/chat", json=chat_data)
            if response.status_code == 200:
                print(f"   ✅ Session {sid[:8]}...: Chat successful")
            else:
                print(f"   ❌ Session {sid[:8]}...: Chat failed ({response.status_code})")
        
        # Test 8: End a session
        print(f"\n8. Ending session {session_ids[0][:8]}...")
        response = requests.delete(f"{API_BASE}/sessions/{session_ids[0]}")
        if response.status_code == 200:
            print(f"✅ Session ended successfully")
        else:
            print(f"❌ Failed to end session: {response.status_code}")
        
        # Test 9: Try to chat with ended session
        print(f"\n9. Testing chat with ended session...")
        chat_data = {
            "message": "This should fail",
            "conversation_history": [],
            "session_id": session_ids[0]
        }
        
        response = requests.post(f"{API_BASE}/chat", json=chat_data)
        if response.status_code == 410:
            print(f"✅ Correctly rejected chat with ended session (410 Gone)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
        
        print(f"\n✅ Session management test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_management()
