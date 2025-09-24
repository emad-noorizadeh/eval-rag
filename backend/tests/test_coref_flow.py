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
Tests for Coreference and Acknowledgment Flow
Author: Emad Noorizadeh

Tests for the conversation utilities that handle acknowledgments,
coreferences, and conversation snippets in the context-aware RAG system.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.conversation_utils import is_ack_or_coref, build_conversation_snippet, validate_evidence_ids

def test_is_ack_or_coref():
    """Test acknowledgment and coreference detection"""
    # Test acknowledgments
    assert is_ack_or_coref("yes")
    assert is_ack_or_coref("That")
    assert is_ack_or_coref("it")
    assert is_ack_or_coref("YEP")
    assert is_ack_or_coref("sure")
    assert is_ack_or_coref("correct")
    assert is_ack_or_coref("exactly")
    assert is_ack_or_coref("sounds good")
    
    # Test coreferences
    assert is_ack_or_coref("that one")
    assert is_ack_or_coref("this is it")
    assert is_ack_or_coref("they are good")
    assert is_ack_or_coref("he mentioned it")
    
    # Test non-acknowledgments
    assert not is_ack_or_coref("what are the tiers?")
    assert not is_ack_or_coref("tell me about benefits")
    assert not is_ack_or_coref("how much does it cost")
    assert not is_ack_or_coref("")
    assert not is_ack_or_coref("   ")

def test_build_conversation_snippet():
    """Test conversation snippet building"""
    msgs = [
        {"role":"user","content":"What are tiers?"},
        {"role":"assistant","content":"Do you mean Bank of America Preferred Rewards?"},
        {"role":"user","content":"yes"}
    ]
    s = build_conversation_snippet(msgs, turns=2)
    assert "Assistant:" in s and "User:" in s
    assert "What are tiers?" in s
    assert "Bank of America Preferred Rewards" in s
    assert "yes" in s
    
    # Test with more turns than available
    s = build_conversation_snippet(msgs, turns=5)
    assert len(s.split('\n')) <= 6  # 3 pairs max
    
    # Test with empty messages
    s = build_conversation_snippet([], turns=3)
    assert s == ""

def test_validate_evidence_ids():
    """Test evidence ID validation"""
    allowed = ["C1","C2","C3"]
    
    # Valid evidence
    assert validate_evidence_ids(["C1","C3"], allowed)
    assert validate_evidence_ids(["C2"], allowed)
    assert validate_evidence_ids([], allowed)
    
    # Invalid evidence
    assert not validate_evidence_ids(["C4"], allowed)
    assert not validate_evidence_ids(["C1","C4"], allowed)
    assert not validate_evidence_ids(["C5","C6"], allowed)
    
    # Edge cases
    assert validate_evidence_ids(None, allowed)
    assert validate_evidence_ids([], [])

def test_integration_flow():
    """Test the complete flow integration"""
    # Simulate a conversation flow
    messages = [
        {"role": "user", "content": "What are the tiers?"},
        {"role": "assistant", "content": "Could you clarify which program's tiers you mean? Bank of America Preferred Rewards?"},
        {"role": "user", "content": "yes"}
    ]
    
    # Test conversation snippet building
    snippet = build_conversation_snippet(messages, turns=3)
    assert "What are the tiers?" in snippet
    assert "Bank of America Preferred Rewards" in snippet
    assert "yes" in snippet
    
    # Test acknowledgment detection
    assert is_ack_or_coref("yes")
    assert is_ack_or_coref("that")
    assert not is_ack_or_coref("what are the tiers?")
    
    # Test evidence validation
    retrieved_chunks = [{"text": "chunk1"}, {"text": "chunk2"}, {"text": "chunk3"}]
    valid_ids = [f"C{i+1}" for i in range(len(retrieved_chunks))]
    assert validate_evidence_ids(["C1", "C2"], valid_ids)
    assert not validate_evidence_ids(["C4"], valid_ids)

if __name__ == "__main__":
    print("Running coreference flow tests...")
    
    test_is_ack_or_coref()
    print("✅ test_is_ack_or_coref passed")
    
    test_build_conversation_snippet()
    print("✅ test_build_conversation_snippet passed")
    
    test_validate_evidence_ids()
    print("✅ test_validate_evidence_ids passed")
    
    test_integration_flow()
    print("✅ test_integration_flow passed")
    
    print("\n🎉 All tests passed!")
