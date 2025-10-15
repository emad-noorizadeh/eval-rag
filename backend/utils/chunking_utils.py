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
Chunking Utilities
Author: Emad Noorizadeh

Utilities for configurable chunking modes (tokenizer-based vs word-count-based).
"""

import os
import json
from typing import List, Callable, Dict, Any

def get_chunking_config() -> Dict[str, Any]:
    """
    Get chunking configuration from the main config system.
    
    Returns:
        Dict containing chunking configuration
    """
    try:
        from ..config import get_config
        return get_config("chunking")
    except Exception as e:
        print(f"⚠️  Error reading chunking config: {e}")
        # Default fallback
        return {
            "word_count_ratio": 0.75
        }

def set_word_count_ratio(word_count_ratio: float) -> bool:
    """
    Set word count ratio using the main config system.
    
    Args:
        word_count_ratio: Ratio for word count mode
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from ..config import set_word_count_ratio
        return set_word_count_ratio(word_count_ratio)
    except Exception as e:
        print(f"❌ Error updating word count ratio: {e}")
        return False

def get_word_count_splitter(chunk_size: int, chunk_overlap: int) -> Callable[[str], List[str]]:
    """
    Get a word-count-based splitter.
    
    Args:
        chunk_size: Maximum words per chunk
        chunk_overlap: Number of words to overlap between chunks
        
    Returns:
        Function that splits text into chunks
    """
    def word_count_split(text: str) -> List[str]:
        """Split text by word count using simple approach"""
        if not text:
            return []
        
        # Split by sentences first
        sentences = text.split('. ')
        if len(sentences) == 1:
            sentences = text.split('\n')
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            # If adding this sentence would exceed chunk_size, save current chunk
            if current_word_count + sentence_word_count > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = sentence_words
                current_word_count = sentence_word_count
            else:
                current_chunk.extend(sentence_words)
                current_word_count += sentence_word_count
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    return word_count_split

def get_configurable_encoder() -> Callable[[str], List[int]]:
    """
    Get encoder based on chunking configuration.
    
    Returns:
        Encoder function for the configured chunking mode
    """
    config = get_chunking_config()
    use_tokenizer = config.get("use_tokenizer", False)
    
    if use_tokenizer:
        # Try to get tokenizer encoder
        try:
            from ..index_builder import _get_encoder
            return _get_encoder("cl100k_base")
        except Exception as e:
            print(f"⚠️  Tokenizer not available ({e}), falling back to word count")
            # Fall back to word count encoder
            pass
    
    # Word count encoder (simple word counter)
    def word_count_encoder(text: str) -> List[int]:
        """Simple word count encoder for non-tokenizer mode"""
        if not text:
            return []
        return list(range(len(text.split())))
    
    return word_count_encoder

def get_effective_chunk_sizes(chunk_size: int, chunk_overlap: int) -> Dict[str, int]:
    """
    Get effective chunk sizes based on word-count configuration.
    
    Args:
        chunk_size: Base chunk size
        chunk_overlap: Base chunk overlap
        
    Returns:
        Dict with effective sizes for word-count mode
    """
    config = get_chunking_config()
    word_count_ratio = config.get("word_count_ratio", 0.75)
    
    effective_size = int(chunk_size * word_count_ratio)
    effective_overlap = int(chunk_overlap * word_count_ratio)
    return {
        "mode": "word_count",
        "chunk_size": effective_size,
        "chunk_overlap": effective_overlap,
        "unit": "words",
        "ratio": word_count_ratio
    }

if __name__ == "__main__":
    from ..config import show_chunking_config
    show_chunking_config()
