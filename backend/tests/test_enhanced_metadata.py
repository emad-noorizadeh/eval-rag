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
Test Enhanced Metadata System
Author: Emad Noorizadeh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager
from index_builder import IndexBuilder
from processors.enhanced_metadata_extractor import EnhancedMetadataExtractor, DocumentMetadata, ChunkMetadata

def test_enhanced_metadata_system():
    """Test the enhanced metadata extraction system"""
    print("🧪 Testing Enhanced Metadata System")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        model_manager = ModelManager()
        metadata_extractor = EnhancedMetadataExtractor(model_manager)
        
        # Test document metadata extraction
        print("\n" + "="*50)
        print("TESTING DOCUMENT METADATA EXTRACTION")
        print("="*50)
        
        # Sample document text
        sample_text = """
        Bank of America Preferred Rewards Program
        
        The Bank of America Preferred Rewards program offers real benefits and rewards on your everyday banking and investing. 
        There are four tiers in the Preferred Rewards program: Gold, Platinum, and Diamond.
        
        Gold tier requires a minimum combined balance of $20,000 across eligible Bank of America accounts.
        Platinum tier requires $50,000 minimum balance and Diamond tier requires $100,000 minimum balance.
        
        Published: 2024-01-15
        Last Updated: 2024-03-20
        Effective Date: 2024-01-01
        """
        
        sample_url = "https://promotions.bankofamerica.com/preferredrewards/en"
        sample_file_path = "/path/to/preferred_rewards.txt"
        
        # Extract document metadata
        print("Extracting document metadata...")
        doc_metadata = metadata_extractor.extract_document_metadata(
            text=sample_text,
            file_path=sample_file_path,
            url=sample_url
        )
        
        print(f"\n📄 DOCUMENT METADATA:")
        print(f"  Doc ID: {doc_metadata.doc_id}")
        print(f"  Title: {doc_metadata.title}")
        print(f"  Doc Type: {doc_metadata.doc_type}")
        print(f"  Domain: {doc_metadata.domain}")
        print(f"  Language: {doc_metadata.language}")
        print(f"  Authority Score: {doc_metadata.authority_score:.2f}")
        print(f"  Product Entities: {doc_metadata.product_entities}")
        print(f"  Categories: {doc_metadata.categories}")
        print(f"  Published At: {doc_metadata.published_at}")
        print(f"  Updated At: {doc_metadata.updated_at}")
        print(f"  Effective Date: {doc_metadata.effective_date}")
        print(f"  Geo Scope: {doc_metadata.geo_scope}")
        print(f"  Currency: {doc_metadata.currency}")
        
        # Test chunk metadata extraction
        print("\n" + "="*50)
        print("TESTING CHUNK METADATA EXTRACTION")
        print("="*50)
        
        # Sample chunk text
        chunk_text = "Gold tier requires a minimum combined balance of $20,000 across eligible Bank of America accounts."
        
        # Extract chunk metadata
        print("Extracting chunk metadata...")
        chunk_metadata = metadata_extractor.extract_chunk_metadata(
            text=chunk_text,
            doc_id=doc_metadata.doc_id,
            chunk_index=0,
            start_line=5,
            end_line=5,
            start_char=100,
            end_char=200
        )
        
        print(f"\n📦 CHUNK METADATA:")
        print(f"  Chunk ID: {chunk_metadata.chunk_id}")
        print(f"  Doc ID: {chunk_metadata.doc_id}")
        print(f"  Section Path: {chunk_metadata.section_path}")
        print(f"  Start Line: {chunk_metadata.start_line}")
        print(f"  End Line: {chunk_metadata.end_line}")
        print(f"  Start Char: {chunk_metadata.start_char}")
        print(f"  End Char: {chunk_metadata.end_char}")
        print(f"  Token Count: {chunk_metadata.token_count}")
        print(f"  Has Numbers: {chunk_metadata.has_numbers}")
        print(f"  Has Currency: {chunk_metadata.has_currency}")
        print(f"  Embedding Version: {chunk_metadata.embedding_version}")
        
        # Test metadata retrieval
        print("\n" + "="*50)
        print("TESTING METADATA RETRIEVAL")
        print("="*50)
        
        # Get document metadata by ID
        retrieved_doc = metadata_extractor.get_document_metadata(doc_metadata.doc_id)
        if retrieved_doc:
            print(f"✅ Retrieved document: {retrieved_doc.title}")
        else:
            print("❌ Document not found")
        
        # Get all document metadata
        all_docs = metadata_extractor.get_all_document_metadata()
        print(f"📊 Total documents in metadata store: {len(all_docs)}")
        
        # Test metadata export
        print("\n" + "="*50)
        print("TESTING METADATA EXPORT")
        print("="*50)
        
        # Export metadata
        export_data = metadata_extractor.export_metadata("test_metadata_export.json")
        print(f"✅ Metadata exported to test_metadata_export.json")
        print(f"   - Documents: {len(export_data['document_metadata'])}")
        # Note: chunk metadata is not exported by the basic extractor
        
        # Test with IndexBuilder
        print("\n" + "="*50)
        print("TESTING WITH INDEX BUILDER")
        print("="*50)
        
        index_builder = IndexBuilder(model_manager)
        
        # Test enhanced index building (if data folder exists)
        data_folder = "/Users/emadn/Projects/rag-frontend/backend/data"
        if os.path.exists(data_folder):
            print("Building enhanced index...")
            try:
                result = index_builder.build_enhanced_index_from_folder()
                print(f"✅ Enhanced index built successfully")
                print(f"   - Processed files: {result['processed_files']}")
                print(f"   - Total chunks: {result['total_chunks']}")
                print(f"   - Enhanced metadata stats:")
                for key, value in result['enhanced_metadata'].items():
                    print(f"     {key}: {value}")
            except Exception as e:
                print(f"⚠ Error building enhanced index: {e}")
        else:
            print("ℹ Data folder not found, skipping index building test")
        
        print("\n✅ Enhanced metadata system test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_metadata_system()
