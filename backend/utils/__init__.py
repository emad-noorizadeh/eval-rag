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
Utils Package for RAG Frontend
Author: Emad Noorizadeh
"""

from .metric_utils import (
    calculate_context_utilization_percentage,
    calculate_confidence_score,
    calculate_faithfulness_score,
    calculate_completeness_score
)

from .graph_utils import (
    is_clarification_response,
    is_yes_no_response,
    is_follow_up_question,
    extract_question_intent,
    create_clarification_prompt,
    create_rephrasing_prompt,
    format_context_for_llm,
    extract_key_terms
)

from .chat_utils import (
    format_conversation_history,
    extract_sources_from_chunks,
    create_session_response,
    validate_chat_request,
    format_error_response,
    create_metrics_summary,
    extract_retrieval_metadata,
    create_chat_response,
    sanitize_message,
    detect_message_type
)

from .utils_json import (
    coerce_json
)

# Import from rag_utils for backward compatibility
from .rag_utils import (
    MetadataExtractor,
    format_context_with_metadata
)

# Import from other modules
# Note: HybridMetadataExtractor moved to processors package
# Import directly: from processors.hybrid_metadata_extractor import HybridMetadataExtractor

__all__ = [
    # Metric utilities
    "calculate_context_utilization_percentage",
    "calculate_confidence_score",
    "calculate_faithfulness_score",
    "calculate_completeness_score",
    
    # Graph utilities
    "is_clarification_response",
    "is_yes_no_response",
    "is_follow_up_question",
    "extract_question_intent",
    "create_clarification_prompt",
    "create_rephrasing_prompt",
    "format_context_for_llm",
    "extract_key_terms",
    
    # Chat utilities
    "format_conversation_history",
    "extract_sources_from_chunks",
    "create_session_response",
    "validate_chat_request",
    "format_error_response",
    "create_metrics_summary",
    "extract_retrieval_metadata",
    "create_chat_response",
    "sanitize_message",
    "detect_message_type",
    
    # JSON utilities
    "coerce_json",
    
    # RAG utilities (backward compatibility)
    "MetadataExtractor",
    "format_context_with_metadata"
]
