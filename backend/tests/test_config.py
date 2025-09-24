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
Test script for configuration system
Author: Emad Noorizadeh
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SystemConfig, get_config, set_config, get_data_folder, get_database_path

def test_config_system():
    """Test the configuration system"""
    print("=== Testing Configuration System ===\n")
    
    # Test 1: Default configuration
    print("🔧 Test 1: Default configuration...")
    config = SystemConfig()
    
    # Test basic getters
    data_folder = get_data_folder()
    db_path = get_database_path()
    chunk_size = get_config("chunking", "chunk_size")
    chunk_overlap = get_config("chunking", "chunk_overlap")
    
    print(f"Data folder: {data_folder}")
    print(f"Database path: {db_path}")
    print(f"Chunk size: {chunk_size}")
    print(f"Chunk overlap: {chunk_overlap}")
    
    # Test 2: Configuration sections
    print("\n🔧 Test 2: Configuration sections...")
    database_config = config.get_database_config()
    data_config = config.get_data_config()
    chunking_config = config.get_chunking_config()
    api_config = config.get_api_config()
    
    print(f"Database config: {database_config}")
    print(f"Data config: {data_config}")
    print(f"Chunking config: {chunking_config}")
    print(f"API config: {api_config}")
    
    # Test 3: Set and get configuration
    print("\n🔧 Test 3: Set and get configuration...")
    original_chunk_size = get_config("chunking", "chunk_size")
    set_config("chunking", "chunk_size", 2048)
    new_chunk_size = get_config("chunking", "chunk_size")
    print(f"Original chunk size: {original_chunk_size}")
    print(f"New chunk size: {new_chunk_size}")
    
    # Restore original value
    set_config("chunking", "chunk_size", original_chunk_size)
    
    # Test 4: Configuration validation
    print("\n🔧 Test 4: Configuration validation...")
    validation_results = config.validate_config()
    print(f"Configuration valid: {validation_results['valid']}")
    if validation_results['errors']:
        print(f"Errors: {validation_results['errors']}")
    if validation_results['warnings']:
        print(f"Warnings: {validation_results['warnings']}")
    
    # Test 5: Environment variable loading
    print("\n🔧 Test 5: Environment variable loading...")
    # Set a test environment variable
    os.environ["RAG_CHUNK_SIZE"] = "512"
    os.environ["RAG_DATA_FOLDER"] = "./test_data"
    
    # Create new config instance to test env loading
    test_config = SystemConfig()
    env_chunk_size = test_config.get("chunking", "chunk_size")
    env_data_folder = test_config.get("data", "folder_path")
    
    print(f"Environment chunk size: {env_chunk_size}")
    print(f"Environment data folder: {env_data_folder}")
    
    # Clean up environment variables
    del os.environ["RAG_CHUNK_SIZE"]
    del os.environ["RAG_DATA_FOLDER"]
    
    # Test 6: Sample config creation
    print("\n🔧 Test 6: Sample config creation...")
    config.create_sample_config()
    
    # Test 7: Configuration printing
    print("\n🔧 Test 7: Configuration printing...")
    print("Current configuration:")
    config.print_config()
    
    print(f"\n✅ Configuration system test completed!")

if __name__ == "__main__":
    test_config_system()
