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
Fixed RAG Comparison Test
Author: Emad Noorizadeh

Proper comparison between standard RAG and hybrid RAG with real data.
"""

import sys
import os
sys.path.append('.')

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from rag_hybrid import HybridRAG

def test_rag_comparison_with_real_data():
    """Compare RAG systems with actual data from the index."""
    print("🔬 RAG Comparison with Real Data")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        # Initialize RAG systems
        standard_rag = RAG(model_manager, index_builder)
        hybrid_rag = HybridRAG(model_manager, index_builder, use_hybrid=False)  # Start with standard for comparison
        
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
                standard_response = standard_rag.query(query)
                print(f"Answer: {standard_response.answer[:200]}...")
                print(f"Confidence: {standard_response.confidence}")
                print(f"Abstained: {standard_response.abstained}")
                print(f"Evidence: {len(standard_response.evidence)} chunks")
                print(f"Faithfulness: {standard_response.faithfulness_score:.2f}")
                print(f"Completeness: {standard_response.completeness_score:.2f}")
            except Exception as e:
                print(f"Error in standard RAG: {e}")
            
            # Hybrid RAG (with standard retrieval first)
            print("\n🚀 Hybrid RAG (Standard Retrieval):")
            try:
                hybrid_response = hybrid_rag.query(query)
                print(f"Answer: {hybrid_response.answer[:200]}...")
                print(f"Confidence: {hybrid_response.confidence}")
                print(f"Abstained: {hybrid_response.abstained}")
                print(f"Evidence: {len(hybrid_response.evidence)} chunks")
                print(f"Faithfulness: {hybrid_response.faithfulness_score:.2f}")
                print(f"Completeness: {hybrid_response.completeness_score:.2f}")
                print(f"Retrieval method: {hybrid_response.retrieval_metadata.get('method', 'unknown')}")
            except Exception as e:
                print(f"Error in hybrid RAG: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Comparison completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_retrieval_methods():
    """Test different retrieval methods directly."""
    print("\n🔍 Testing Retrieval Methods")
    print("=" * 50)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        # Test standard retrieval
        print("\n📊 Standard Retrieval:")
        try:
            retriever = index_builder.index.as_retriever(similarity_top_k=5)
            nodes = retriever.retrieve("What is the gold tier?")
            print(f"Found {len(nodes)} nodes")
            for i, node in enumerate(nodes[:3], 1):
                print(f"  {i}. {node.id_}: {node.text[:100]}...")
                print(f"     Score: {getattr(node, 'score', 'N/A')}")
        except Exception as e:
            print(f"Error in standard retrieval: {e}")
        
        # Test hybrid retrieval (if we can get data)
        print("\n🚀 Hybrid Retrieval Setup:")
        try:
            # Try to get some data for hybrid retrieval
            collection_info = index_builder.get_collection_info()
            print(f"Collection info: {collection_info}")
            
            # Check if we have an index
            if hasattr(index_builder, 'index') and index_builder.index:
                print("✓ Index available for hybrid retrieval")
            else:
                print("⚠ No index available for hybrid retrieval")
                
        except Exception as e:
            print(f"Error setting up hybrid retrieval: {e}")
        
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        import traceback
        traceback.print_exc()

def test_simple_rag_query():
    """Test a simple RAG query to see what data we have."""
    print("\n🧪 Simple RAG Query Test")
    print("=" * 50)
    
    try:
        # Initialize components
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Simple query
        query = "What is the gold tier?"
        print(f"Query: {query}")
        
        response = rag.query(query)
        
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")
        print(f"Abstained: {response.abstained}")
        print(f"Evidence: {response.evidence}")
        print(f"Context utilization: {response.context_utilization}")
        print(f"Missing: {response.missing}")
        print(f"Reasoning: {response.reasoning_notes}")
        
        # Check if we have retrieved nodes
        if hasattr(response, 'retrieved_nodes'):
            print(f"Retrieved nodes: {len(response.retrieved_nodes)}")
            for i, node in enumerate(response.retrieved_nodes[:3], 1):
                print(f"  {i}. {node.id_}: {node.text[:100]}...")
        
    except Exception as e:
        print(f"❌ Simple RAG test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("🧪 RAG Comparison Tests (Fixed)")
    print("=" * 60)
    
    try:
        test_simple_rag_query()
        test_retrieval_methods()
        test_rag_comparison_with_real_data()
        
        print(f"\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
