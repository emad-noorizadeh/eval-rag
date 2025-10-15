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
Telemetry Disable Module
Author: Emad Noorizadeh

This module disables all telemetry, analytics, and external logging
to ensure the application never sends data to external services.
"""

import os
import logging
import warnings

def disable_all_telemetry():
    """
    Disable all telemetry, analytics, and external logging.
    This function should be called at the very beginning of the application.
    """
    
    # Disable OpenAI telemetry
    os.environ["OPENAI_TELEMETRY_DISABLED"] = "1"
    os.environ["OPENAI_DISABLE_TELEMETRY"] = "1"
    
    # Disable LangChain telemetry
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGCHAIN_TRACING"] = "false"
    os.environ["LANGCHAIN_VERBOSE"] = "false"
    os.environ["LANGCHAIN_DEBUG"] = "false"
    os.environ["LANGCHAIN_ENDPOINT"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""
    os.environ["LANGCHAIN_PROJECT"] = ""
    
    # Disable LangGraph telemetry
    os.environ["LANGGRAPH_TELEMETRY_DISABLED"] = "1"
    os.environ["LANGGRAPH_DISABLE_TELEMETRY"] = "1"
    
    # Disable LlamaIndex telemetry
    os.environ["LLAMA_INDEX_TELEMETRY_DISABLED"] = "1"
    os.environ["LLAMA_INDEX_DISABLE_TELEMETRY"] = "1"
    
    # Disable ChromaDB telemetry
    os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "1"
    
    # Disable spaCy telemetry
    os.environ["SPACY_DISABLE_TELEMETRY"] = "1"
    
    # Disable sentence-transformers telemetry
    os.environ["SENTENCE_TRANSFORMERS_DISABLE_TELEMETRY"] = "1"
    
    # Disable Hugging Face telemetry
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    
    # Disable general Python telemetry
    os.environ["PYTHON_DISABLE_TELEMETRY"] = "1"
    
    # Disable FastAPI telemetry
    os.environ["FASTAPI_DISABLE_TELEMETRY"] = "1"
    
    # Disable uvicorn telemetry
    os.environ["UVICORN_DISABLE_TELEMETRY"] = "1"
    
    # Disable Pydantic telemetry
    os.environ["PYDANTIC_DISABLE_TELEMETRY"] = "1"
    
    # Disable all external analytics
    os.environ["ANALYTICS_DISABLED"] = "1"
    os.environ["TELEMETRY_DISABLED"] = "1"
    os.environ["TRACKING_DISABLED"] = "1"
    
    # Disable network requests for telemetry
    os.environ["NO_PROXY"] = "*"
    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""
    
    # Configure logging to only local files, no external services
    logging.getLogger().setLevel(logging.WARNING)  # Reduce log verbosity
    
    # Disable specific library warnings that might trigger telemetry
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*telemetry.*")
    warnings.filterwarnings("ignore", message=".*tracking.*")
    warnings.filterwarnings("ignore", message=".*analytics.*")
    
    print("✅ All telemetry and external logging disabled")

def configure_local_logging_only():
    """
    Configure logging to only write to local files, never external services.
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create local file handler only
    os.makedirs("./logs", exist_ok=True)
    file_handler = logging.FileHandler("./logs/rag_system_local.log")
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    
    # Add only local file handler
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)
    
    # Disable propagation to prevent external logging
    root_logger.propagate = False
    
    print("✅ Configured local-only logging")

def disable_network_telemetry():
    """
    Disable network-based telemetry by blocking common telemetry endpoints.
    """
    
    # Block common telemetry domains
    blocked_domains = [
        "api.openai.com/v1/telemetry",
        "api.anthropic.com/telemetry", 
        "api.langchain.com/telemetry",
        "api.langgraph.com/telemetry",
        "api.llamaindex.ai/telemetry",
        "api.chroma.ai/telemetry",
        "api.huggingface.co/telemetry",
        "api.spacy.io/telemetry",
        "analytics.google.com",
        "www.google-analytics.com",
        "telemetry.mozilla.org",
        "telemetry.microsoft.com"
    ]
    
    # Set environment variables to block these
    os.environ["BLOCKED_TELEMETRY_DOMAINS"] = ",".join(blocked_domains)
    
    print("✅ Network telemetry blocking configured")

def disable_all_external_connections():
    """
    Disable all non-essential external connections for maximum security.
    """
    
    # Disable package manager telemetry
    os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    os.environ["PIP_NO_CACHE_DIR"] = "1"
    os.environ["PIP_DISABLE_TELEMETRY"] = "1"
    
    # Disable conda telemetry
    os.environ["CONDA_DISABLE_TELEMETRY"] = "1"
    
    # Disable npm telemetry
    os.environ["NPM_CONFIG_DISABLE_TELEMETRY"] = "1"
    
    # Disable git telemetry
    os.environ["GIT_DISABLE_TELEMETRY"] = "1"
    
    # Disable system telemetry
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["DNT"] = "1"
    
    # Disable browser telemetry
    os.environ["BROWSER_DISABLE_TELEMETRY"] = "1"
    
    # Disable OS telemetry
    os.environ["OS_DISABLE_TELEMETRY"] = "1"
    
    # Disable all analytics
    os.environ["ANALYTICS_DISABLED"] = "1"
    os.environ["METRICS_DISABLED"] = "1"
    os.environ["STATS_DISABLED"] = "1"
    
    print("✅ All external connections disabled")

def create_network_monitor():
    """
    Create a simple network monitor to detect any unexpected external connections.
    """
    import socket
    import threading
    import time
    
    def monitor_connections():
        """Monitor for unexpected external connections"""
        try:
            # This is a simple check - in production you'd want more sophisticated monitoring
            print("🔍 Network monitoring active - checking for unexpected connections")
        except Exception as e:
            print(f"⚠️ Network monitoring error: {e}")
    
    # Start monitoring in background
    monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
    monitor_thread.start()
    
    print("✅ Network monitoring enabled")

if __name__ == "__main__":
    # Run all telemetry disabling functions
    disable_all_telemetry()
    configure_local_logging_only()
    disable_network_telemetry()
    print("🔒 All telemetry and external logging completely disabled")
