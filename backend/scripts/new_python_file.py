#!/usr/bin/env python3
"""
Script to create new Python files with Apache 2.0 license header
Usage: python scripts/new_python_file.py <filename> [description]
"""

import sys
import os
from pathlib import Path

LICENSE_HEADER = '''# Copyright 2025 Emad Noorizadeh
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

'''

def create_python_file(filename, description="Python module"):
    """Create a new Python file with license header"""
    if not filename.endswith('.py'):
        filename += '.py'
    
    # Get the current directory (backend)
    current_dir = Path.cwd()
    file_path = current_dir / filename
    
    if file_path.exists():
        print(f"❌ File {filename} already exists!")
        return False
    
    content = LICENSE_HEADER + f'"""\n{description}\nAuthor: Emad Noorizadeh\n"""\n\n# [Your code here]\n'
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created {filename} with Apache 2.0 license header")
        print(f"📁 Location: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating {filename}: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/new_python_file.py <filename> [description]")
        print("Example: python scripts/new_python_file.py my_module 'My awesome module'")
        return
    
    filename = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else "Python module"
    
    create_python_file(filename, description)

if __name__ == "__main__":
    main()
