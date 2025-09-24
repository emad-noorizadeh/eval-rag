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
Run tests and save output to files
Author: Emad Noorizadeh
"""

import os
import sys
import subprocess
from datetime import datetime

def run_test_with_output(test_name, test_file):
    """Run a test and save output to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_{test_name}_results_{timestamp}.txt"
    
    print(f"🧪 Running {test_name} test...")
    
    try:
        # Run the test and capture output
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Save output to file
        with open(output_file, 'w') as f:
            f.write(f"=== {test_name.upper()} TEST RESULTS ===\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Test file: {test_file}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("STDOUT:\n")
            f.write("-" * 20 + "\n")
            f.write(result.stdout)
            
            if result.stderr:
                f.write("\n\nSTDERR:\n")
                f.write("-" * 20 + "\n")
                f.write(result.stderr)
            
            f.write(f"\n\nReturn code: {result.returncode}\n")
        
        print(f"✅ {test_name} test completed - Results saved to: {output_file}")
        return True, output_file
        
    except Exception as e:
        print(f"❌ {test_name} test failed: {e}")
        return False, None

def main():
    """Run all tests and save outputs"""
    print("🚀 Running Tests with Output Capture")
    print("=" * 50)
    
    tests = [
        ("index_builder", "test_index_builder.py"),
        ("metadata_extraction", "test_metadata_extraction.py"),
        ("hybrid_metadata_extractor", "test_hybrid_metadata_extractor.py"),
    ]
    
    results = {}
    
    for test_name, test_file in tests:
        success, output_file = run_test_with_output(test_name, test_file)
        results[test_name] = {
            "success": success,
            "output_file": output_file
        }
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("-" * 30)
    for test_name, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        output_file = result["output_file"] or "No output file"
        print(f"{test_name}: {status} - {output_file}")
    
    print(f"\n📁 All output files saved in: {os.getcwd()}/tests/")

if __name__ == "__main__":
    main()
