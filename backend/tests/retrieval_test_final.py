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
Final retrieval test with comprehensive results
Author: Emad Noorizadeh
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from index_builder import IndexBuilder

def test_retrieval_comprehensive():
    """Comprehensive retrieval test with detailed results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comprehensive_retrieval_results_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write("=== COMPREHENSIVE RAG RETRIEVAL TEST RESULTS ===\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        
        try:
            # Initialize system
            f.write("🔧 SYSTEM INITIALIZATION\n")
            f.write("-" * 30 + "\n")
            f.write("Initializing ModelManager...\n")
            model_manager = ModelManager()
            f.write(f"Model status: {model_manager.list_models()}\n")
            f.write("✅ ModelManager initialized\n\n")
            
            f.write("Initializing IndexBuilder...\n")
            index_builder = IndexBuilder(model_manager, collection_name="comprehensive_test")
            f.write("✅ IndexBuilder initialized\n\n")
            
            # Build index
            f.write("📚 INDEX BUILDING\n")
            f.write("-" * 30 + "\n")
            data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            f.write(f"Data folder: {data_folder}\n")
            
            # Check data files
            if os.path.exists(data_folder):
                files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]
                f.write(f"Found {len(files)} text files:\n")
                for file in files:
                    f.write(f"  - {file}\n")
            f.write("\n")
            
            f.write("Building index...\n")
            result = index_builder.build_index_from_folder(data_folder)
            f.write(f"Build result: {result}\n")
            
            if 'processed_files' in result and result['processed_files'] > 0:
                f.write("✅ Index built successfully!\n")
                f.write(f"  - Files processed: {result['processed_files']}\n")
                f.write(f"  - Total chunks: {result['total_chunks']}\n")
                f.write(f"  - Collection size: {result['collection_size']}\n")
                f.write(f"  - Errors: {result.get('errors', [])}\n\n")
                
                # Test retrieval
                f.write("🔍 RETRIEVAL TESTING\n")
                f.write("-" * 30 + "\n")
                
                test_queries = [
                    "What is the main topic?",
                    "Tell me about banking services",
                    "What are the key benefits?",
                    "How does the rewards program work?",
                    "What are the account fees?",
                    "Tell me about Preferred Rewards"
                ]
                
                for i, query in enumerate(test_queries, 1):
                    f.write(f"\nQuery {i}: '{query}'\n")
                    f.write("-" * 40 + "\n")
                    
                    try:
                        search_results = index_builder.search(query, n_results=3)
                        f.write(f"Found {len(search_results)} results:\n\n")
                        
                        for j, result in enumerate(search_results, 1):
                            f.write(f"Result {j}:\n")
                            f.write(f"  Similarity Score: {result['similarity']:.4f}\n")
                            f.write(f"  Text Preview: {result['text'][:200]}...\n")
                            f.write(f"  Source: {result['metadata'].get('source', 'unknown')}\n")
                            f.write(f"  Categories: {result['metadata'].get('categories', 'unknown')}\n")
                            f.write(f"  Word Count: {result['metadata'].get('word_count', 'unknown')}\n")
                            f.write(f"  Has Headings: {result['metadata'].get('headings', 'unknown')}\n")
                            f.write(f"  Processed At: {result['metadata'].get('processed_at', 'unknown')}\n")
                            f.write("\n")
                            
                    except Exception as e:
                        f.write(f"❌ Search error: {e}\n\n")
                
                # Collection info
                f.write("📋 COLLECTION INFORMATION\n")
                f.write("-" * 30 + "\n")
                try:
                    info = index_builder.get_collection_info()
                    f.write(f"Collection name: {info.get('collection_name', 'unknown')}\n")
                    f.write(f"Total documents: {info.get('total_documents', 'unknown')}\n")
                except Exception as e:
                    f.write(f"Error getting collection info: {e}\n")
                
                f.write(f"\n✅ COMPREHENSIVE RETRIEVAL TEST COMPLETED\n")
                f.write(f"Test completed at: {datetime.now().isoformat()}\n")
                
            else:
                f.write("❌ Index build failed - no files processed\n")
                
        except Exception as e:
            f.write(f"❌ Test failed with error: {e}\n")
            import traceback
            f.write(f"Traceback: {traceback.format_exc()}\n")
    
    print(f"📄 Comprehensive retrieval test results saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    test_retrieval_comprehensive()
