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
Security Package
Author: Emad Noorizadeh

Security-related modules for the RAG system including:
- Telemetry disabling
- URL guardrails
- Security checks
- Network monitoring
"""

from .disable_telemetry import (
    disable_all_telemetry,
    configure_local_logging_only,
    disable_network_telemetry,
    disable_all_external_connections,
    create_network_monitor
)

from .url_guardrail import (
    guardrail,
    block_external_requests,
    create_network_monitor as create_url_monitor
)

from .security_check import main as run_security_check

__all__ = [
    # Telemetry disabling
    'disable_all_telemetry',
    'configure_local_logging_only',
    'disable_network_telemetry',
    'disable_all_external_connections',
    'create_network_monitor',
    
    # URL guardrails
    'guardrail',
    'block_external_requests',
    'create_url_monitor',
    
    # Security checks
    'run_security_check'
]
