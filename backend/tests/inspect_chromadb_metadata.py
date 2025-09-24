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
Inspect ChromaDB Metadata Storage
Author: Emad Noorizadeh
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config

def inspect_chromadb_metadata():
    """Inspect how metadata is actually stored in ChromaDB"""
    print("🔍 Inspecting ChromaDB Metadata Storage")
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
        print(f"\n📄 Sample Documents (first 3):")
        print("-" * 50)
        
        # Query to get some documents
        results = collection.get(limit=3, include=['metadatas', 'documents'])
        
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"\n📄 Document {i+1}:")
            print(f"  Text preview: {doc[:100]}...")
            print(f"  Metadata keys: {list(metadata.keys())}")
            
            # Show specific metadata fields
            print(f"  📋 Key Metadata Fields:")
            for key in ['doc_id', 'title', 'doc_type', 'domain', 'authority_score']:
                if key in metadata:
                    print(f"    {key}: {metadata[key]}")
            
            # Show converted fields
            print(f"  🔄 Converted Fields:")
            for key in ['product_entities', 'categories', 'section_path']:
                if key in metadata:
                    try:
                        parsed = json.loads(metadata[key])
                        print(f"    {key}: {parsed}")
                    except:
                        print(f"    {key}: {metadata[key]} (raw)")
            
            print(f"  📊 Chunk Info:")
            for key in ['chunk_id', 'start_line', 'end_line', 'token_count', 'has_numbers', 'has_currency']:
                if key in metadata:
                    print(f"    {key}: {metadata[key]}")
        
        # Show metadata field types
        print(f"\n🔍 Metadata Field Analysis:")
        print("-" * 50)
        
        # Get all unique metadata keys
        all_keys = set()
        for metadata in results['metadatas']:
            all_keys.update(metadata.keys())
        
        print(f"Total unique metadata fields: {len(all_keys)}")
        
        # Analyze field types
        field_types = {}
        for metadata in results['metadatas']:
            for key, value in metadata.items():
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(type(value).__name__)
        
        print(f"\nField Type Analysis:")
        for key, types in sorted(field_types.items()):
            print(f"  {key}: {', '.join(types)}")
        
        # Show JSON fields
        print(f"\nJSON Serialized Fields:")
        json_fields = []
        for key, types in field_types.items():
            if 'str' in types and any('[' in str(metadata.get(key, '')) for metadata in results['metadatas']):
                json_fields.append(key)
        
        for field in json_fields:
            print(f"  {field}: JSON string")
            # Show example
            for metadata in results['metadatas']:
                if field in metadata and '[' in str(metadata[field]):
                    try:
                        parsed = json.loads(metadata[field])
                        print(f"    Example: {parsed}")
                        break
                    except:
                        print(f"    Example: {metadata[field]}")
                        break
        
        print(f"\n✅ ChromaDB metadata inspection completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_chromadb_metadata()
