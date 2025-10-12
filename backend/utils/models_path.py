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
Models Path Utility
Author: Emad Noorizadeh

Provides centralized model path management using environment variables.
"""

import os
from pathlib import Path
from typing import Optional

def get_models_path() -> str:
    """
    Get the models directory path from environment variable or use default.
    
    Returns:
        str: Path to the models directory
    """
    # Try to get from environment variable first
    models_path = os.getenv("MODELS_PATH")
    
    if models_path:
        # Expand user home directory if present
        models_path = os.path.expanduser(models_path)
        # Convert to absolute path
        models_path = os.path.abspath(models_path)
        return models_path
    
    # Default path
    default_path = "/Users/emadn/Projects/models"
    return os.path.abspath(default_path)

def get_model_path(model_name: str = "all-MiniLM-L6-v2") -> str:
    """
    Get the full path to a specific model.
    
    Args:
        model_name: Name of the model (default: "all-MiniLM-L6-v2")
        
    Returns:
        str: Full path to the model directory
    """
    models_dir = get_models_path()
    return os.path.join(models_dir, model_name)

def ensure_models_directory() -> bool:
    """
    Ensure the models directory exists.
    
    Returns:
        bool: True if directory exists or was created successfully
    """
    models_dir = get_models_path()
    
    try:
        os.makedirs(models_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating models directory '{models_dir}': {e}")
        return False

def list_available_models() -> list:
    """
    List all available models in the models directory.
    
    Returns:
        list: List of model names found in the directory
    """
    models_dir = get_models_path()
    
    if not os.path.exists(models_dir):
        return []
    
    try:
        models = []
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path):
                models.append(item)
        return models
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []

def get_model_info() -> dict:
    """
    Get information about the models configuration.
    
    Returns:
        dict: Information about models path and available models
    """
    models_dir = get_models_dir()
    available_models = list_available_models()
    
    return {
        "models_path": models_dir,
        "models_path_env": os.getenv("MODELS_PATH"),
        "default_path": "/Users/emadn/Projects/models",
        "directory_exists": os.path.exists(models_dir),
        "available_models": available_models,
        "minilm_path": get_model_path("all-MiniLM-L6-v2"),
        "minilm_exists": os.path.exists(get_model_path("all-MiniLM-L6-v2"))
    }

# Backward compatibility function
def get_models_dir() -> str:
    """Backward compatibility function for get_models_path()"""
    return get_models_path()

if __name__ == "__main__":
    print("🔍 Models Path Configuration")
    print("=" * 50)
    
    info = get_model_info()
    
    print(f"Models Directory: {info['models_path']}")
    print(f"Environment Variable: {info['models_path_env'] or 'Not set'}")
    print(f"Default Path: {info['default_path']}")
    print(f"Directory Exists: {info['directory_exists']}")
    print(f"MiniLM Path: {info['minilm_path']}")
    print(f"MiniLM Exists: {info['minilm_exists']}")
    print(f"Available Models: {info['available_models']}")
