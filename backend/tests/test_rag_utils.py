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
Test script for RAG utilities
Author: Emad Noorizadeh
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.rag_utils import MetadataExtractor, DocumentProcessor, create_file_metadata_function, validate_document_folder
from config import get_config

def test_metadata_extractor():
    """Test the MetadataExtractor class"""
    print("=== Testing MetadataExtractor ===\n")
    
    # Test 1: Initialize extractor
    print("🔧 Test 1: Initialize MetadataExtractor...")
    extractor = MetadataExtractor(get_config)
    print("✓ MetadataExtractor initialized")
    
    # Test 2: Extract metadata from sample text
    print("\n🔧 Test 2: Extract metadata from sample text...")
    sample_text = """[Skip to content](https://example.com/skip)

# Main Heading

This is a sample document with some content.

## Subheading

- List item 1
- List item 2

Contact us at support@example.com for more information.
Visit our website at https://example.com for details.
"""
    
    metadata = extractor.extract_content_metadata(sample_text)
    print(f"✓ Metadata extracted: {len(metadata)} fields")
    print(f"Metadata keys: {list(metadata.keys())}")
    
    # Test specific metadata fields
    if 'title' in metadata:
        print(f"Title: {metadata['title']}")
    if 'link_text' in metadata:
        print(f"Link text: {metadata['link_text']}")
    if 'link_url' in metadata:
        print(f"Link URL: {metadata['link_url']}")
    if 'headings' in metadata:
        print(f"Headings: {metadata['headings']}")
    if 'emails' in metadata:
        print(f"Emails: {metadata['emails']}")
    if 'urls' in metadata:
        print(f"URLs: {metadata['urls']}")
    
    # Test 3: Test individual extraction methods
    print("\n🔧 Test 3: Test individual extraction methods...")
    
    # Test link extraction
    link_metadata = extractor._extract_link_metadata("[Test Link](https://test.com)")
    print(f"Link extraction: {link_metadata}")
    
    # Test heading extraction
    heading_metadata = extractor._extract_heading_metadata("### Test Heading")
    print(f"Heading extraction: {heading_metadata}")
    
    # Test category extraction
    categories = extractor._extract_categories(["This is about banking and financial services"], 1)
    print(f"Category extraction: {categories}")
    
    # Test date extraction
    dates_metadata = extractor._extract_dates("The date is 2024-01-15 and also 01/15/2024")
    print(f"Date extraction: {dates_metadata}")
    
    # Test email extraction
    emails = extractor._extract_emails("Contact us at test@example.com and admin@test.org")
    print(f"Email extraction: {emails}")
    
    # Test URL extraction
    urls = extractor._extract_urls("Visit https://example.com and http://test.org")
    print(f"URL extraction: {urls}")
    
    print(f"\n✅ MetadataExtractor test completed!")

def test_document_processor():
    """Test the DocumentProcessor class"""
    print("\n=== Testing DocumentProcessor ===\n")
    
    # Test 1: Initialize processor
    print("🔧 Test 1: Initialize DocumentProcessor...")
    processor = DocumentProcessor(get_config)
    print("✓ DocumentProcessor initialized")
    
    # Test 2: Test configuration methods
    print("\n🔧 Test 2: Test configuration methods...")
    should_extract = processor.should_extract_metadata()
    should_recursive = processor.should_use_recursive()
    print(f"Should extract metadata: {should_extract}")
    print(f"Should use recursive: {should_recursive}")
    
    # Test 3: Test document enhancement (mock)
    print("\n🔧 Test 3: Test document enhancement...")
    
    # Create mock document
    from llama_index.core import Document
    mock_doc = Document(
        text="[Test Link](https://test.com)\n\n# Test Heading\n\nThis is test content.",
        metadata={"source": "test.txt"},
        id_="test_doc"
    )
    
    enhanced_docs = processor.enhance_document_metadata([mock_doc])
    print(f"✓ Enhanced {len(enhanced_docs)} documents")
    
    if enhanced_docs:
        enhanced_metadata = enhanced_docs[0].metadata
        print(f"Enhanced metadata keys: {list(enhanced_metadata.keys())}")
        if 'link_text' in enhanced_metadata:
            print(f"Link text: {enhanced_metadata['link_text']}")
        if 'main_heading' in enhanced_metadata:
            print(f"Main heading: {enhanced_metadata['main_heading']}")
    
    print(f"\n✅ DocumentProcessor test completed!")

def test_utility_functions():
    """Test utility functions"""
    print("\n=== Testing Utility Functions ===\n")
    
    # Test 1: File metadata function
    print("🔧 Test 1: Test file metadata function...")
    file_metadata_func = create_file_metadata_function()
    metadata = file_metadata_func("/path/to/test/file.txt")
    print(f"File metadata: {metadata}")
    
    # Test 2: Document folder validation
    print("\n🔧 Test 2: Test document folder validation...")
    from pathlib import Path
    
    # Test with existing directory
    current_dir = Path(".")
    try:
        validate_document_folder(current_dir)
        print("✓ Valid directory passed validation")
    except ValueError as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test with non-existent directory
    fake_dir = Path("/non/existent/path")
    try:
        validate_document_folder(fake_dir)
        print("❌ Should have failed for non-existent directory")
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")
    
    print(f"\n✅ Utility functions test completed!")

def test_rag_utils():
    """Run all RAG utilities tests"""
    print("=== Testing RAG Utilities ===\n")
    
    try:
        test_metadata_extractor()
        test_document_processor()
        test_utility_functions()
        print("\n🎉 All RAG utilities tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ RAG utilities test failed: {e}")
        return False

if __name__ == "__main__":
    test_rag_utils()
