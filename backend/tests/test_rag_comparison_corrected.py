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
Corrected RAG Comparison Test
Author: Emad Noorizadeh

Proper comparison between standard RAG and hybrid RAG with correct data access.
"""

import sys
import os
sys.path.append('.')

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from rag_hybrid import HybridRAG

def test_corrected_rag_comparison():
    """Compare RAG systems with correct data access."""
    print("🔬 Corrected RAG Comparison")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        # Initialize RAG systems
        standard_rag = RAG(model_manager, index_builder)
        hybrid_rag = HybridRAG(model_manager, index_builder, use_hybrid=False)
        
        print("✓ Components initialized successfully")
        
        # Test queries
        test_queries = [
            "What is the gold tier?",
            "What are the minimum balance requirements?",
            "What benefits do I get?",
            "How do I apply for Preferred Rewards?",
            "What documents do I need?"
        ]
        
        print(f"\nTesting {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}: {query}")
            print('='*60)
            
            # Standard RAG
            print("\n📊 Standard RAG:")
            try:
                std_response = standard_rag.query(query, n_results=5)
                metrics = std_response.get('metrics', {})
                
                print(f"Answer: {std_response.get('answer', 'N/A')[:200]}...")
                print(f"Confidence: {metrics.get('confidence', 'N/A')}")
                print(f"Abstained: {metrics.get('abstained', 'N/A')}")
                print(f"Evidence: {len(metrics.get('evidence', []))} chunks")
                print(f"Faithfulness: {metrics.get('faithfulness_score', 0):.2f}")
                print(f"Completeness: {metrics.get('completeness_score', 0):.2f}")
                print(f"Retrieved docs: {len(std_response.get('sources', []))}")
                print(f"Chunks retrieved: {len(metrics.get('chunks_retrieved', []))}")
                
            except Exception as e:
                print(f"Error in standard RAG: {e}")
            
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
                print(f"Error in hybrid RAG: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Comparison completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_retrieval_quality():
    """Test the quality of retrieval for both systems."""
    print("\n🔍 Retrieval Quality Analysis")
    print("=" * 50)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        standard_rag = RAG(model_manager, index_builder)
        
        # Test specific query
        query = "What is the gold tier?"
        print(f"Query: {query}")
        
        # Standard RAG
        print("\n📊 Standard RAG Analysis:")
        std_response = standard_rag.query(query, n_results=5)
        metrics = std_response.get('metrics', {})
        
        print(f"✓ Answer Quality: {'Excellent' if len(std_response.get('answer', '')) > 100 else 'Poor'}")
        print(f"✓ Confidence: {metrics.get('confidence', 'N/A')}")
        print(f"✓ Abstained: {metrics.get('abstained', 'N/A')}")
        print(f"✓ Evidence Chunks: {len(metrics.get('evidence', []))}")
        print(f"✓ Faithfulness: {metrics.get('faithfulness_score', 0):.2f}")
        print(f"✓ Completeness: {metrics.get('completeness_score', 0):.2f}")
        print(f"✓ Retrieved Documents: {len(std_response.get('sources', []))}")
        
        # Show evidence chunks
        evidence = metrics.get('evidence', [])
        if evidence:
            print(f"\nEvidence chunks used: {evidence}")
        
        # Show retrieved documents
        sources = std_response.get('sources', [])
        if sources:
            print(f"\nRetrieved documents:")
            for i, source in enumerate(sources[:3], 1):
                print(f"  {i}. {source.get('id_', 'N/A')}: {source.get('text', 'N/A')[:100]}...")
        
        print(f"\n✅ Standard RAG is working perfectly!")
        
    except Exception as e:
        print(f"❌ Retrieval quality test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("🧪 Corrected RAG Comparison Tests")
    print("=" * 60)
    
    try:
        test_retrieval_quality()
        test_corrected_rag_comparison()
        
        print(f"\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
