#!/usr/bin/env python3
# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Index Deletion Script
Author: Emad Noorizadeh

Deletes the current index by removing the collection from ChromaDB.
Uses the collection name from configuration.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from config.database_config import DatabaseConfig
# Capabilities persistence removed - using semantic only
# BM25 persistence removed - using semantic only

def delete_index(collection_name: str = None, confirm: bool = False) -> Dict[str, Any]:
    """
    Delete the current index by removing the collection from ChromaDB.
    
    Args:
        collection_name: Name of the collection to delete (if None, uses config)
        confirm: Whether to proceed without confirmation prompt
        
    Returns:
        Dict with success status and details
    """
    try:
        # Configuration is loaded automatically
        
        # Get collection name from config if not provided
        if collection_name is None:
            collection_name = get_config("database", "collection_name")
        
        print(f"🗑️  Index Deletion Script")
        print(f"   Collection: {collection_name}")
        print("=" * 50)
        
        # Initialize database configuration
        db_path = get_config("database", "path")
        db_config = DatabaseConfig(db_path=db_path, collection_name=collection_name)
        
        # Check if collection exists
        if not db_config.chroma_collection:
            return {
                "success": False,
                "message": f"Collection '{collection_name}' does not exist or is not initialized",
                "collection_name": collection_name
            }
        
        # Get collection info before deletion
        try:
            collection_info = db_config.get_collection_info()
            doc_count = collection_info.get("total_documents", 0)
            print(f"📊 Collection Info:")
            print(f"   Name: {collection_name}")
            print(f"   Documents: {doc_count}")
            print(f"   Database Path: {db_path}")
        except Exception as e:
            print(f"⚠️  Could not get collection info: {e}")
            doc_count = 0
        
        # Confirmation prompt
        if not confirm:
            print(f"\n⚠️  WARNING: This will permanently delete the collection '{collection_name}'")
            print(f"   This action cannot be undone!")
            print(f"   Documents to be deleted: {doc_count}")
            
            response = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                return {
                    "success": False,
                    "message": "Deletion cancelled by user",
                    "collection_name": collection_name
                }
        
        print(f"\n🗑️  Deleting collection '{collection_name}'...")
        
        # Delete the collection
        try:
            # Clear the collection (remove all documents)
            db_config.clear_collection()
            print(f"✅ Collection '{collection_name}' cleared successfully")
            
            # Note: ChromaDB doesn't have a direct "delete collection" method
            # The collection will be empty but may still exist in metadata
            # This is the standard way to "delete" a collection in ChromaDB
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing collection: {str(e)}",
                "collection_name": collection_name
            }
        
        # Clean up related files
        print(f"🧹 Cleaning up related files...")
        
        # BM25 indices removed - using semantic only
        
        # Capabilities persistence removed - using semantic only
        
        # Clear metadata files
        try:
            metadata_paths = [
                "index/metadata/document_metadata.json",
                "index/metadata/enhanced_chunks.json", 
                "index/metadata/enhanced_metadata_export.json",
                "index/metadata/chunk_metadata.json",
                "index/metadata/complex_metadata.json"
            ]
            
            for path in metadata_paths:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"✅ Removed {path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear some metadata files: {e}")
        
        # Clear index configuration
        try:
            config_path = "config/index_config.json"
            if os.path.exists(config_path):
                os.remove(config_path)
                print(f"✅ Removed index configuration")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear index configuration: {e}")
        
        print(f"\n✅ Index deletion completed successfully!")
        print(f"   Collection '{collection_name}' has been cleared")
        print(f"   Related files have been cleaned up")
        
        return {
            "success": True,
            "message": f"Index '{collection_name}' deleted successfully",
            "collection_name": collection_name,
            "documents_deleted": doc_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during index deletion: {str(e)}",
            "collection_name": collection_name
        }

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Delete RAG index")
    parser.add_argument("--collection", type=str, default=None,
                       help="Collection name to delete (uses config if not specified)")
    parser.add_argument("--yes", "-y", action="store_true",
                       help="Skip confirmation prompt")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Delete the index
    result = delete_index(
        collection_name=args.collection,
        confirm=args.yes
    )
    
    if result["success"]:
        print(f"\n🎉 {result['message']}")
        if "documents_deleted" in result:
            print(f"   Documents deleted: {result['documents_deleted']}")
        return 0
    else:
        print(f"\n❌ {result['message']}")
        return 1

def delete_index_api(collection_name: str = None) -> Dict[str, Any]:
    """
    API function for index deletion
    
    Args:
        collection_name: Name of the collection to delete
        
    Returns:
        Dict with success status and details
    """
    return delete_index(collection_name=collection_name, confirm=True)

if __name__ == "__main__":
    sys.exit(main())
