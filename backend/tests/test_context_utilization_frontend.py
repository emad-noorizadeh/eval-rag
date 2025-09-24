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
Test context utilization data being sent to frontend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from rag import RAG
from chat_agent_v2 import ChatAgentV2
from session_manager import session_manager
import json

def test_context_utilization_frontend():
    """Test context utilization data being sent to frontend"""
    print("🧪 Testing Context Utilization for Frontend")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        rag = RAG(model_manager, index_builder)
        
        # Create chat agent V2
        print("Creating ChatAgentV2...")
        chat_agent_v2 = ChatAgentV2(rag, model_manager, session_manager)
        
        # Test question
        print("\nTesting question: 'what is tier?'")
        response = chat_agent_v2.chat(
            message="what is tier?",
            session_id="test-context-utilization-frontend",
            conversation_history=[]
        )
        
        print(f"Answer: {response.get('answer', 'N/A')[:100]}...")
        
        # Check metrics
        metrics = response.get('metrics', {})
        print(f"\n📊 Metrics sent to frontend:")
        print(f"  - Answer Type: {metrics.get('answer_type', 'N/A')}")
        print(f"  - Confidence: {metrics.get('confidence', 'N/A')}")
        print(f"  - Faithfulness Score: {metrics.get('faithfulness_score', 'N/A')}")
        print(f"  - Completeness Score: {metrics.get('completeness_score', 'N/A')}")
        
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
        
        # Check if it's the new format (array) or legacy format (number)
        if isinstance(context_utilization, list):
            print("✅ Using new format: Array of context snippets")
        elif isinstance(context_utilization, (int, float)):
            print("⚠️ Using legacy format: Number")
        else:
            print(f"❌ Unknown format: {type(context_utilization)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_utilization_frontend()
