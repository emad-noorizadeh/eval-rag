#!/usr/bin/env python3
"""
Enable Offline Mode for RAG System
Author: Emad Noorizadeh

This script configures the RAG system to run in offline mode,
disabling all web-based downloads and using local tokenizers.
"""

import os
import sys

def enable_offline_mode():
    """Enable offline mode by setting environment variables"""
    print("🔒 Enabling offline mode...")
    
    # Set offline mode environment variables
    os.environ["OFFLINE_MODE"] = "true"
    os.environ["TIKTOKEN_CACHE_DIR"] = "./tokenizer_cache"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./models"
    
    # Disable web-based downloads
    os.environ["DISABLE_WEB_DOWNLOADS"] = "true"
    os.environ["LOCAL_MODELS_ONLY"] = "true"
    
    print("✅ Offline mode enabled")
    print("📋 Environment variables set:")
    print(f"  - OFFLINE_MODE: {os.environ.get('OFFLINE_MODE')}")
    print(f"  - TIKTOKEN_CACHE_DIR: {os.environ.get('TIKTOKEN_CACHE_DIR')}")
    print(f"  - HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
    print(f"  - TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
    print(f"  - SENTENCE_TRANSFORMERS_HOME: {os.environ.get('SENTENCE_TRANSFORMERS_HOME')}")
    print(f"  - DISABLE_WEB_DOWNLOADS: {os.environ.get('DISABLE_WEB_DOWNLOADS')}")
    print(f"  - LOCAL_MODELS_ONLY: {os.environ.get('LOCAL_MODELS_ONLY')}")

def create_offline_env_file():
    """Create .env file with offline mode settings"""
    env_content = """# Offline Mode Configuration
OFFLINE_MODE=true
TIKTOKEN_CACHE_DIR=./tokenizer_cache
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
SENTENCE_TRANSFORMERS_HOME=./models
DISABLE_WEB_DOWNLOADS=true
LOCAL_MODELS_ONLY=true

# Disable all telemetry
OPENAI_TELEMETRY_DISABLED=1
OPENAI_DISABLE_TELEMETRY=1
LANGCHAIN_TRACING_V2=false
LANGCHAIN_TRACING=false
LANGGRAPH_TELEMETRY_DISABLED=1
LLAMA_INDEX_TELEMETRY_DISABLED=1
CHROMA_TELEMETRY_DISABLED=1
SPACY_DISABLE_TELEMETRY=1
HF_HUB_DISABLE_TELEMETRY=1
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("📄 Created .env file with offline mode settings")

def test_offline_tokenizer():
    """Test the offline tokenizer"""
    print("\n🧪 Testing offline tokenizer...")
    
    try:
        from local_tokenizer import get_safe_encoder
        
        # Test the tokenizer
        encoder = get_safe_encoder("cl100k_base")
        test_text = "Hello world! This is a test sentence for offline tokenization."
        
        tokens = encoder(test_text)
        print(f"✅ Tokenizer test successful")
        print(f"   Input: '{test_text}'")
        print(f"   Tokens: {len(tokens)} tokens")
        print(f"   Sample tokens: {tokens[:5]}...")
        
    except Exception as e:
        print(f"❌ Tokenizer test failed: {e}")

if __name__ == "__main__":
    print("🚀 RAG System Offline Mode Setup")
    print("=" * 40)
    
    # Enable offline mode
    enable_offline_mode()
    
    # Create .env file
    create_offline_env_file()
    
    # Test offline tokenizer
    test_offline_tokenizer()
    
    print("\n🎉 Offline mode setup complete!")
    print("\n📋 Next steps:")
    print("1. Ensure all models are downloaded locally")
    print("2. Run: python main.py")
    print("3. The system will now work completely offline")
    print("\n⚠️  Note: Make sure to download models before going offline!")
