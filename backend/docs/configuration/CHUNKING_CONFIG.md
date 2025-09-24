# Chunking Configuration Guide

## Overview

The RAG system uses configurable text chunking parameters to split documents into manageable pieces for processing. This guide explains the chunking parameters and how to configure them.

## Chunking Parameters

### `chunk_size`
- **Description**: Maximum number of tokens per chunk
- **Type**: Integer
- **Default**: 1024 tokens (LlamaIndex default)
- **Range**: Typically 100-4000 tokens

### `chunk_overlap`
- **Description**: Number of overlapping tokens between consecutive chunks
- **Type**: Integer
- **Default**: 20 tokens (LlamaIndex default)
- **Range**: Typically 0-500 tokens

## Configuration Methods

### 1. Constructor Parameters

```python
from model_manager import ModelManager
from index_builder import IndexBuilder

# Initialize with custom chunking parameters
model_manager = ModelManager()
index_builder = IndexBuilder(
    model_manager=model_manager,
    collection_name="documents",
    chunk_size=512,      # Smaller chunks (default: 1024)
    chunk_overlap=50     # Less overlap (default: 20)
)
```

### 2. Runtime Updates

```python
# Update chunking parameters after initialization
index_builder.update_chunking_params(
    chunk_size=2048,     # Larger chunks
    chunk_overlap=100    # More overlap
)
```

### 3. API Endpoints

#### Get Current Configuration
```bash
GET /chunking-config
```

Response:
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "llamaindex_defaults": {
    "chunk_size": 1024,
    "chunk_overlap": 20
  },
  "current_vs_defaults": {
    "chunk_size": "1000 (default: 1024)",
    "chunk_overlap": "200 (default: 20)"
  }
}
```

#### Update Configuration
```bash
POST /chunking-config
Content-Type: application/json

{
  "chunk_size": 1500,
  "chunk_overlap": 150
}
```

## Parameter Guidelines

### Chunk Size Recommendations

| Use Case | Recommended Size | Reasoning |
|----------|------------------|-----------|
| **Short documents** | 500-800 tokens | Preserve document structure |
| **General purpose** | 1000-1500 tokens | Balance context and performance |
| **Long documents** | 2000-3000 tokens | Maintain context across sections |
| **Code/Technical** | 800-1200 tokens | Preserve code blocks |

### Overlap Recommendations

| Chunk Size | Recommended Overlap | Reasoning |
|------------|-------------------|-----------|
| **< 500 tokens** | 50-100 tokens | Ensure context continuity |
| **500-1000 tokens** | 100-200 tokens | Standard overlap |
| **1000-2000 tokens** | 200-300 tokens | Maintain section context |
| **> 2000 tokens** | 300-500 tokens | Preserve long-range dependencies |

## Impact on Performance

### Smaller Chunks (500-800 tokens)
- ✅ **Pros**: Faster processing, more precise retrieval
- ❌ **Cons**: May lose context, more chunks to process

### Larger Chunks (1500-3000 tokens)
- ✅ **Pros**: Better context preservation, fewer chunks
- ❌ **Cons**: Slower processing, less precise retrieval

### Overlap Impact
- **Low overlap (10-50 tokens)**: Faster processing, may lose context
- **High overlap (200-500 tokens)**: Better context, slower processing

## Testing Different Configurations

Use the test script to experiment with different settings:

```bash
# Run chunking configuration tests
python tests/run_tests.py chunking

# Run all tests
python tests/run_tests.py
```

## Best Practices

1. **Start with defaults**: Use 1024/20 (LlamaIndex defaults) for most use cases
2. **Test with your data**: Different document types may need different settings
3. **Monitor performance**: Balance chunk size with processing speed
4. **Consider context**: Ensure overlap is sufficient for your use case
5. **Document your choices**: Record why you chose specific parameters

## Examples

### Example 1: News Articles
```python
# Good for news articles with clear paragraphs
chunk_size=800
chunk_overlap=100
```

### Example 2: Technical Documentation
```python
# Good for technical docs with code blocks
chunk_size=1200
chunk_overlap=150
```

### Example 3: Academic Papers
```python
# Good for long academic papers
chunk_size=2000
chunk_overlap=300
```

### Example 4: Chat Messages
```python
# Good for short conversational data
chunk_size=500
chunk_overlap=50
```

## Troubleshooting

### Issue: Chunks too small, losing context
**Solution**: Increase `chunk_size` and `chunk_overlap`

### Issue: Chunks too large, slow processing
**Solution**: Decrease `chunk_size`

### Issue: Poor retrieval quality
**Solution**: Adjust `chunk_overlap` to improve context continuity

### Issue: Memory issues
**Solution**: Decrease `chunk_size` and `chunk_overlap`

## Author

Emad Noorizadeh
