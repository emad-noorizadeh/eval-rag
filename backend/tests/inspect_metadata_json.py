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

#!/usr/bin/env python3
"""
Inspect Metadata JSON Validity
Author: Emad Noorizadeh
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config

def inspect_metadata_json():
    """Inspect metadata for JSON validity and Python objects"""
    print("🔍 Inspecting Metadata JSON Validity")
    print("=" * 50)
    
    try:
        # Initialize database connection
        db_config = DatabaseConfig()
        collection = db_config.get_chroma_collection()
        
        # Get collection info
        count = collection.count()
        print(f"📊 Collection: {collection.name}")
        print(f"📊 Total documents: {count}")
        
        if count == 0:
            print("ℹ No documents in collection")
            return
        
        # Get a sample of documents
        print(f"\n📄 Sample Documents (first 2):")
        print("-" * 50)
        
        # Query to get some documents
        results = collection.get(limit=2, include=['metadatas', 'documents'])
        
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"\n📄 Document {i+1}:")
            print(f"  Text preview: {doc[:100]}...")
            
            # Check each metadata field for JSON validity
            print(f"  🔍 Metadata Field Analysis:")
            json_fields = []
            invalid_json_fields = []
            python_object_fields = []
            
            for key, value in metadata.items():
                print(f"    {key}: {type(value).__name__} = {repr(value)[:100]}")
                
                # Check if it's a JSON string
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    try:
                        parsed = json.loads(value)
                        json_fields.append(key)
                        print(f"      ✅ Valid JSON: {parsed}")
                    except json.JSONDecodeError as e:
                        invalid_json_fields.append((key, value, str(e)))
                        print(f"      ❌ Invalid JSON: {e}")
                
                # Check for Python objects
                elif isinstance(value, (list, dict, tuple, set)):
                    python_object_fields.append((key, value, type(value).__name__))
                    print(f"      ⚠️  Python object: {type(value).__name__}")
                
                # Check for None values
                elif value is None:
                    print(f"      ℹ️  None value")
                
                # Check for other types
                else:
                    print(f"      ✅ Simple type: {type(value).__name__}")
            
            # Summary for this document
            print(f"\n  📊 Summary:")
            print(f"    JSON fields: {len(json_fields)} - {json_fields}")
            print(f"    Invalid JSON: {len(invalid_json_fields)}")
            print(f"    Python objects: {len(python_object_fields)}")
            
            if invalid_json_fields:
                print(f"    ❌ Invalid JSON fields:")
                for key, value, error in invalid_json_fields:
                    print(f"      {key}: {error}")
                    print(f"        Value: {repr(value)[:200]}")
            
            if python_object_fields:
                print(f"    ⚠️  Python object fields:")
                for key, value, obj_type in python_object_fields:
                    print(f"      {key}: {obj_type}")
                    print(f"        Value: {repr(value)[:200]}")
        
        print(f"\n✅ Metadata JSON inspection completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_metadata_json()
