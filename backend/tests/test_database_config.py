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
Test script for DatabaseConfig module
Author: Emad Noorizadeh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database_config import DatabaseConfig

def test_database_config():
    """Test the database configuration functionality"""
    print("=== Testing DatabaseConfig Module ===\n")
    
    # Test 1: Initialize database config
    print("🔧 Test 1: Initializing DatabaseConfig...")
    try:
        db_config = DatabaseConfig(db_path="./test_chroma_db", collection_name="test_collection")
        print("✅ DatabaseConfig initialized successfully")
    except Exception as e:
        print(f"❌ DatabaseConfig initialization failed: {e}")
        return
    
    # Test 2: Health check
    print("\n🔧 Test 2: Health check...")
    health = db_config.health_check()
    print(f"Health status: {health['status']}")
    if health['status'] == 'healthy':
        print(f"  - Database path: {health['database_path']}")
        print(f"  - Collection: {health['collection_name']}")
        print(f"  - Document count: {health['document_count']}")
        print(f"  - Client status: {health['client_status']}")
    else:
        print(f"  - Error: {health['message']}")
    
    # Test 3: Collection info
    print("\n🔧 Test 3: Collection info...")
    info = db_config.get_collection_info()
    print(f"Collection info: {info}")
    
    # Test 4: List documents (should be empty initially)
    print("\n🔧 Test 4: List documents...")
    documents = db_config.list_documents(limit=5)
    print(f"Found {len(documents)} documents")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. ID: {doc['id']}")
        print(f"     Text: {doc['text'][:50]}...")
        print(f"     Metadata: {doc['metadata']}")
    
    # Test 5: Clear collection
    print("\n🔧 Test 5: Clear collection...")
    db_config.clear_collection()
    print("✅ Collection cleared")
    
    # Test 6: Final health check
    print("\n🔧 Test 6: Final health check...")
    final_health = db_config.health_check()
    print(f"Final health status: {final_health['status']}")
    print(f"Final document count: {final_health['document_count']}")
    
    print(f"\n✅ DatabaseConfig test completed!")

if __name__ == "__main__":
    test_database_config()
