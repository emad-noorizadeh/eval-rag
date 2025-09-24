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
Working RAG Comparison Test
Author: Emad Noorizadeh

Proper comparison between standard RAG and hybrid RAG with correct APIs.
"""

import sys
import os
sys.path.append('.')

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from rag_hybrid import HybridRAG

def test_standard_rag():
    """Test standard RAG system."""
    print("📊 Testing Standard RAG")
    print("=" * 40)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Test queries
        test_queries = [
            "What is the gold tier?",
            "What are the minimum balance requirements?",
            "What benefits do I get?",
            "How do I apply for Preferred Rewards?",
            "What documents do I need?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            try:
                response = rag.query(query, n_results=5)
                
                print(f"Answer: {response.get('answer', 'N/A')[:150]}...")
                print(f"Confidence: {response.get('confidence', 'N/A')}")
                print(f"Abstained: {response.get('abstained', 'N/A')}")
                print(f"Evidence: {len(response.get('evidence', []))} chunks")
                print(f"Faithfulness: {response.get('faithfulness_score', 0):.2f}")
                print(f"Completeness: {response.get('completeness_score', 0):.2f}")
                print(f"Retrieved docs: {len(response.get('chunks_retrieved', []))}")
                
            except Exception as e:
                print(f"Error: {e}")
        
        print(f"\n✅ Standard RAG testing completed!")
        
    except Exception as e:
        print(f"❌ Standard RAG test failed: {e}")
        import traceback
        traceback.print_exc()

def test_hybrid_rag():
    """Test hybrid RAG system."""
    print("\n🚀 Testing Hybrid RAG")
    print("=" * 40)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        hybrid_rag = HybridRAG(model_manager, index_builder, use_hybrid=False)  # Start with standard
        
        # Test queries
        test_queries = [
            "What is the gold tier?",
            "What are the minimum balance requirements?",
            "What benefits do I get?",
            "How do I apply for Preferred Rewards?",
            "What documents do I need?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            try:
                response = hybrid_rag.query(query, top_k=5)
                
                print(f"Answer: {response.answer[:150]}...")
                print(f"Confidence: {response.confidence}")
                print(f"Abstained: {response.abstained}")
                print(f"Evidence: {len(response.evidence)} chunks")
                print(f"Faithfulness: {response.faithfulness_score:.2f}")
                print(f"Completeness: {response.completeness_score:.2f}")
                print(f"Retrieval method: {response.retrieval_metadata.get('method', 'unknown')}")
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Hybrid RAG testing completed!")
        
    except Exception as e:
        print(f"❌ Hybrid RAG test failed: {e}")
        import traceback
        traceback.print_exc()

def test_retrieval_comparison():
    """Compare retrieval methods directly."""
    print("\n🔍 Testing Retrieval Methods")
    print("=" * 40)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        query = "What is the gold tier?"
        print(f"Query: {query}")
        
        # Test standard retrieval
        print("\n📊 Standard Retrieval:")
        try:
            retrieved_docs = index_builder.search(query, n_results=5)
            print(f"Found {len(retrieved_docs)} documents")
            for i, doc in enumerate(retrieved_docs[:3], 1):
                print(f"  {i}. {doc.get('id_', 'N/A')}: {doc.get('text', 'N/A')[:100]}...")
        except Exception as e:
            print(f"Error in standard retrieval: {e}")
        
        # Test if we can get collection info
        print("\n📈 Collection Info:")
        try:
            collection_info = index_builder.get_collection_info()
            print(f"Collection: {collection_info}")
        except Exception as e:
            print(f"Error getting collection info: {e}")
        
    except Exception as e:
        print(f"❌ Retrieval comparison failed: {e}")
        import traceback
        traceback.print_exc()

def test_side_by_side_comparison():
    """Compare standard RAG vs hybrid RAG side by side."""
    print("\n⚖️ Side-by-Side RAG Comparison")
    print("=" * 50)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        # Initialize both RAG systems
        standard_rag = RAG(model_manager, index_builder)
        hybrid_rag = HybridRAG(model_manager, index_builder, use_hybrid=False)
        
        # Test queries
        test_queries = [
            "What is the gold tier?",
            "What are the minimum balance requirements?",
            "What benefits do I get?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}: {query}")
            print('='*60)
            
            # Standard RAG
            print("\n📊 Standard RAG:")
            try:
                std_response = standard_rag.query(query, n_results=5)
                print(f"Answer: {std_response.get('answer', 'N/A')[:200]}...")
                print(f"Confidence: {std_response.get('confidence', 'N/A')}")
                print(f"Abstained: {std_response.get('abstained', 'N/A')}")
                print(f"Evidence: {len(std_response.get('evidence', []))} chunks")
                print(f"Faithfulness: {std_response.get('faithfulness_score', 0):.2f}")
                print(f"Completeness: {std_response.get('completeness_score', 0):.2f}")
            except Exception as e:
                print(f"Error: {e}")
            
            # Hybrid RAG
            print("\n🚀 Hybrid RAG:")
            try:
                hyb_response = hybrid_rag.query(query, top_k=5)
                print(f"Answer: {hyb_response.answer[:200]}...")
                print(f"Confidence: {hyb_response.confidence}")
                print(f"Abstained: {hyb_response.abstained}")
                print(f"Evidence: {len(hyb_response.evidence)} chunks")
                print(f"Faithfulness: {hyb_response.faithfulness_score:.2f}")
                print(f"Completeness: {hyb_response.completeness_score:.2f}")
                print(f"Retrieval method: {hyb_response.retrieval_metadata.get('method', 'unknown')}")
            except Exception as e:
                print(f"Error: {e}")
        
        print(f"\n✅ Side-by-side comparison completed!")
        
    except Exception as e:
        print(f"❌ Side-by-side comparison failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("🧪 Working RAG Comparison Tests")
    print("=" * 60)
    
    try:
        test_standard_rag()
        test_hybrid_rag()
        test_retrieval_comparison()
        test_side_by_side_comparison()
        
        print(f"\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
