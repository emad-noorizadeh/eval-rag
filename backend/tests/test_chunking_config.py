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
Test script for chunking configuration
Author: Emad Noorizadeh
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder

def test_chunking_config():
    """Test chunking configuration functionality"""
    print("=== Testing Chunking Configuration ===\n")
    
    # Initialize model manager
    print("🔧 Initializing ModelManager...")
    model_manager = ModelManager()
    
    if not model_manager.list_models()['embedding']:
        print("❌ Embedding model not available. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Test 1: Default configuration
    print("\n🔧 Test 1: Default chunking configuration...")
    index_builder = IndexBuilder(
        model_manager, 
        collection_name="chunking_test"
        # Using LlamaIndex defaults: chunk_size=1024, chunk_overlap=20
    )
    
    config = index_builder.get_chunking_config()
    print("Current configuration:")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # Test 2: Update chunking parameters
    print("\n🔧 Test 2: Update chunking parameters...")
    print("Updating to LlamaIndex defaults...")
    index_builder.update_chunking_params(chunk_size=1024, chunk_overlap=20)
    
    config = index_builder.get_chunking_config()
    print("Updated configuration:")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # Test 3: Test with different chunk sizes
    print("\n🔧 Test 3: Test with different chunk sizes...")
    
    # Test with smaller chunks
    print("Testing with smaller chunks (512, 50)...")
    index_builder.update_chunking_params(chunk_size=512, chunk_overlap=50)
    
    # Test with larger chunks
    print("Testing with larger chunks (2048, 100)...")
    index_builder.update_chunking_params(chunk_size=2048, chunk_overlap=100)
    
    # Test with minimal overlap
    print("Testing with minimal overlap (1000, 10)...")
    index_builder.update_chunking_params(chunk_size=1000, chunk_overlap=10)
    
    # Test with high overlap
    print("Testing with high overlap (1000, 300)...")
    index_builder.update_chunking_params(chunk_size=1000, chunk_overlap=300)
    
    # Final configuration
    print("\n🔧 Final configuration:")
    final_config = index_builder.get_chunking_config()
    print(f"  Chunk size: {final_config['chunk_size']}")
    print(f"  Chunk overlap: {final_config['chunk_overlap']}")
    
    print(f"\n✅ Chunking configuration test completed!")

if __name__ == "__main__":
    test_chunking_config()
