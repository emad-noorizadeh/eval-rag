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
Index Creation Script
Author: Emad Noorizadeh

Simplified script to create semantic-only index using IndexBuilder.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from index_builder import IndexBuilder
from model_manager import ModelManager

def main():
    parser = argparse.ArgumentParser(description="Setup index for RAG system")
    parser.add_argument("--retrieval-method", choices=["semantic"], 
                       default="semantic", help="Target retrieval method")
    parser.add_argument("--overwrite", action="store_true", 
                       help="Overwrite existing index")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check compatibility, don't build")
    parser.add_argument("--source-folder", default="data",
                       help="Source folder for documents")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    print(f"🚀 Index Creation Script")
    print(f"   Target Method: {args.retrieval_method}")
    print(f"   Source Folder: {args.source_folder}")
    print(f"   Overwrite: {args.overwrite}")
    print("=" * 50)
    
    # Initialize index builder
    model_manager = ModelManager()
    index_builder = IndexBuilder(model_manager)
    
    # Get current status
    collection_info = index_builder.get_collection_info()
    print(f"📊 Current Index Status:")
    print(f"   Exists: {collection_info.get('documents', 0) > 0}")
    print(f"   Capabilities: {collection_info.get('capabilities', ['semantic'])}")
    print(f"   Documents: {collection_info.get('documents', 0)}")
    print(f"   Chunks: {collection_info.get('chunks', 0)}")
    print()
    
    if args.check_only:
        # Just check if semantic is supported (always true)
        print(f"🔍 Compatibility Check:")
        print(f"   Compatible: True")
        print(f"   Missing: []")
        print(f"   Can Enhance: False")
        print(f"   Requires Rebuild: False")
        print(f"   Message: Semantic retrieval is fully supported")
        return 0
    
    # Check if index exists and overwrite is needed
    if collection_info.get('total_documents', 0) > 0 and not args.overwrite:
        print(f"✅ Index already exists with {collection_info.get('total_documents', 0)} documents")
        print("   Use --overwrite to rebuild the index")
        return 0
    
    # Build or rebuild index
    if args.overwrite and collection_info.get('total_documents', 0) > 0:
        print("🔄 Rebuilding index...")
        index_builder.clear_index()
    
    print(f"🔨 Building index from {args.source_folder}...")
    result = index_builder.build_index_from_folder(args.source_folder)
    
    if result:
        print("✅ Index setup completed successfully!")
        
        # Show final status
        final_info = index_builder.get_collection_info()
        print(f"📊 Final Index Status:")
        print(f"   Documents: {final_info.get('documents', 0)}")
        print(f"   Chunks: {final_info.get('chunks', 0)}")
        print(f"   Capabilities: {final_info.get('capabilities', ['semantic'])}")
        print(f"   Supports Semantic: True")
        
        return 0
    else:
        print("❌ Index setup failed")
        return 1

def create_index_api(retrieval_method: str, overwrite: bool = False, source_folder: str = "data") -> dict:
    """API function for creating index"""
    try:
        model_manager = ModelManager()
        index_builder = IndexBuilder(model_manager)
        
        # Clear existing index if overwrite requested
        if overwrite:
            index_builder.clear_index()
        
        # Build index from source folder
        result = index_builder.build_index_from_folder(source_folder)
        
        return {
            "success": True,
            "message": "Index built successfully",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

if __name__ == "__main__":
    sys.exit(main())