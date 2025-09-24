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
Simple data extraction test to avoid recursion issues
Author: Emad Noorizadeh
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.hybrid_metadata_extractor import HybridMetadataExtractor
from model_manager import ModelManager
from config import get_config, set_config, get_data_folder

def extract_metadata_from_data_folder():
    """Extract metadata from data folder files and save results"""
    print("=== Simple Data Folder Metadata Extraction ===\n")
    
    # Get data folder path
    data_folder = Path(get_data_folder())
    if not data_folder.exists():
        print(f"❌ Data folder not found: {data_folder}")
        return False
    
    print(f"📁 Data folder: {data_folder}")
    
    # Initialize model manager (optional)
    model_manager = None
    try:
        model_manager = ModelManager()
        if not model_manager.list_models()['openai']:
            print("⚠ OpenAI client not available. Using regex-only mode.")
            model_manager = None
    except Exception as e:
        print(f"⚠ Model manager initialization failed: {e}. Using regex-only mode.")
        model_manager = None
    
    # Test configurations
    configs = [
        {"name": "Regex Only", "enabled": False, "method": "regex_only"},
        {"name": "Hybrid", "enabled": True, "method": "hybrid"} if model_manager else None
    ]
    
    # Filter out None configs
    configs = [c for c in configs if c is not None]
    
    results = {}
    
    for config in configs:
        print(f"\n🔧 Testing {config['name']} configuration...")
        
        # Set configuration
        set_config("data", "llm_metadata_extraction.enabled", config["enabled"])
        set_config("data", "llm_metadata_extraction.method", config["method"])
        
        # Initialize extractor
        extractor = HybridMetadataExtractor(get_config, model_manager)
        
        # Get text files
        text_files = list(data_folder.glob("*.txt")) + list(data_folder.glob("*.md"))
        
        if not text_files:
            print(f"⚠ No text files found in {data_folder}")
            continue
        
        print(f"📄 Processing {len(text_files)} files...")
        
        file_results = []
        total_time = 0
        
        for file_path in text_files:
            try:
                print(f"  Processing: {file_path.name}")
                
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                result = extractor.extract_metadata(content)
                total_time += result.processing_time
                
                # Store result
                file_result = {
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "extraction_method": result.extraction_method,
                    "processing_time": result.processing_time,
                    "confidence": result.confidence_scores.get('overall', 0),
                    "deterministic_fields": len(result.deterministic),
                    "semantic_fields": len(result.semantic) if result.semantic else 0,
                    "combined_fields": len(result.combined),
                    "sample_metadata": dict(list(result.combined.items())[:10]),  # First 10 fields
                    "full_metadata": result.combined  # Full metadata for detailed analysis
                }
                
                file_results.append(file_result)
                
                print(f"    Method: {result.extraction_method}")
                print(f"    Time: {result.processing_time:.2f}s")
                print(f"    Fields: {len(result.combined)}")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                file_results.append({
                    "file_name": file_path.name,
                    "error": str(e),
                    "extraction_method": "failed"
                })
        
        # Calculate stats
        successful = len([r for r in file_results if r.get('extraction_method') != 'failed'])
        hybrid_count = len([r for r in file_results if r.get('extraction_method') == 'hybrid'])
        regex_count = len([r for r in file_results if r.get('extraction_method') == 'regex_only'])
        
        avg_confidence = 0
        if successful > 0:
            confidences = [r.get('confidence', 0) for r in file_results if 'confidence' in r]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        results[config['name']] = {
            "config": config,
            "files_processed": len(file_results),
            "successful": successful,
            "success_rate": successful / len(file_results) if file_results else 0,
            "hybrid_extractions": hybrid_count,
            "regex_extractions": regex_count,
            "total_time": total_time,
            "avg_time": total_time / len(file_results) if file_results else 0,
            "avg_confidence": avg_confidence,
            "file_results": file_results
        }
        
        print(f"  ✅ {config['name']} completed:")
        print(f"    Files: {len(file_results)}, Success: {successful}")
        print(f"    Hybrid: {hybrid_count}, Regex: {regex_count}")
        print(f"    Time: {total_time:.2f}s, Confidence: {avg_confidence:.2f}")
    
    # Save results
    print(f"\n💾 Saving results to metadata_results.txt...")
    
    output_file = Path(__file__).parent / "metadata_results.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Hybrid Metadata Extraction Results\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Data folder: {data_folder}\n")
        f.write(f"Total files: {len(text_files)}\n\n")
        
        for config_name, config_results in results.items():
            f.write(f"\n{config_name} Configuration\n")
            f.write("-" * 30 + "\n")
            f.write(f"Files processed: {config_results['files_processed']}\n")
            f.write(f"Success rate: {config_results['success_rate']:.2%}\n")
            f.write(f"Hybrid extractions: {config_results['hybrid_extractions']}\n")
            f.write(f"Regex extractions: {config_results['regex_extractions']}\n")
            f.write(f"Total time: {config_results['total_time']:.2f}s\n")
            f.write(f"Average time: {config_results['avg_time']:.2f}s\n")
            f.write(f"Average confidence: {config_results['avg_confidence']:.2f}\n\n")
            
            f.write("File Results:\n")
            f.write("-" * 15 + "\n")
            
            for file_result in config_results['file_results']:
                f.write(f"\nFile: {file_result['file_name']}\n")
                f.write(f"Method: {file_result.get('extraction_method', 'unknown')}\n")
                f.write(f"Time: {file_result.get('processing_time', 0):.2f}s\n")
                
                if 'error' in file_result:
                    f.write(f"Error: {file_result['error']}\n")
                else:
                    f.write(f"Confidence: {file_result.get('confidence', 0):.2f}\n")
                    f.write(f"Fields: {file_result.get('combined_fields', 0)}\n")
                    f.write(f"Deterministic: {file_result.get('deterministic_fields', 0)}\n")
                    f.write(f"Semantic: {file_result.get('semantic_fields', 0)}\n")
                    
                    # Show sample metadata
                    sample = file_result.get('sample_metadata', {})
                    if sample:
                        f.write("Sample metadata:\n")
                        for key, value in sample.items():
                            f.write(f"  {key}: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}\n")
                    
                    # Show all metadata for hybrid extractions
                    if file_result.get('extraction_method') == 'hybrid':
                        f.write("\nFull metadata details:\n")
                        f.write("-" * 20 + "\n")
                        
                        # Get the actual combined metadata from the result
                        if 'full_metadata' in file_result:
                            full_metadata = file_result['full_metadata']
                            f.write(f"Total fields: {len(full_metadata)}\n\n")
                            
                            # Group by type
                            deterministic_fields = {}
                            semantic_fields = {}
                            
                            for key, value in full_metadata.items():
                                if key in ['title', 'headline', 'link_text', 'link_url', 'is_link', 'headings', 'main_heading', 'categories', 'line_count', 'word_count', 'char_count', 'emails', 'urls', 'processed_at']:
                                    deterministic_fields[key] = value
                                else:
                                    semantic_fields[key] = value
                            
                            f.write("Deterministic fields:\n")
                            for key, value in deterministic_fields.items():
                                f.write(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n")
                            
                            f.write("\nSemantic fields:\n")
                            for key, value in semantic_fields.items():
                                f.write(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n")
            
            f.write("\n" + "=" * 50 + "\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 Summary:")
    for config_name, config_results in results.items():
        print(f"  {config_name}:")
        print(f"    Success: {config_results['success_rate']:.2%}")
        print(f"    Hybrid: {config_results['hybrid_extractions']}, Regex: {config_results['regex_extractions']}")
        print(f"    Time: {config_results['avg_time']:.2f}s, Confidence: {config_results['avg_confidence']:.2f}")
    
    return True

if __name__ == "__main__":
    extract_metadata_from_data_folder()
