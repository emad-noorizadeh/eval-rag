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
Conversation Utilities for Coreference and Acknowledgment Handling
Author: Emad Noorizadeh

Utilities for handling acknowledgments, coreferences, and conversation snippets
in the context-aware RAG system.
"""

import re
from typing import List, Dict

ACK_TOKENS = {"yes","y","yeah","yep","ok","okay","sure","that","this","it","right","correct","exactly","sounds good"}

def is_ack_or_coref(text: str) -> bool:
    """Check if text is an acknowledgment or contains coreference"""
    t = text.strip().lower()
    if t in ACK_TOKENS:
        return True
    # minimal coref cues - only if the text is short and contains coref pronouns
    if len(t.split()) <= 3:  # Only for short phrases
        return bool(re.search(r"\b(it|that|this|those|these|them|they|he|she)\b", t))
    return False

def build_conversation_snippet(messages: List[Dict[str,str]], turns: int = 3) -> str:
    """Return last N (user,assistant) turns as plain text for non-factual lane."""
    last_pairs = []
    u, a = 0, 0
    for m in reversed(messages):
        if m["role"] == "assistant" and a < turns:
            last_pairs.append(f"Assistant: {m['content']}")
            a += 1
        if m["role"] == "user" and u < turns:
            last_pairs.append(f"User: {m['content']}")
            u += 1
        if u >= turns and a >= turns:
            break
    return "\n".join(reversed(last_pairs))

def validate_evidence_ids(evidence: List[str], allowed_ids: List[str]) -> bool:
    """Validate that all evidence IDs are in the allowed set"""
    allowed = set(allowed_ids)
    return all(e in allowed for e in (evidence or []))
