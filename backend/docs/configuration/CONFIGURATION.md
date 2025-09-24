# Configuration System Guide

## Overview

The RAG system now includes a comprehensive configuration management system that allows you to customize all aspects of the system through configuration files, environment variables, or programmatic settings.

## Configuration Sources (Priority Order)

1. **Environment Variables** (Highest Priority)
2. **Configuration File** (`config.json`)
3. **Default Values** (Lowest Priority)

## Quick Start

### Using Default Configuration
```python
from index_builder import IndexBuilder
from model_manager import ModelManager

# Uses all default configuration values
model_manager = ModelManager()
index_builder = IndexBuilder(model_manager)  # Uses config defaults
```

### Using Configuration File
1. Copy `config.sample.json` to `config.json`
2. Modify values as needed
3. The system will automatically load your configuration

### Using Environment Variables
```bash
export RAG_DATA_FOLDER="./my_data"
export RAG_CHUNK_SIZE=2048
export RAG_API_PORT=8000
```

## Configuration Sections

### Database Configuration
```json
{
  "database": {
    "path": "./chroma_db",
    "collection_name": "enhanced-search",
    "backup_path": "./chroma_db_backup"
  }
}
```

**Environment Variables:**
- `RAG_DB_PATH`: Database storage path
- `RAG_COLLECTION_NAME`: Collection name

### Data Configuration
```json
{
  "data": {
    "folder_path": "./data",
    "supported_extensions": [".txt", ".md", ".pdf"],
    "max_file_size_mb": 50,
    "encoding": "utf-8"
  }
}
```

**Environment Variables:**
- `RAG_DATA_FOLDER`: Default data folder path
- `RAG_MAX_FILE_SIZE`: Maximum file size in MB

### Chunking Configuration
```json
{
  "chunking": {
    "chunk_size": 1024,
    "chunk_overlap": 20,
    "min_chunk_size": 100,
    "max_chunk_size": 4000
  }
}
```

**Environment Variables:**
- `RAG_CHUNK_SIZE`: Chunk size in tokens
- `RAG_CHUNK_OVERLAP`: Chunk overlap in tokens

### API Configuration
```json
{
  "api": {
    "host": "0.0.0.0",
    "port": 9000,
    "cors_origins": ["http://localhost:4000"],
    "max_request_size": 104857600,
    "timeout": 30
  }
}
```

**Environment Variables:**
- `RAG_API_HOST`: API host address
- `RAG_API_PORT`: API port number

### Model Configuration
```json
{
  "models": {
    "embedding_model": "text-embedding-ada-002",
    "llm_model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Environment Variables:**
- `OPENAI_API_KEY`: OpenAI API key
- `RAG_EMBEDDING_MODEL`: Embedding model name
- `RAG_LLM_MODEL`: LLM model name

## Usage Examples

### Programmatic Configuration
```python
from config import get_config, set_config, get_data_folder

# Get configuration values
data_folder = get_data_folder()
chunk_size = get_config("chunking", "chunk_size")

# Set configuration values
set_config("chunking", "chunk_size", 2048)
set_config("data", "folder_path", "./my_data")
```

### Using Configuration in Code
```python
from index_builder import IndexBuilder
from model_manager import ModelManager

# IndexBuilder now uses configuration defaults
model_manager = ModelManager()
index_builder = IndexBuilder(model_manager)  # Uses config defaults

# Build index using configured data folder
result = index_builder.build_index_from_folder()  # Uses config default folder
```

### API Endpoints with Configuration
```python
# Build index using configured default folder
POST /build-index
# No folder_path needed - uses configuration default

# Build index using specific folder
POST /build-index?folder_path=/path/to/documents
```

## Environment Variables Reference

| Variable | Section | Key | Type | Default |
|----------|---------|-----|------|---------|
| `RAG_DB_PATH` | database | path | string | `./chroma_db` |
| `RAG_COLLECTION_NAME` | database | collection_name | string | `enhanced-search` |
| `RAG_DATA_FOLDER` | data | folder_path | string | `./data` |
| `RAG_MAX_FILE_SIZE` | data | max_file_size_mb | int | `50` |
| `RAG_CHUNK_SIZE` | chunking | chunk_size | int | `1024` |
| `RAG_CHUNK_OVERLAP` | chunking | chunk_overlap | int | `20` |
| `RAG_API_HOST` | api | host | string | `0.0.0.0` |
| `RAG_API_PORT` | api | port | int | `9000` |
| `OPENAI_API_KEY` | models | api_key | string | - |
| `RAG_EMBEDDING_MODEL` | models | embedding_model | string | `text-embedding-ada-002` |
| `RAG_LLM_MODEL` | models | llm_model | string | `gpt-3.5-turbo` |
| `RAG_LOG_LEVEL` | logging | level | string | `INFO` |
| `RAG_LOG_FILE` | logging | file | string | `./logs/rag_system.log` |

## Configuration Validation

The system includes built-in validation:

```python
from config import config

validation_results = config.validate_config()
if not validation_results['valid']:
    print("Configuration errors:", validation_results['errors'])
```

## Best Practices

### 1. Use Environment Variables for Deployment
```bash
# Production deployment
export RAG_DATA_FOLDER="/app/data"
export RAG_DB_PATH="/app/db"
export RAG_API_PORT=8000
```

### 2. Use Configuration Files for Development
```json
{
  "data": {
    "folder_path": "./dev_data"
  },
  "chunking": {
    "chunk_size": 512,
    "chunk_overlap": 50
  }
}
```

### 3. Validate Configuration
Always validate configuration before starting the system:
```python
from config import config

validation = config.validate_config()
if not validation['valid']:
    raise ValueError(f"Configuration errors: {validation['errors']}")
```

### 4. Use Convenience Functions
```python
from config import get_data_folder, get_database_path, get_chunking_params

# Instead of
folder = get_config("data", "folder_path")

# Use
folder = get_data_folder()
```

## Migration from Hardcoded Values

### Before (Hardcoded)
```python
index_builder = IndexBuilder(
    model_manager,
    collection_name="documents",
    db_path="./chroma_db",
    chunk_size=1000,
    chunk_overlap=200
)
```

### After (Configuration-based)
```python
# Uses configuration defaults
index_builder = IndexBuilder(model_manager)

# Or override specific values
index_builder = IndexBuilder(
    model_manager,
    collection_name="custom_collection"  # Only override what you need
)
```

## Troubleshooting

### Configuration Not Loading
1. Check if `config.json` exists and is valid JSON
2. Verify environment variable names (must start with `RAG_`)
3. Check file permissions

### Validation Errors
1. Run configuration validation: `python -c "from config import config; print(config.validate_config())"`
2. Check chunking parameters (overlap must be < size)
3. Verify file paths exist

### Environment Variables Not Working
1. Ensure variables start with `RAG_` prefix
2. Check variable names match the mapping table
3. Restart the application after setting variables

## Author

Emad Noorizadeh
