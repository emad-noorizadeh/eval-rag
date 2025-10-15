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
Model Manager for RAG System
Author: Emad Noorizadeh
"""

from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
import openai
import os
from .config import get_config

# Ensure environment variables (like OPENAI_API_KEY) are loaded once per process
load_dotenv(find_dotenv(), override=False)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _resolve_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Resolve the OpenAI API key from explicit arg, env, or config."""
    if explicit_key:
        return explicit_key
    
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    
    try:
        config_key = get_config("models", "api_key")
    except Exception:
        config_key = None
    
    if config_key:
        print("✓ OpenAI API key loaded from configuration")
        return config_key
    
    fallback_path = Path.home() / ".openai_key"
    try:
        if fallback_path.exists():
            file_key = fallback_path.read_text(encoding="utf-8").strip()
            if file_key:
                print(f"✓ OpenAI API key loaded from {fallback_path}")
                return file_key
    except Exception as e:
        print(f"⚠️ Could not read fallback OpenAI key file {fallback_path}: {e}")
    
    return None

class ModelManager:
    """Manages all models used in the RAG system"""
    
    def __init__(self, openai_api_key: str = None):
        self.models: Dict[str, Any] = {}
        self.embedding_model = None
        self.openai_client = None
        self.api_key = _resolve_api_key(openai_api_key)
        self.openai_base_url = get_config("models", "base_url")
        self.use_openai_url = bool(get_config("models", "use_openai_url") or False)
        if self.use_openai_url:
            if self.openai_base_url:
                openai.base_url = self.openai_base_url
                os.environ["OPENAI_BASE_URL"] = self.openai_base_url
                print(f"✓ OpenAI base URL set to {self.openai_base_url}")
            else:
                print("⚠️ use_openai_url enabled but no base URL configured; falling back to default OpenAI endpoint.")
        if self.api_key:
            # Keep env in sync so downstream libs relying on os.getenv still work
            os.environ["OPENAI_API_KEY"] = self.api_key
        self._initialize_models()
    
    def _initialize_models(self, openai_api_key: str = None):
        """Initialize all available models"""
        # Get API key from environment or parameter
        api_key = self.api_key or _resolve_api_key(openai_api_key)
        
        if not api_key:
            raise ValueError("No OpenAI API key available. Set OPENAI_API_KEY or configure models.api_key.")
        
        try:
            # Get embedding model from configuration
            embedding_model_name = get_config("models", "embedding_model")
            # Initialize embedding model for LlamaIndex
            embedding_kwargs = {
                "api_key": api_key,
                "model": embedding_model_name
            }
            if self.use_openai_url and self.openai_base_url:
                embedding_kwargs["api_base"] = self.openai_base_url
            self.embedding_model = OpenAIEmbedding(**embedding_kwargs)
            self.models['embedding'] = self.embedding_model
            print(f"✓ OpenAI Embedding model ({embedding_model_name}) loaded for LlamaIndex")
        except Exception as e:
            print(f"✗ Failed to load embedding model: {e}")
            self.embedding_model = None
        
        try:
            # Initialize OpenAI client for direct API calls
            client_kwargs = {"api_key": api_key}
            if self.use_openai_url and self.openai_base_url:
                client_kwargs["base_url"] = self.openai_base_url
            self.openai_client = openai.OpenAI(**client_kwargs)
            self.models['openai'] = self.openai_client
            print("✓ OpenAI client initialized for direct API calls")
        except Exception as e:
            print(f"✗ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def get_embedding_model(self) -> Optional[OpenAIEmbedding]:
        """Get the embedding model for LlamaIndex"""
        return self.embedding_model
    
    def get_openai_client(self) -> Optional[openai.OpenAI]:
        """Get the OpenAI client for direct API calls"""
        return self.openai_client
    
    def get_model(self, model_type: str) -> Optional[Any]:
        """Get a specific model by type"""
        return self.models.get(model_type)
    
    def list_models(self) -> Dict[str, bool]:
        """List all available models and their status"""
        return {
            'embedding': self.embedding_model is not None,
            'openai': self.openai_client is not None
        }
    
    def generate_text(self, messages: list, model: str = None, temperature: float = None) -> str:
        """Generate text using OpenAI API directly"""
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        # Use configured defaults if not provided
        if model is None:
            model = get_config("models", "llm_model")
        if temperature is None:
            temperature = get_config("models", "temperature")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=get_config("models", "max_tokens")
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Error generating text: {e}")
