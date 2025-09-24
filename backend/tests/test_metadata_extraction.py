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
Test script for metadata extraction functionality
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder
from config import set_config

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

def test_metadata_extraction():
    """Test metadata extraction functionality"""
    # Set up logging to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_metadata_extraction_results_{timestamp}.txt"
    logger = TestLogger(log_filename)
    sys.stdout = logger
    
    try:
        print("=== Testing Metadata Extraction ===\n")
        print(f"Test started at: {datetime.now().isoformat()}\n")
    
    # Initialize model manager
    print("🔧 Initializing ModelManager...")
    model_manager = ModelManager()
    
    if not model_manager.list_models()['embedding']:
        print("❌ Embedding model not available. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Test 1: Enable metadata extraction
    print("\n🔧 Test 1: Enable metadata extraction...")
    set_config("data", "extract_metadata", True)
    set_config("data", "recursive", True)
    
    # Enable all metadata extraction features
    metadata_config = {
        "extract_headings": True,
        "extract_links": True,
        "extract_dates": True,
        "extract_emails": True,
        "extract_urls": True,
        "extract_categories": True,
        "max_heading_lines": 10,
        "max_category_lines": 5
    }
    
    for key, value in metadata_config.items():
        set_config("data", f"metadata_extraction.{key}", value)
    
    print("✓ Metadata extraction enabled")
    
    # Test 2: Create IndexBuilder with metadata extraction
    print("\n🔧 Test 2: Create IndexBuilder with metadata extraction...")
    index_builder = IndexBuilder(
        model_manager, 
        collection_name="metadata_test"
    )
    
    # Test 3: Build index with enhanced metadata
    print("\n🔧 Test 3: Build index with enhanced metadata...")
    data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    if os.path.exists(data_folder):
        result = index_builder.build_index_from_folder(data_folder)
        print(f"✓ Index built: {result['processed_files']} files, {result['total_chunks']} chunks")
        
        # Test 4: Search and examine metadata
        print("\n🔧 Test 4: Search and examine metadata...")
        search_results = index_builder.search("Bank of America", n_results=3)
        
        print(f"Found {len(search_results)} results:")
        for i, result in enumerate(search_results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Similarity: {result['similarity']:.3f}")
            print(f"Text preview: {result['text'][:100]}...")
            print(f"Metadata keys: {list(result['metadata'].keys())}")
            
            # Show specific metadata
            metadata = result['metadata']
            if 'title' in metadata:
                print(f"Title: {metadata['title']}")
            if 'headline' in metadata:
                print(f"Headline: {metadata['headline']}")
            if 'is_link' in metadata and metadata['is_link']:
                print(f"Link text: {metadata.get('link_text', 'N/A')}")
                print(f"Link URL: {metadata.get('link_url', 'N/A')}")
            if 'headings' in metadata:
                print(f"Headings: {metadata['headings']}")
            if 'categories' in metadata:
                print(f"Categories: {metadata['categories']}")
            if 'urls' in metadata:
                print(f"URLs: {metadata['urls']}")
            if 'dates_found' in metadata:
                print(f"Dates: {metadata['dates_found']}")
            if 'emails' in metadata:
                print(f"Emails: {metadata['emails']}")
            
            # Show document structure
            print(f"Line count: {metadata.get('line_count', 'N/A')}")
            print(f"Word count: {metadata.get('word_count', 'N/A')}")
            print(f"Char count: {metadata.get('char_count', 'N/A')}")
            print(f"Processed at: {metadata.get('processed_at', 'N/A')}")
    
    else:
        print(f"❌ Data folder not found: {data_folder}")
    
    # Test 5: Test with metadata extraction disabled
    print("\n🔧 Test 5: Test with metadata extraction disabled...")
    set_config("data", "extract_metadata", False)
    
    index_builder_no_metadata = IndexBuilder(
        model_manager, 
        collection_name="no_metadata_test"
    )
    
    if os.path.exists(data_folder):
        result = index_builder_no_metadata.build_index_from_folder(data_folder)
        print(f"✓ Index built without metadata: {result['processed_files']} files, {result['total_chunks']} chunks")
        
        search_results = index_builder_no_metadata.search("Bank of America", n_results=1)
        if search_results:
            metadata = search_results[0]['metadata']
            print(f"Metadata keys without extraction: {list(metadata.keys())}")
    
        print(f"\n✅ Metadata extraction test completed!")
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
    test_metadata_extraction()
