# File Usage Analysis

## Currently Active Files (In Production Use)

### Core Production Files
- ✅ **`main.py`** - FastAPI application (main entry point)
- ✅ **`config.py`** - Configuration management
- ✅ **`model_manager.py`** - LLM model management
- ✅ **`index_builder.py`** - Document indexing
- ✅ **`rag.py`** - Standard RAG system
- ✅ **`session_manager.py`** - Session management
- ✅ **`database_config.py`** - Database configuration
- ✅ **`rag_utils.py`** - RAG utility functions

### Active Chat Agents
- ✅ **`chat_agent.py`** - **ACTIVELY USED** in session_manager.py
- ✅ **`chat_agent_v2.py`** - **ACTIVELY USED** in main.py `/chat-v2` endpoint
- ❌ **`chat_agent_hybrid.py`** - **NOT USED** (no imports found)

### Active Router/Agent Systems
- ✅ **`router_graph_v3.py`** - **ACTIVELY USED** in chat_agent_v2.py
- ❌ **`router_graph.py`** - **NOT USED** (no imports found)
- ❌ **`router_graph_v2.py`** - **NOT USED** (no imports found)
- ❌ **`agent_graph.py`** - **NOT USED** (only imported by chat_agent.py, but chat_agent.py is only used in session_manager)

### Active Metadata System
- ✅ **`enhanced_metadata_extractor.py`** - **ACTIVELY USED** in main.py endpoints
- ✅ **`enhanced_document_processor.py`** - **ACTIVELY USED** in index_builder.py
- ✅ **`hybrid_metadata_extractor.py`** - **ACTIVELY USED** in enhanced_document_processor.py
- ✅ **`llm_metadata_extractor.py`** - **ACTIVELY USED** in hybrid_metadata_extractor.py

### Active Hybrid Retrieval System
- ✅ **`hybrid_retriever/`** - **ACTIVELY USED** in rag_hybrid.py
- ✅ **`rag_hybrid.py`** - **ACTIVELY USED** in tests and chat_agent_hybrid.py
- ✅ **`authority_scores.py`** - **ACTIVELY USED** in enhanced_metadata_extractor.py

### Active Utility Files
- ✅ **`utils_json.py`** - **ACTIVELY USED** in router_graph_v3.py

## Obsolete/Unused Files (Can Be Removed)

### Unused Chat Agents
- ❌ **`chat_agent_hybrid.py`** - No imports found, not used anywhere
- ❌ **`agent_graph.py`** - Only imported by chat_agent.py, but not used in main flow

### Unused Router Systems
- ❌ **`router_graph.py`** - No imports found
- ❌ **`router_graph_v2.py`** - No imports found

### Unused Test/Debug Files (Already Moved to tests/)
- ❌ All `test_*.py` files - Moved to tests/
- ❌ All `debug_*.py` files - Moved to tests/
- ❌ All `inspect_*.py` files - Moved to tests/

## Current API Endpoints Analysis

### Main Chat Endpoints
1. **`/chat`** - Uses `session_manager` → `chat_agent.py` (ChatAgent)
2. **`/chat-v2`** - Uses `chat_agent_v2.py` (ChatAgentV2) → `router_graph_v3.py`

### Other Active Endpoints
- `/sessions/*` - Session management
- `/documents/*` - Document management
- `/build-index` - Index building
- `/query` - Document querying
- `/enhanced-metadata/*` - Enhanced metadata system
- `/data-files/*` - File management

## Recommendations

### Files to Remove (Obsolete)
```bash
# These files are not used anywhere and can be safely removed:
rm chat_agent_hybrid.py
rm agent_graph.py
rm router_graph.py
rm router_graph_v2.py
```

### Files to Keep (Active)
- All files in the "Currently Active Files" section above
- All files in `tests/` directory
- All documentation files (`*.md`)

### Current Architecture
```
main.py
├── /chat → session_manager → chat_agent.py
├── /chat-v2 → chat_agent_v2.py → router_graph_v3.py
├── /documents → index_builder.py → enhanced_document_processor.py
└── /enhanced-metadata → enhanced_metadata_extractor.py
```

## Summary

**Active Files**: 15+ core files
**Obsolete Files**: 4 files can be removed
**Test Files**: 100+ files (moved to tests/)

The codebase is well-organized with clear separation between active production code and obsolete/unused files.
