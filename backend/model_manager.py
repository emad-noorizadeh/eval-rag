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
from llama_index.embeddings.openai import OpenAIEmbedding
import openai
import os
from config import get_config

class ModelManager:
    """Manages all models used in the RAG system"""
    
    def __init__(self, openai_api_key: str = None):
        self.models: Dict[str, Any] = {}
        self.embedding_model = None
        self.openai_client = None
        self._initialize_models(openai_api_key)
    
    def _initialize_models(self, openai_api_key: str = None):
        """Initialize all available models"""
        # Get API key from environment or parameter
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("⚠ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            return
        
        try:
            # Get embedding model from configuration
            embedding_model_name = get_config("models", "embedding_model")
            # Initialize embedding model for LlamaIndex
            self.embedding_model = OpenAIEmbedding(
                api_key=api_key,
                model=embedding_model_name
            )
            self.models['embedding'] = self.embedding_model
            print(f"✓ OpenAI Embedding model ({embedding_model_name}) loaded for LlamaIndex")
        except Exception as e:
            print(f"✗ Failed to load embedding model: {e}")
            self.embedding_model = None
        
        try:
            # Initialize OpenAI client for direct API calls
            self.openai_client = openai.OpenAI(api_key=api_key)
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
