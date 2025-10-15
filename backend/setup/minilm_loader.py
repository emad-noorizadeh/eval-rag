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
Minimal Model Loader
Author: Emad Noorizadeh

Downloads and saves the sentence-transformers model locally for offline use.
"""

import os
import sys
from sentence_transformers import SentenceTransformer

def download_and_save_model():
    """Download and save the sentence-transformers model locally."""
    print("🔄 Downloading sentence-transformers model...")
    print("Model: sentence-transformers/all-MiniLM-L6-v2")
    
    try:
        # Download the model (this will cache it in ~/.cache or HF_HOME)
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✅ Model downloaded successfully")
        
        # Use models path from environment or default
        from ..utils.models_path import get_models_path, ensure_models_directory
        
        models_dir = get_models_path()
        
        # Ensure models directory exists
        if not ensure_models_directory():
            print(f"❌ Error: Could not create models directory at {models_dir}")
            return False
        
        # Save the model to the models directory
        model_path = os.path.join(models_dir, "all-MiniLM-L6-v2")
        print(f"💾 Saving model to: {model_path}")
        
        model.save(model_path)
        print("✅ Model saved successfully!")
        
        # Verify the model was saved
        if os.path.exists(model_path):
            print(f"✅ Verification: Model directory exists at {model_path}")
            print("📁 Contents:")
            for item in os.listdir(model_path):
                print(f"   - {item}")
        else:
            print("❌ Error: Model directory not found after saving")
            return False
            
        print("\n🎉 Model download and save completed successfully!")
        print("You can now load the model locally using:")
        print(f"model = SentenceTransformer('{model_path}')")
        print(f"Models directory: {models_dir}")
        print("The model will be automatically loaded from this location by the system.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading/saving model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Minimal Model Loader")
    print("=" * 60)
    
    success = download_and_save_model()
    
    if success:
        print("\n✅ Process completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Process failed!")
        sys.exit(1)
