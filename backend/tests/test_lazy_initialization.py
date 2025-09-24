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
Test script for lazy initialization behavior
Author: Emad Noorizadeh
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder

def test_lazy_initialization():
    """Test lazy initialization behavior"""
    print("=== Testing Lazy Initialization ===\n")
    
    # Initialize model manager
    print("🔧 Initializing ModelManager...")
    model_manager = ModelManager()
    
    if not model_manager.list_models()['embedding']:
        print("❌ Embedding model not available. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Test 1: Constructor doesn't initialize index immediately
    print("\n🔧 Test 1: Constructor behavior...")
    print("Creating IndexBuilder instance...")
    index_builder = IndexBuilder(
        model_manager, 
        collection_name="lazy_test",
        db_path="./test_lazy_db"
    )
    
    print(f"Index initialized after constructor: {index_builder.index is not None}")
    
    # Test 2: First search call initializes the index
    print("\n🔧 Test 2: First search call...")
    print("Performing search (should trigger lazy initialization)...")
    results = index_builder.search("test query", n_results=1)
    print(f"Index initialized after first search: {index_builder.index is not None}")
    print(f"Search results count: {len(results)}")
    
    # Test 3: Subsequent calls don't reinitialize
    print("\n🔧 Test 3: Subsequent calls...")
    print("Performing another search...")
    results2 = index_builder.search("another query", n_results=1)
    print(f"Index still initialized: {index_builder.index is not None}")
    print(f"Second search results count: {len(results2)}")
    
    # Test 4: Add document also triggers lazy initialization
    print("\n🔧 Test 4: Add document...")
    print("Adding a test document...")
    doc_id = index_builder.add_document("This is a test document for lazy initialization.")
    print(f"Document added with ID: {doc_id}")
    print(f"Index initialized after add_document: {index_builder.index is not None}")
    
    # Test 5: Build index from folder
    print("\n🔧 Test 5: Build index from folder...")
    data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if os.path.exists(data_folder):
        print("Building index from data folder...")
        result = index_builder.build_index_from_folder(data_folder)
        print(f"Index built successfully: {result['processed_files']} files, {result['total_chunks']} chunks")
    else:
        print("Data folder not found, skipping folder test")
    
    print(f"\n✅ Lazy initialization test completed!")

if __name__ == "__main__":
    test_lazy_initialization()
