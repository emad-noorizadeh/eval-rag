# Metadata Conversion and Database Storage
**Author: Emad Noorizadeh**

## Overview

This document explains how complex metadata objects are converted to ChromaDB-compatible formats and stored in the database.

## ChromaDB Requirements

ChromaDB has strict metadata value requirements:
- ✅ `str` (string)
- ✅ `int` (integer) 
- ✅ `float` (floating point)
- ✅ `None` (null)
- ❌ `List[str]` (lists)
- ❌ `Dict[str, Any]` (dictionaries)
- ❌ `Optional[str]` (optional types)

## Conversion Strategy

### 1. List to JSON String Conversion

**Problem**: Lists like `product_entities` and `categories` are not ChromaDB-compatible.

**Solution**: Convert lists to JSON strings.

```python
# Original data structure
product_entities = ["Bank of America Preferred Rewards", "Gold", "Platinum", "Diamond"]
categories = ["Banking", "Rewards Program", "Financial Services"]

# ChromaDB-compatible conversion
"product_entities": json.dumps(product_entities) if product_entities else "[]"
"categories": json.dumps(categories) if categories else "[]"

# Result in database
"product_entities": '["Bank of America Preferred Rewards", "Gold", "Platinum", "Diamond"]'
"categories": '["Banking", "Rewards Program", "Financial Services"]'
```

### 2. Optional Values to Empty String

**Problem**: Optional fields like dates might be `None`, which ChromaDB accepts but we prefer empty strings for consistency.

**Solution**: Convert `None` to empty string.

```python
# Original data structure
published_at = None
updated_at = "2024-03-20"

# ChromaDB-compatible conversion
"published_at": doc_metadata.published_at or ""
"updated_at": doc_metadata.updated_at or ""

# Result in database
"published_at": ""
"updated_at": "2024-03-20"
```

### 3. Complex Objects Serialization

**Problem**: Complex nested objects need to be flattened or serialized.

**Solution**: Use JSON serialization for complex objects.

```python
# Original data structure
section_path = ["Rewards built around you", "Eligibility", "Tiers"]

# ChromaDB-compatible conversion
"section_path": json.dumps(section_path) if section_path else "[]"

# Result in database
"section_path": '["Rewards built around you", "Eligibility", "Tiers"]'
```

## Database Storage Examples

### Document-Level Metadata in ChromaDB

```json
{
  "doc_id": "doc_4fc4cb4e",
  "canonical_url": "https://promotions.bankofamerica.com/preferredrewards/en",
  "domain": "promotions.bankofamerica.com",
  "doc_type": "promo",
  "language": "en",
  "published_at": "2024-01-15",
  "updated_at": "2024-03-20",
  "effective_date": "2024-01-01",
  "expires_at": "",
  "authority_score": 0.7,
  "geo_scope": "US",
  "currency": "USD",
  "product_entities": "[\"Bank of America Preferred Rewards Program\", \"Gold\", \"Platinum\", \"Diamond\"]",
  "title": "Bank of America Preferred Rewards Program",
  "categories": "[\"Banking\", \"Rewards Program\", \"Financial Services\"]",
  "file_path": "/path/to/preferred_rewards.txt",
  "file_type": ".txt",
  "file_name": "preferred_rewards.txt",
  "chunks_count": 7,
  "created_at": "2025-09-18T00:19:11.608826",
  "updated_at_processing": "2025-09-18T00:19:11.608826"
}
```

### Chunk-Level Metadata in ChromaDB

```json
{
  "chunk_id": "doc_4fc4cb4e_chunk_0",
  "doc_id": "doc_4fc4cb4e",
  "section_path": "[\"Rewards built around you\", \"Eligibility\"]",
  "start_line": 5,
  "end_line": 5,
  "start_char": 100,
  "end_char": 200,
  "token_count": 15,
  "has_numbers": true,
  "has_currency": true,
  "embedding_version": "text-embedding-3-small",
  "doc_metadata_ref": "doc_4fc4cb4e",
  "source": "/path/to/preferred_rewards.txt",
  "title": "Bank of America Preferred Rewards Program",
  "doc_type": "promo",
  "domain": "promotions.bankofamerica.com",
  "authority_score": 0.7,
  "product_entities": "[\"Bank of America Preferred Rewards Program\", \"Gold\", \"Platinum\", \"Diamond\"]",
  "categories": "[\"Banking\", \"Rewards Program\", \"Financial Services\"]"
}
```

## Reference-Based Linking

### How References Work

1. **Document Metadata**: Stored in separate JSON file (`document_metadata.json`)
2. **Chunk Metadata**: Stored in ChromaDB with `doc_id` reference
3. **Lookup Process**: Use `doc_id` to fetch full document metadata

```python
# Chunk metadata in ChromaDB
chunk_metadata = {
    "chunk_id": "doc_4fc4cb4e_chunk_0",
    "doc_id": "doc_4fc4cb4e",  # Reference to document
    "section_path": "[\"Eligibility\"]",
    # ... other chunk-specific data
}

# Document metadata in JSON file
document_metadata = {
    "doc_4fc4cb4e": {
        "doc_id": "doc_4fc4cb4e",
        "title": "Bank of America Preferred Rewards Program",
        "product_entities": ["Bank of America Preferred Rewards Program", "Gold", "Platinum", "Diamond"],
        "categories": ["Banking", "Rewards Program", "Financial Services"],
        "authority_score": 0.7,
        # ... full document metadata
    }
}
```

## Data Retrieval Process

### 1. Get Chunk from ChromaDB
```python
# Query ChromaDB for similar chunks
results = collection.query(
    query_texts=["gold tier requirements"],
    n_results=5
)

# Get chunk metadata
chunk_metadata = results['metadatas'][0][0]
chunk_id = chunk_metadata['chunk_id']
doc_id = chunk_metadata['doc_id']  # Reference to document
```

### 2. Get Full Document Metadata
```python
# Use doc_id to get full document metadata
full_doc_metadata = enhanced_processor.get_document_metadata(doc_id)

# Parse JSON strings back to Python objects
product_entities = json.loads(chunk_metadata['product_entities'])
categories = json.loads(chunk_metadata['categories'])
```

### 3. Reconstruct Full Context
```python
# Combine chunk and document metadata
full_context = {
    "chunk_text": chunk_text,
    "chunk_metadata": chunk_metadata,
    "document_metadata": full_doc_metadata,
    "parsed_entities": product_entities,
    "parsed_categories": categories
}
```

## Benefits of This Approach

### 1. **ChromaDB Compatibility**
- All metadata values are ChromaDB-compatible types
- No conversion errors during storage
- Efficient querying and filtering

### 2. **Reference Efficiency**
- No duplication of document-level data in chunks
- Fast lookups via `doc_id` references
- Memory efficient storage

### 3. **Data Integrity**
- JSON serialization preserves data structure
- Easy to parse back to original objects
- Consistent data format across all chunks

### 4. **Query Performance**
- ChromaDB can efficiently filter on simple types
- Complex data available via reference lookup
- Best of both worlds: fast queries + rich metadata

## Code Examples

### Conversion Functions

```python
def make_chromadb_compatible(metadata_dict):
    """Convert metadata to ChromaDB-compatible format"""
    compatible = {}
    
    for key, value in metadata_dict.items():
        if isinstance(value, list):
            # Convert lists to JSON strings
            compatible[key] = json.dumps(value) if value else "[]"
        elif value is None:
            # Convert None to empty string
            compatible[key] = ""
        elif isinstance(value, (str, int, float)):
            # Keep as-is
            compatible[key] = value
        else:
            # Serialize complex objects
            compatible[key] = json.dumps(value)
    
    return compatible

def parse_chromadb_metadata(metadata_dict):
    """Parse ChromaDB metadata back to original format"""
    parsed = {}
    
    for key, value in metadata_dict.items():
        if key in ['product_entities', 'categories', 'section_path']:
            # Parse JSON strings back to lists
            try:
                parsed[key] = json.loads(value) if value else []
            except json.JSONDecodeError:
                parsed[key] = []
        else:
            parsed[key] = value
    
    return parsed
```

## Summary

The metadata conversion system ensures:

1. **ChromaDB Compatibility**: All values are `str`, `int`, `float`, or `None`
2. **Data Preservation**: Complex objects serialized as JSON strings
3. **Reference Efficiency**: Document metadata stored separately, chunks reference via `doc_id`
4. **Easy Retrieval**: Simple parsing functions to reconstruct original data
5. **Query Performance**: ChromaDB can efficiently filter on simple types while maintaining rich metadata access

This approach provides the best balance of ChromaDB compatibility, storage efficiency, and rich metadata capabilities.
