# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Local Tokenizer for Offline Deployment
Author: Emad Noorizadeh

Provides local tokenization without requiring internet access.
Uses a simple word-based tokenizer as fallback when tiktoken is not available
or when internet access is disabled.
"""

import re
import os
from typing import List, Callable, Optional

def create_local_tokenizer() -> Callable[[str], List[int]]:
    """
    Create a local tokenizer that works offline.
    
    Returns:
        A function that takes a string and returns a list of token IDs
    """
    def local_encode(text: str) -> List[int]:
        """
        Simple local tokenizer that splits text into words and assigns IDs.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of token IDs
        """
        if not text:
            return []
        
        # Simple word-based tokenization
        # Split on whitespace and punctuation, keep alphanumeric sequences
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Create a simple hash-based token ID system
        token_ids = []
        for token in tokens:
            # Use hash of token as ID (simple but consistent)
            token_id = hash(token) % 100000  # Keep IDs in reasonable range
            token_ids.append(token_id)
        
        return token_ids
    
    return local_encode

def create_character_tokenizer() -> Callable[[str], List[int]]:
    """
    Create a character-based tokenizer for more precise tokenization.
    
    Returns:
        A function that takes a string and returns a list of token IDs
    """
    def char_encode(text: str) -> List[int]:
        """
        Character-based tokenizer.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of character token IDs
        """
        if not text:
            return []
        
        # Convert each character to its Unicode code point
        return [ord(char) for char in text]
    
    return char_encode

def get_offline_encoder(encoding_name: str = "cl100k_base") -> Callable[[str], List[int]]:
    """
    Get an offline tokenizer encoder.
    
    Args:
        encoding_name: Name of the encoding (for compatibility, not used in offline mode)
        
    Returns:
        A tokenizer function that works offline
    """
    # For now, use word-based tokenizer
    # In production, you might want to use a more sophisticated local tokenizer
    return create_local_tokenizer()

def get_token_count(text: str, encoder: Callable[[str], List[int]]) -> int:
    """
    Get the number of tokens in text using the provided encoder.
    
    Args:
        text: Input text
        encoder: Tokenizer function
        
    Returns:
        Number of tokens
    """
    return len(encoder(text))

def is_offline_mode() -> bool:
    """
    Check if the system is running in offline mode.
    
    Returns:
        True if offline mode is enabled
    """
    return os.getenv("OFFLINE_MODE", "false").lower() in ("true", "1", "yes")

def get_safe_encoder(encoding_name: str = "cl100k_base") -> Callable[[str], List[int]]:
    """
    Get a safe encoder that works both online and offline.
    
    Args:
        encoding_name: Name of the encoding
        
    Returns:
        A tokenizer function
    """
    # Check if we're in offline mode
    if is_offline_mode():
        print("🔒 Offline mode: Using local tokenizer")
        return get_offline_encoder(encoding_name)
    
    # Try to use tiktoken if available and online
    try:
        import tiktoken
        # Set environment variable to prevent downloads
        os.environ["TIKTOKEN_CACHE_DIR"] = "./tokenizer_cache"
        return tiktoken.get_encoding(encoding_name).encode
    except Exception as e:
        print(f"⚠️  tiktoken not available ({e}), using local tokenizer")
        return get_offline_encoder(encoding_name)

# Test the tokenizer
if __name__ == "__main__":
    print("🧪 Testing local tokenizer...")
    
    test_text = "Hello world! This is a test sentence."
    
    # Test local tokenizer
    local_encoder = create_local_tokenizer()
    tokens = local_encoder(test_text)
    print(f"Local tokenizer: {len(tokens)} tokens")
    print(f"Tokens: {tokens[:10]}...")  # Show first 10 tokens
    
    # Test character tokenizer
    char_encoder = create_character_tokenizer()
    char_tokens = char_encoder(test_text)
    print(f"Character tokenizer: {len(char_tokens)} tokens")
    print(f"Tokens: {char_tokens[:10]}...")  # Show first 10 tokens
    
    print("✅ Local tokenizer test completed")
