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
Session Management System
Author: Emad Noorizadeh

Handles user sessions with 30-minute expiration and automatic cleanup.
Each session maintains its own chat agent instance.
"""

import uuid
import time
import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
# from chat_agent import ChatAgent  # Avoid circular import
from model_manager import ModelManager
from index_builder import IndexBuilder
from config import get_config


@dataclass
class SessionData:
    """Data structure for a user session"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    agent_state: Optional[Dict[str, Any]] = None
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        if not self.is_active:
            return True
        
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time
    
    def get_remaining_time(self, timeout_minutes: int = 30) -> int:
        """Get remaining time in seconds before expiration"""
        if not self.is_active:
            return 0
        
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        remaining = expiry_time - datetime.now()
        return max(0, int(remaining.total_seconds()))


class SessionManager:
    """Manages user sessions with automatic cleanup"""
    
    def __init__(self, timeout_minutes: int = 30, cleanup_interval: int = 300):
        """
        Initialize session manager
        
        Args:
            timeout_minutes: Session timeout in minutes (default: 30)
            cleanup_interval: Cleanup interval in seconds (default: 5 minutes)
        """
        self.timeout_minutes = timeout_minutes
        self.cleanup_interval = cleanup_interval
        self.sessions: Dict[str, SessionData] = {}
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        print(f"✅ SessionManager initialized: {timeout_minutes}min timeout, {cleanup_interval}s cleanup")
    
    def create_session(self) -> str:
        """
        Create a new session
        
        Returns:
            Session ID
        """
        with self.lock:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            try:
                # Create session data
                session_data = SessionData(
                    session_id=session_id,
                    created_at=datetime.now(),
                    last_activity=datetime.now()
                )
                
                # Store session
                self.sessions[session_id] = session_data
                
                print(f"✅ Session {session_id[:8]} created successfully")
                return session_id
                
            except Exception as e:
                print(f"❌ Failed to create session: {e}")
                raise
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data and update activity
        
        Args:
            session_id: Session ID to retrieve
        
        Returns:
            SessionData if found and active, None otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session is None:
                return None
            
            # Check if expired
            if session.is_expired(self.timeout_minutes):
                print(f"⏰ Session {session_id[:8]} expired, removing...")
                self._remove_session(session_id)
                return None
            
            # Update activity
            session.update_activity()
            return session
    
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information without updating activity
        
        Args:
            session_id: Session ID
        
        Returns:
            Session info dict or None if not found/expired
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session is None or session.is_expired(self.timeout_minutes):
                return None
            
            return {
                "session_id": session_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active,
                "remaining_time": session.get_remaining_time(self.timeout_minutes),
                "timeout_minutes": self.timeout_minutes
            }
    
    def extend_session(self, session_id: str) -> bool:
        """
        Extend session by updating last activity
        
        Args:
            session_id: Session ID to extend
        
        Returns:
            True if extended, False if session not found/expired
        """
        session = self.get_session(session_id)
        return session is not None
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session
        
        Args:
            session_id: Session ID to end
        
        Returns:
            True if ended, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                self._remove_session(session_id)
                return True
            return False
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active sessions
        
        Returns:
            Dict of session_id -> session_info
        """
        with self.lock:
            active_sessions = {}
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if session.is_expired(self.timeout_minutes):
                    expired_sessions.append(session_id)
                else:
                    active_sessions[session_id] = {
                        "session_id": session_id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "remaining_time": session.get_remaining_time(self.timeout_minutes),
                        "is_active": session.is_active
                    }
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                self._remove_session(session_id)
            
            return active_sessions
    
    
    def update_session_state(self, session_id: str, agent_state: Dict[str, Any]) -> bool:
        """Update the agent state for a session"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.agent_state = agent_state
                session.last_activity = datetime.now()
                return True
            return False
    
    def _remove_session(self, session_id: str):
        """Remove a session from the manager"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            del self.sessions[session_id]
            print(f"🗑️ Session {session_id[:8]} removed")
    
    def _cleanup_loop(self):
        """Background thread for cleaning up expired sessions"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_sessions()
            except Exception as e:
                print(f"❌ Error in cleanup loop: {e}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        with self.lock:
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if session.is_expired(self.timeout_minutes):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self._remove_session(session_id)
            
            if expired_sessions:
                print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


# Global session manager instance
session_manager = SessionManager(
    timeout_minutes=get_config("session", "timeout_minutes"),
    cleanup_interval=get_config("session", "cleanup_interval")
)
