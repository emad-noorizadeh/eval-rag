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
System Configuration for RAG System
Author: Emad Noorizadeh
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

class SystemConfig:
    """Centralized system configuration management"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config_from_file()
        self._load_config_from_env()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            # Database Configuration
            "database": {
                "path": "./chroma_db",
                "collection_name": "enhanced-search",
                "backup_path": "./chroma_db_backup"
            },
            
            # Data Configuration
            "data": {
                "folder_path": "./data",
                "supported_extensions": [".txt", ".md", ".pdf"],
                "max_file_size_mb": 50,
                "encoding": "utf-8",
                "recursive": True,
                "extract_metadata": True,
                "metadata_extraction": {
                    "extract_headings": True,
                    "extract_links": True,
                    "extract_dates": True,
                    "extract_emails": True,
                    "extract_urls": True,
                    "extract_categories": True,
                    "max_heading_lines": 10,
                    "max_category_lines": 5
                },
                "llm_metadata_extraction": {
                    "enabled": True,  # Re-enabled for richer metadata
                    "method": "hybrid",  # regex_only, llm_only, hybrid, adaptive
                    "model": "gpt-4o",
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enable_structured_output": True,
                    "fallback_to_regex": True,
                    "confidence_threshold": 0.7,
                    "max_text_length": 4000
                }
            },
            
            # Chunking Configuration
            "chunking": {
                "chunk_size": 1024,
                "chunk_overlap": 20,
                "min_chunk_size": 100,
                "max_chunk_size": 4000
            },
            
            # API Configuration
            "api": {
                "host": "0.0.0.0",
                "port": 9000,
                "cors_origins": ["http://localhost:4000"],
                "max_request_size": 100 * 1024 * 1024,  # 100MB
                "timeout": 30
            },
            
            # Chat Agent Configuration
            "chat_agent": {
                "retrieval_method": "semantic",  # semantic only
                "routing_strategy": "intelligent",  # intelligent, simple
                "retrieval_top_k": 5,
                "similarity_threshold": 0.45,
                "max_clarify": 2,
                "reclarify_threshold": 0.35,
                "window_k": 4
            },
            
            # Session Configuration
            "session": {
                "timeout_minutes": 30,
                "cleanup_interval": 300,
                "data_folder": "./data",
                "collection_prefix": "session"
            },
            
            # Model Configuration
            "models": {
                "embedding_model": "text-embedding-3-small",
                "llm_model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            
            # Logging Configuration - LOCAL ONLY, NO EXTERNAL TELEMETRY
            "logging": {
                "level": "WARNING",  # Reduced verbosity
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "./logs/rag_system_local.log",  # Local file only
                "max_size_mb": 10,
                "backup_count": 5,
                "disable_external": True,  # Disable all external logging
                "telemetry_disabled": True  # Explicit telemetry disable
            },
            
            # Performance Configuration
            "performance": {
                "max_concurrent_requests": 10,
                "cache_size": 1000,
                "cache_ttl_seconds": 3600,
                "enable_caching": True
            },
            
            # Security Configuration
            "security": {
                "api_key_required": False,
                "rate_limit_per_minute": 100,
                "allowed_ips": [],
                "enable_cors": True
            }
        }
    
    def _load_config_from_file(self):
        """Load configuration from JSON file if it exists"""
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                print(f"✓ Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"⚠ Error loading config file {self.config_file}: {e}")
                print("Using default configuration")
    
    def _load_config_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database
            "RAG_DB_PATH": ("database", "path"),
            "RAG_COLLECTION_NAME": ("database", "collection_name"),
            
            # Data
            "RAG_DATA_FOLDER": ("data", "folder_path"),
            "RAG_MAX_FILE_SIZE": ("data", "max_file_size_mb"),
            
            # Chunking
            "RAG_CHUNK_SIZE": ("chunking", "chunk_size"),
            "RAG_CHUNK_OVERLAP": ("chunking", "chunk_overlap"),
            
            # API
            "RAG_API_HOST": ("api", "host"),
            "RAG_API_PORT": ("api", "port"),
            
            # Models
            "OPENAI_API_KEY": ("models", "api_key"),
            "RAG_EMBEDDING_MODEL": ("models", "embedding_model"),
            "RAG_LLM_MODEL": ("models", "llm_model"),
            
            # Logging
            "RAG_LOG_LEVEL": ("logging", "level"),
            "RAG_LOG_FILE": ("logging", "file"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key in ["chunk_size", "chunk_overlap", "port", "max_file_size_mb", "max_tokens"]:
                    value = int(value)
                elif key in ["temperature", "max_size_mb"]:
                    value = float(value)
                elif key in ["enable_caching", "api_key_required", "enable_cors"]:
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif key == "cors_origins":
                    value = value.split(',')
                
                self.config[section][key] = value
                print(f"✓ Environment variable {env_var} loaded")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing config"""
        def merge_dicts(d1: dict, d2: dict) -> dict:
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    merge_dicts(d1[key], value)
                else:
                    d1[key] = value
            return d1
        
        merge_dicts(self.config, new_config)
    
    def get(self, section: str, key: str = None) -> Any:
        """Get configuration value"""
        if key is None:
            return self.config.get(section, {})
        
        # Handle nested keys like "metadata_extraction.extract_headings"
        if '.' in key:
            keys = key.split('.')
            value = self.config.get(section, {})
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None
            return value
        else:
            return self.config.get(section, {}).get(key)
    
    def set(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        
        # Handle nested keys like "metadata_extraction.extract_headings"
        if '.' in key:
            keys = key.split('.')
            current = self.config[section]
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Set the final value
            current[keys[-1]] = value
        else:
            self.config[section][key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            import json
            os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else ".", exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config file: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get("database")
    
    def get_data_config(self) -> Dict[str, Any]:
        """Get data configuration"""
        return self.get("data")
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """Get chunking configuration"""
        return self.get("chunking")
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.get("api")
    
    def get_models_config(self) -> Dict[str, Any]:
        """Get models configuration"""
        return self.get("models")
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get("logging")
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get("performance")
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get("security")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate required paths
        data_folder = self.get("data", "folder_path")
        if not os.path.exists(data_folder):
            validation_results["warnings"].append(f"Data folder does not exist: {data_folder}")
        
        # Validate chunking parameters
        chunk_size = self.get("chunking", "chunk_size")
        chunk_overlap = self.get("chunking", "chunk_overlap")
        
        if chunk_size < 100:
            validation_results["errors"].append("Chunk size too small (minimum: 100)")
            validation_results["valid"] = False
        
        if chunk_overlap >= chunk_size:
            validation_results["errors"].append("Chunk overlap must be less than chunk size")
            validation_results["valid"] = False
        
        # Validate API port
        port = self.get("api", "port")
        if not (1 <= port <= 65535):
            validation_results["errors"].append("Invalid API port (must be 1-65535)")
            validation_results["valid"] = False
        
        return validation_results
    
    def print_config(self):
        """Print current configuration"""
        print("=== RAG System Configuration ===")
        for section, values in self.config.items():
            print(f"\n[{section.upper()}]")
            for key, value in values.items():
                print(f"  {key}: {value}")
    
    def create_sample_config(self):
        """Create a sample configuration file"""
        sample_config = {
            "database": {
                "path": "./chroma_db",
                "collection_name": "enhanced-search"
            },
            "data": {
                "folder_path": "./data",
                "supported_extensions": [".txt", ".md"]
            },
            "chunking": {
                "chunk_size": 1024,
                "chunk_overlap": 20
            },
            "api": {
                "host": "0.0.0.0",
                "port": 9000
            }
        }
        
        try:
            import json
            with open("config.sample.json", 'w') as f:
                json.dump(sample_config, f, indent=2)
            print("✓ Sample configuration created: config.sample.json")
        except Exception as e:
            print(f"❌ Error creating sample config: {e}")

# Global configuration instance
config = SystemConfig()

# Convenience functions
def get_config(section: str, key: str = None) -> Any:
    """Get configuration value (convenience function)"""
    return config.get(section, key)

def set_config(section: str, key: str, value: Any):
    """Set configuration value (convenience function)"""
    config.set(section, key, value)

def get_data_folder() -> str:
    """Get data folder path"""
    return get_config("data", "folder_path")

def get_database_path() -> str:
    """Get database path"""
    return get_config("database", "path")

def get_collection_name() -> str:
    """Get collection name"""
    return get_config("database", "collection_name")

def get_chunking_params() -> tuple:
    """Get chunking parameters"""
    return (
        get_config("chunking", "chunk_size"),
        get_config("chunking", "chunk_overlap")
    )
