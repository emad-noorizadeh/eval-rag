# Enhanced Index Builder Migration Guide

## Overview

The `EnhancedIndexBuilder` is now fully configurable and can serve as a drop-in replacement for the basic `IndexBuilder` with optional advanced features.

## Configuration Options

### Feature Flags

- **`enable_enhanced_metadata`**: Enable document-level metadata extraction
- **`enable_chunk_metadata`**: Enable chunk-level metadata extraction  
- **`enable_metadata_filtering`**: Enable metadata-based search filtering
- **`enable_advanced_search`**: Enable advanced search methods

### Pre-configured Modes

#### 1. Basic Mode (IndexBuilder Compatible)
```python
from enhanced_index_builder import create_basic_index_builder

# Same as IndexBuilder - embedding only
builder = create_basic_index_builder(model_manager)
```

#### 2. Enhanced Mode (Full Features)
```python
from enhanced_index_builder import create_enhanced_index_builder

# All advanced features enabled
builder = create_enhanced_index_builder(model_manager)
```

#### 3. Custom Mode (Selective Features)
```python
from enhanced_index_builder import create_custom_index_builder

# Custom configuration
builder = create_custom_index_builder(
    model_manager,
    enhanced_metadata=True,
    chunk_metadata=False,
    metadata_filtering=True,
    advanced_search=False
)
```

## Migration from IndexBuilder

### Step 1: Update Imports
```python
# Before
from index_builder import IndexBuilder

# After
from enhanced_index_builder import create_basic_index_builder
```

### Step 2: Update Instantiation
```python
# Before
index_builder = IndexBuilder(model_manager)

# After (basic mode - same functionality)
index_builder = create_basic_index_builder(model_manager)

# Or (enhanced mode - more features)
index_builder = create_enhanced_index_builder(model_manager)
```

### Step 3: API Compatibility
The `EnhancedIndexBuilder` maintains full API compatibility with `IndexBuilder`:

```python
# All these methods work the same way
builder.build_index_from_folder()
builder.add_document(text, metadata)
builder.search(query, n_results)
builder.delete_document(doc_id)
```

## Advanced Features (When Enabled)

### Metadata Filtering
```python
# Search within specific documents
results = builder.search_by_document(query, "document_name.txt")

# Search by topic
results = builder.search_by_topic(query, "banking")

# Search by sentiment
results = builder.search_by_sentiment(query, "positive")
```

### Advanced Search
```python
# Search with metadata filters
results = builder.search_with_metadata(
    query="banking services",
    similarity_top_k=10,
    metadata_filters={"chunk_topics": "financial"}
)
```

### Chunk Metadata
```python
# Get metadata for specific chunks
chunk_metadata = builder.get_chunk_metadata("chunk_id")

# Get all chunks from a document
document_chunks = builder.get_document_chunks("document_name.txt")
```

## Performance Considerations

### Basic Mode
- **Memory**: Minimal overhead
- **Speed**: Same as IndexBuilder
- **Features**: Embedding search only

### Enhanced Mode
- **Memory**: Higher due to metadata storage
- **Speed**: Slightly slower due to metadata processing
- **Features**: Full metadata extraction and filtering

### Custom Mode
- **Memory**: Configurable based on enabled features
- **Speed**: Configurable based on enabled features
- **Features**: Only what you enable

## Configuration Examples

### Development/Testing
```python
# Fast, basic functionality
builder = create_basic_index_builder(model_manager)
```

### Production with Metadata
```python
# Enhanced but not too heavy
builder = create_custom_index_builder(
    model_manager,
    enhanced_metadata=True,
    chunk_metadata=False,  # Skip heavy chunk processing
    metadata_filtering=True,
    advanced_search=True
)
```

### Full Featured
```python
# All features enabled
builder = create_enhanced_index_builder(model_manager)
```

## Backward Compatibility

The `EnhancedIndexBuilder` is designed to be 100% backward compatible with `IndexBuilder`. You can:

1. **Replace gradually**: Start with basic mode, enable features as needed
2. **Keep existing code**: All existing method calls work unchanged
3. **Add features incrementally**: Enable one feature at a time

## Testing

Run the test script to verify different configurations:

```bash
python test_configurable_index_builder.py
```

This will test all three modes and show you the configuration output.
