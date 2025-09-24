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
Simple retrieval test with output
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder

def test_retrieval():
    """Test retrieval functionality and save results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"retrieval_test_results_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write("=== RAG RETRIEVAL TEST RESULTS ===\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n\n")
        
        try:
            f.write("🔧 Initializing ModelManager...\n")
            model_manager = ModelManager()
            f.write(f"📊 Model status: {model_manager.list_models()}\n\n")
            
            f.write("🔧 Initializing IndexBuilder...\n")
            index_builder = IndexBuilder(model_manager, collection_name="retrieval_test")
            f.write("✅ IndexBuilder initialized\n\n")
            
            # Build index
            data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            f.write(f"📚 Building index from: {data_folder}\n")
            
            result = index_builder.build_index_from_folder(data_folder)
            f.write(f"Index build result: {result}\n\n")
            
            if 'files_processed' in result:
                f.write("✅ Index built successfully!\n")
                f.write(f"📊 Results:\n")
                f.write(f"  - Files processed: {result['files_processed']}\n")
                f.write(f"  - Total chunks: {result['total_chunks']}\n")
                f.write(f"  - Collection size: {result['collection_size']}\n\n")
                
                # Test retrieval
                f.write("🔍 Testing retrieval functionality...\n")
                test_queries = [
                    "What is the main topic?",
                    "Tell me about banking services",
                    "What are the key benefits?",
                    "How does the rewards program work?"
                ]
                
                for query in test_queries:
                    f.write(f"\n🔎 Query: '{query}'\n")
                    try:
                        search_results = index_builder.search(query, n_results=3)
                        f.write(f"  Found {len(search_results)} results:\n")
                        
                        for i, result in enumerate(search_results):
                            f.write(f"    {i+1}. Similarity: {result['similarity']:.3f}\n")
                            f.write(f"       Text: {result['text'][:150]}...\n")
                            f.write(f"       Source: {result['metadata'].get('source', 'unknown')}\n")
                            f.write(f"       Categories: {result['metadata'].get('categories', 'unknown')}\n")
                            f.write(f"       Word count: {result['metadata'].get('word_count', 'unknown')}\n")
                    except Exception as e:
                        f.write(f"  ❌ Search error: {e}\n")
                
                f.write(f"\n✅ Retrieval test completed successfully!\n")
            else:
                f.write(f"❌ Index build failed: {result}\n")
                
        except Exception as e:
            f.write(f"❌ Test failed with error: {e}\n")
            import traceback
            f.write(f"Traceback: {traceback.format_exc()}\n")
    
    print(f"📄 Retrieval test results saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    test_retrieval()
