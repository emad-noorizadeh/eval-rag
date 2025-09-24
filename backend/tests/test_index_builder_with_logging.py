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
Test script for IndexBuilder module with logging
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder

class TestLogger:
    """Logger to capture test output to file"""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()

def test_index_builder():
    """Test the index builder functionality"""
    # Set up logging to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_index_builder_results_{timestamp}.txt"
    logger = TestLogger(log_filename)
    sys.stdout = logger
    
    try:
        print("=== Testing IndexBuilder Module ===\n")
        print(f"Test started at: {datetime.now().isoformat()}\n")
        
        # Check if data folder exists
        data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not os.path.exists(data_folder):
            print(f"❌ Data folder not found: {data_folder}")
            return
        
        # List files in data folder
        files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]
        print(f"📁 Found {len(files)} text files in data folder:")
        for file in files:
            print(f"  - {file}")
        print()
        
        # Initialize model manager
        print("🔧 Initializing ModelManager...")
        model_manager = ModelManager()
        print(f"📊 Model status: {model_manager.list_models()}")
        print()
        
        # Initialize index builder
        print("🔧 Initializing IndexBuilder...")
        index_builder = IndexBuilder(
            model_manager, 
            collection_name="test_documents"
        )
        print("✅ IndexBuilder initialized")
        print()
        
        # Build index from folder
        print(f"📚 Building index from folder: {data_folder}")
        result = index_builder.build_index_from_folder(data_folder)
        
        if result['status'] == 'success':
            print("✅ Index built successfully!")
            print(f"📊 Results:")
            print(f"  - Processed files: {result['files_processed']}")
            print(f"  - Total chunks: {result['total_chunks']}")
            print(f"  - Collection size: {result['collection_size']}")
            if result['errors']:
                print(f"  - Errors: {result['errors']}")
        else:
            print(f"❌ Error building index: {result.get('error', 'Unknown error')}")
            return
        
        # Test collection info
        print(f"\n📋 Collection info:")
        info = index_builder.get_collection_info()
        print(f"  - Collection name: {info['collection_name']}")
        print(f"  - Total documents: {info['total_documents']}")
        
        # Test search functionality
        print(f"\n🔍 Testing search functionality...")
        test_queries = [
            "What is the main topic?",
            "Tell me about the content",
            "What are the key points?"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Query: '{query}'")
            try:
                search_results = index_builder.search(query, n_results=3)
                print(f"  Found {len(search_results)} results:")
                
                for i, result in enumerate(search_results):
                    print(f"    {i+1}. Similarity: {result['similarity']:.3f}")
                    print(f"       Text preview: {result['text'][:100]}...")
                    print(f"       Metadata: {result['metadata']}")
            except Exception as e:
                print(f"  ❌ Search error: {e}")
        
        print(f"\n✅ IndexBuilder test completed!")
        print(f"Test completed at: {datetime.now().isoformat()}")
        print(f"Results saved to: {log_filename}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        # Restore stdout and close logger
        sys.stdout = logger.terminal
        logger.close()
        print(f"\n📄 Test results saved to: {log_filename}")

if __name__ == "__main__":
    test_index_builder()
