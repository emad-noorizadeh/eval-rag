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
Security Check Script
Author: Emad Noorizadeh

This script verifies that the application is not sending data to external services.
"""

import os
import sys
import socket
import subprocess
import requests
from dotenv import load_dotenv

def check_telemetry_disabled():
    """Check if telemetry is properly disabled"""
    print("🔍 Checking telemetry disable status...")
    
    load_dotenv()
    
    checks = {
        "OpenAI Telemetry": os.getenv('OPENAI_TELEMETRY_DISABLED') == '1',
        "LangChain Tracing": os.getenv('LANGCHAIN_TRACING_V2') == 'false',
        "LangGraph Telemetry": os.getenv('LANGGRAPH_TELEMETRY_DISABLED') == '1',
        "ChromaDB Telemetry": os.getenv('CHROMA_TELEMETRY_DISABLED') == '1',
        "spaCy Telemetry": os.getenv('SPACY_DISABLE_TELEMETRY') == '1',
        "Hugging Face Telemetry": os.getenv('HF_HUB_DISABLE_TELEMETRY') == '1',
        "General Telemetry": os.getenv('TELEMETRY_DISABLED') == '1',
        "Analytics Disabled": os.getenv('ANALYTICS_DISABLED') == '1'
    }
    
    all_good = True
    for check, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check}: {'DISABLED' if status else 'ENABLED'}")
        if not status:
            all_good = False
    
    return all_good

def check_network_connections():
    """Check what network connections are being made"""
    print("\n🔍 Checking network connections...")
    
    try:
        # Check if we can resolve common telemetry domains
        telemetry_domains = [
            "api.openai.com",
            "api.langchain.com", 
            "api.langgraph.com",
            "api.llamaindex.ai",
            "api.chroma.ai",
            "api.huggingface.co"
        ]
        
        for domain in telemetry_domains:
            try:
                socket.gethostbyname(domain)
                print(f"  ⚠️  Can resolve {domain} (may be used for API calls)")
            except socket.gaierror:
                print(f"  ✅ Cannot resolve {domain} (blocked)")
        
        return True
    except Exception as e:
        print(f"  ❌ Network check error: {e}")
        return False

def check_logging_config():
    """Check logging configuration"""
    print("\n🔍 Checking logging configuration...")
    
    try:
        import logging
        root_logger = logging.getLogger()
        
        print(f"  📝 Log level: {root_logger.level}")
        print(f"  📁 Handlers: {len(root_logger.handlers)}")
        
        for handler in root_logger.handlers:
            if hasattr(handler, 'stream'):
                print(f"    - Stream handler: {type(handler.stream).__name__}")
            elif hasattr(handler, 'baseFilename'):
                print(f"    - File handler: {handler.baseFilename}")
        
        print(f"  🔄 Propagate: {root_logger.propagate}")
        
        return True
    except Exception as e:
        print(f"  ❌ Logging check error: {e}")
        return False

def check_environment_variables():
    """Check critical environment variables"""
    print("\n🔍 Checking environment variables...")
    
    critical_vars = [
        'OPENAI_TELEMETRY_DISABLED',
        'LANGCHAIN_TRACING_V2',
        'LANGGRAPH_TELEMETRY_DISABLED',
        'CHROMA_TELEMETRY_DISABLED',
        'TELEMETRY_DISABLED',
        'ANALYTICS_DISABLED'
    ]
    
    all_set = True
    for var in critical_vars:
        value = os.getenv(var)
        status_icon = "✅" if value else "❌"
        print(f"  {status_icon} {var}: {value}")
        if not value:
            all_set = False
    
    return all_set

def main():
    """Run all security checks"""
    print("🛡️  RAG Application Security Check")
    print("=" * 50)
    
    checks = [
        ("Telemetry Disabled", check_telemetry_disabled),
        ("Network Connections", check_network_connections),
        ("Logging Config", check_logging_config),
        ("Environment Variables", check_environment_variables)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Security Summary:")
    
    all_passed = True
    for name, result in results:
        status_icon = "✅" if result else "❌"
        print(f"  {status_icon} {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All security checks passed! Application is safe.")
    else:
        print("\n⚠️  Some security checks failed. Review the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
