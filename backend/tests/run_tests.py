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
Test Runner for RAG System
Author: Emad Noorizadeh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_database_config import test_database_config
from test_index_builder import test_index_builder
from test_chunking_config import test_chunking_config
from test_lazy_initialization import test_lazy_initialization
from test_config import test_config_system
from test_metadata_extraction import test_metadata_extraction
from test_rag_utils import test_rag_utils
from test_llm_metadata_extractor import run_llm_metadata_tests
from test_hybrid_metadata_extractor import run_all_hybrid_tests

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting RAG System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Config", test_config_system),
        ("DatabaseConfig", test_database_config),
        ("RAGUtils", test_rag_utils),
        ("LLMMetadataExtractor", run_llm_metadata_tests),
        ("HybridMetadataExtractor", run_all_hybrid_tests),
        ("IndexBuilder", test_index_builder),
        ("ChunkingConfig", test_chunking_config),
        ("LazyInitialization", test_lazy_initialization),
        ("MetadataExtraction", test_metadata_extraction),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} tests...")
        print("-" * 30)
        
        try:
            test_func()
            print(f"✅ {test_name} tests PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} tests FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    tests = {
        "config": test_config_system,
        "database": test_database_config,
        "utils": test_rag_utils,
        "llm": run_llm_metadata_tests,
        "hybrid": run_all_hybrid_tests,
        "index": test_index_builder,
        "chunking": test_chunking_config,
        "lazy": test_lazy_initialization,
        "metadata": test_metadata_extraction,
    }
    
    if test_name not in tests:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(tests.keys())}")
        return False
    
    print(f"🧪 Running {test_name} test...")
    try:
        tests[test_name]()
        print(f"✅ {test_name} test PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name} test FAILED: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
