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
Configuration Package

This package contains all configuration-related modules and files for the RAG system.
It provides centralized configuration management, database settings, and authority scoring.

Modules:
- config: Main configuration management with environment variable support
- database_config: Database connection and ChromaDB configuration
- authority_scores: Authority scoring configuration for document trustworthiness

Author: Emad Noorizadeh
"""

from .config import *
from .database_config import *
from .authority_scores import *

__all__ = [
    # Main configuration
    'Config',
    'load_config',
    'get_config',
    
    # Database configuration
    'DatabaseConfig',
    'get_database_config',
    
    # Authority scores
    'AuthorityScores',
    'get_authority_scores',
    'load_authority_scores_config'
]
