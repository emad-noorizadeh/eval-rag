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
Test script for JSON metadata extraction
Author: Emad Noorizadeh
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.hybrid_metadata_extractor import HybridMetadataExtractor
from model_manager import ModelManager
from config import get_config, set_config, get_data_folder

def test_json_metadata_extraction():
    """Test JSON metadata extraction on data folder files"""
    print("=== Testing JSON Metadata Extraction ===\n")
    
    # Get data folder path
    data_folder = Path(get_data_folder())
    if not data_folder.exists():
        print(f"❌ Data folder not found: {data_folder}")
        return False
    
    print(f"📁 Data folder: {data_folder}")
    
    # Initialize model manager
    model_manager = ModelManager()
    if not model_manager.list_models()['openai']:
        print("❌ OpenAI client not available. Testing with regex-only mode.")
        model_manager = None
    
    # Initialize hybrid extractor
    print("\n🔧 Initializing Hybrid Metadata Extractor...")
    extractor = HybridMetadataExtractor(get_config, model_manager)
    
    # Test configurations
    configs = [
        {"name": "Regex Only", "enabled": False, "method": "regex_only"},
        {"name": "Hybrid", "enabled": True, "method": "hybrid"} if model_manager else None
    ]
    
    # Filter out None configs
    configs = [c for c in configs if c is not None]
    
    # Get text files
    text_files = list(data_folder.glob("*.txt")) + list(data_folder.glob("*.md"))
    
    if not text_files:
        print(f"⚠ No text files found in {data_folder}")
        return False
    
    print(f"📄 Processing {len(text_files)} files...")
    
    for config in configs:
        print(f"\n🔧 Testing {config['name']} configuration...")
        
        # Set configuration
        set_config("data", "llm_metadata_extraction.enabled", config["enabled"])
        set_config("data", "llm_metadata_extraction.method", config["method"])
        
        # Reinitialize extractor with new config
        extractor = HybridMetadataExtractor(get_config, model_manager)
        
        # Process each file and save as JSON
        for file_path in text_files:
            try:
                print(f"  Processing: {file_path.name}")
                
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata as JSON
                json_metadata = extractor.extract_metadata_as_json(content, indent=2)
                
                # Save to JSON file
                output_file = Path(__file__).parent / f"{file_path.stem}_{config['name'].lower().replace(' ', '_')}_metadata.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_metadata)
                
                print(f"    ✅ Saved to: {output_file.name}")
                
                # Show sample of JSON structure
                metadata_obj = json.loads(json_metadata)
                print(f"    📊 Fields: {len(metadata_obj['combined_metadata'])}")
                print(f"    ⏱️ Time: {metadata_obj['processing_time']:.2f}s")
                print(f"    🎯 Method: {metadata_obj['extraction_method']}")
                print(f"    📈 Confidence: {metadata_obj['confidence_scores'].get('overall', 0):.2f}")
                
            except Exception as e:
                print(f"    ❌ Error processing {file_path.name}: {e}")
    
    # Test batch extraction as JSON
    print(f"\n🔧 Testing batch JSON extraction...")
    
    # Set to hybrid mode for batch test
    if model_manager:
        set_config("data", "llm_metadata_extraction.enabled", True)
        set_config("data", "llm_metadata_extraction.method", "hybrid")
        extractor = HybridMetadataExtractor(get_config, model_manager)
        
        # Read all files
        texts = []
        for file_path in text_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                texts.append(f.read())
        
        # Batch extract as JSON
        batch_json = extractor.batch_extract_as_json(texts, indent=2)
        
        # Save batch results
        batch_output_file = Path(__file__).parent / "batch_metadata_results.json"
        with open(batch_output_file, 'w', encoding='utf-8') as f:
            f.write(batch_json)
        
        print(f"✅ Batch results saved to: {batch_output_file.name}")
        
        # Show batch statistics
        batch_data = json.loads(batch_json)
        print(f"📊 Batch processed {len(batch_data)} documents")
        
        total_time = sum(item['processing_time'] for item in batch_data)
        avg_confidence = sum(item['confidence_scores'].get('overall', 0) for item in batch_data) / len(batch_data)
        
        print(f"⏱️ Total time: {total_time:.2f}s")
        print(f"📈 Average confidence: {avg_confidence:.2f}")
    
    print(f"\n✅ JSON metadata extraction test completed!")
    return True

def create_metadata_summary():
    """Create a summary of all JSON metadata files"""
    print("\n📋 Creating metadata summary...")
    
    tests_dir = Path(__file__).parent
    json_files = list(tests_dir.glob("*_metadata.json"))
    
    if not json_files:
        print("No JSON metadata files found.")
        return
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_files": len(json_files),
        "files": []
    }
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_info = {
                "filename": json_file.name,
                "extraction_method": data.get("extraction_method", "unknown"),
                "processing_time": data.get("processing_time", 0),
                "confidence": data.get("confidence_scores", {}).get("overall", 0),
                "total_fields": len(data.get("combined_metadata", {})),
                "deterministic_fields": len(data.get("deterministic_metadata", {})),
                "semantic_fields": len(data.get("semantic_metadata", {}))
            }
            
            summary["files"].append(file_info)
            
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
    
    # Save summary
    summary_file = tests_dir / "metadata_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Summary saved to: {summary_file.name}")
    
    # Print summary
    print(f"\n📊 Metadata Summary:")
    print(f"Total files: {summary['total_files']}")
    for file_info in summary["files"]:
        print(f"  {file_info['filename']}:")
        print(f"    Method: {file_info['extraction_method']}")
        print(f"    Fields: {file_info['total_fields']} (D:{file_info['deterministic_fields']}, S:{file_info['semantic_fields']})")
        print(f"    Time: {file_info['processing_time']:.2f}s, Confidence: {file_info['confidence']:.2f}")

if __name__ == "__main__":
    test_json_metadata_extraction()
    create_metadata_summary()
