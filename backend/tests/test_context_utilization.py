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
Test what context utilization data we get from the LLM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
import json

def test_context_utilization():
    """Test what context utilization data we get from the LLM"""
    print("🧪 Testing Context Utilization from LLM")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Test question
        question = "what is tier?"
        print(f"\nQuestion: '{question}'")
        
        # Retrieve documents
        print("Retrieving documents...")
        nodes = rag.retrieve_documents(question, n_results=3)
        print(f"Retrieved {len(nodes)} chunks")
        
        # Generate response
        print("Generating RAG response...")
        response = rag.generate_response(question, nodes)
        
        print(f"\nAnswer: {response.get('answer', 'N/A')[:100]}...")
        
        # Check what context utilization data we get
        metrics = response.get('metrics', {})
        print(f"\n📊 RAG Metrics:")
        print(f"  - Answer Type: {metrics.get('answer_type', 'N/A')}")
        print(f"  - Confidence: {metrics.get('confidence', 'N/A')}")
        print(f"  - Abstained: {metrics.get('abstained', 'N/A')}")
        print(f"  - Faithfulness Score: {metrics.get('faithfulness_score', 'N/A')}")
        print(f"  - Completeness Score: {metrics.get('completeness_score', 'N/A')}")
        print(f"  - Missing: {metrics.get('missing', 'N/A')}")
        print(f"  - Reasoning Notes: {metrics.get('reasoning_notes', 'N/A')}")
        
        # Check context utilization specifically
        context_utilization = metrics.get('context_utilization', [])
        print(f"\n🔍 Context Utilization:")
        print(f"  - Type: {type(context_utilization)}")
        print(f"  - Length: {len(context_utilization) if isinstance(context_utilization, list) else 'N/A'}")
        
        if isinstance(context_utilization, list) and context_utilization:
            print(f"  - Content:")
            for i, context in enumerate(context_utilization):
                print(f"    [{i+1}] {context[:100]}...")
        else:
            print(f"  - Value: {context_utilization}")
        
        # Check evidence
        evidence = metrics.get('evidence', [])
        print(f"\n📋 Evidence:")
        print(f"  - Type: {type(evidence)}")
        print(f"  - Length: {len(evidence) if isinstance(evidence, list) else 'N/A'}")
        if isinstance(evidence, list) and evidence:
            print(f"  - Content: {evidence}")
        
        # Full response for debugging
        print(f"\n🔍 Full RAG Response:")
        print(json.dumps(response, indent=2, default=str))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_utilization()
