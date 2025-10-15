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
Test Chunking Configuration
Author: Emad Noorizadeh

Test chunking configuration and utilities.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..utils.chunking_utils import (
    get_chunking_config,
    set_chunking_config,
    get_word_count_splitter,
    get_effective_chunk_sizes,
    print_chunking_info
)

class TestChunkingConfig(unittest.TestCase):
    """Test chunking configuration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "chunking": {
                "word_count_ratio": 0.75
            }
        }
    
    def test_get_chunking_config_default(self):
        """Test getting default chunking config"""
        with patch('os.path.exists', return_value=False):
            config = get_chunking_config()
            self.assertEqual(config["word_count_ratio"], 0.75)
    
    def test_get_chunking_config_from_file(self):
        """Test getting chunking config from file"""
        mock_config = json.dumps(self.test_config)
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_config)):
            config = get_chunking_config()
            self.assertEqual(config["word_count_ratio"], 0.75)
    
    def test_set_chunking_config(self):
        """Test setting chunking config"""
        mock_config = {"index_id": "test"}
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_config))), \
             patch('json.dump') as mock_dump:
            result = set_chunking_config(True, 0.8)
            self.assertTrue(result)
            mock_dump.assert_called_once()
    
    def test_word_count_splitter(self):
        """Test word count splitter"""
        splitter = get_word_count_splitter(5, 2)  # 5 words, 2 overlap
        text = "This is a test sentence with more words than the chunk size"
        chunks = splitter(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 1)
        
        # Check that chunks don't exceed word limit
        for chunk in chunks:
            word_count = len(chunk.split())
            self.assertLessEqual(word_count, 5)
    
    
    def test_get_effective_chunk_sizes_word_count(self):
        """Test effective chunk sizes for word count mode"""
        with patch('utils.chunking_utils.get_chunking_config', return_value={
            "word_count_ratio": 0.75
        }):
            sizes = get_effective_chunk_sizes(1024, 20)
            self.assertEqual(sizes["mode"], "word_count")
            self.assertEqual(sizes["chunk_size"], 768)  # 1024 * 0.75
            self.assertEqual(sizes["chunk_overlap"], 15)  # 20 * 0.75
            self.assertEqual(sizes["unit"], "words")
            self.assertEqual(sizes["ratio"], 0.75)

class TestChunkingIntegration(unittest.TestCase):
    """Test chunking integration with index builder"""
    
    def test_chunking_config_loading(self):
        """Test that chunking config is loaded correctly"""
        # This would test the actual integration with index_builder
        # For now, just test that the config can be loaded
        config = get_chunking_config()
        self.assertIn("word_count_ratio", config)

def run_chunking_tests():
    """Run chunking tests"""
    print("🧪 Running Chunking Configuration Tests")
    print("=" * 40)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestChunkingConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestChunkingIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n✅ All chunking tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_chunking_tests()