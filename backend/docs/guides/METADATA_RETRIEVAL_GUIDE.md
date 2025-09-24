# Metadata-Enhanced Retrieval with LlamaIndex

## Overview

This guide explains how to incorporate comprehensive metadata extraction into the RAG system and how LlamaIndex uses metadata for enhanced retrieval.

## Metadata Types

### 1. Document-Level Metadata
- **Source information**: File path, document type, creation date
- **Content analysis**: Title, summary, sentiment, topics, entities
- **Structure information**: Word count, line count, headings
- **Processing info**: Extraction method, confidence scores, timestamps

### 2. Chunk-Level Metadata
- **Chunk identification**: Unique chunk ID, position in document
- **Content analysis**: Chunk-specific summary, sentiment, topics
- **Structural info**: Heading level, contains links/emails/dates
- **Context info**: Source document, document title, document type

## How LlamaIndex Uses Metadata

### 1. **Vector Similarity + Metadata Filtering**
```python
# Basic vector search
results = retriever.retrieve(query)

# With metadata filtering
filtered_results = [
    node for node in results 
    if node.metadata.get('chunk_sentiment') == 'positive'
]
```

### 2. **Metadata-Aware Retrieval Strategies**

#### **By Document Source**
```python
# Search within specific document
doc_results = builder.search_by_document("banking services", "doc_1.txt")
```

#### **By Sentiment**
```python
# Search for positive content
positive_results = builder.search_by_sentiment("banking", "positive")
```

#### **By Topic**
```python
# Search within specific topics
banking_results = builder.search_by_topic("services", "Banking")
```

#### **By Content Type**
```python
# Search chunks with headings
with_headings = [
    node for node in results 
    if node.metadata.get('has_headings', False)
]
```

### 3. **Combined Filtering**
```python
# Multiple metadata filters
filtered_results = [
    node for node in all_results 
    if (node.metadata.get('chunk_sentiment') == 'positive' and 
        node.metadata.get('source_document') == 'doc_1.txt' and
        node.metadata.get('confidence_score', 0) > 0.8)
]
```

## Implementation Architecture

### 1. **Enhanced Index Builder**
```python
class EnhancedIndexBuilder:
    def __init__(self, model_manager):
        self.document_processor = EnhancedDocumentProcessor()
        self.chunk_extractor = ChunkMetadataExtractor()
    
    def build_index_from_folder(self, extract_chunk_metadata=True):
        # 1. Load documents with file metadata
        # 2. Extract document-level metadata
        # 3. Parse into chunks
        # 4. Extract chunk-level metadata
        # 5. Build vector index with rich metadata
```

### 2. **Chunk Metadata Extractor**
```python
class ChunkMetadataExtractor:
    def extract_chunk_metadata(self, chunk_text, chunk_id, document_metadata):
        # Extract chunk-specific metadata using hybrid approach
        # Combine with document metadata
        # Return comprehensive chunk metadata
```

### 3. **Metadata-Aware Retrieval**
```python
def search_with_metadata(self, query, metadata_filters=None):
    # Perform vector search
    # Apply metadata filters
    # Return filtered results
```

## Metadata Fields

### Document-Level Fields
```json
{
  "source": "doc_1.txt",
  "title": "Bank of America Preferred Rewards",
  "file_type": ".txt",
  "summary": "Document summary...",
  "sentiment": "positive",
  "topics": "Banking, Financial Services",
  "entities_organizations": "Bank of America",
  "word_count": 3419,
  "line_count": 480
}
```

### Chunk-Level Fields
```json
{
  "chunk_id": "doc_1_chunk_0",
  "source_document": "doc_1.txt",
  "document_title": "Bank of America Preferred Rewards",
  "chunk_summary": "Chunk-specific summary...",
  "chunk_sentiment": "positive",
  "chunk_topics": "Rewards Program",
  "chunk_key_phrases": "preferred rewards, benefits",
  "has_headings": true,
  "heading_level": 1,
  "contains_links": true,
  "contains_emails": false,
  "confidence_score": 0.9
}
```

## Retrieval Strategies

### 1. **Semantic + Metadata Filtering**
- Use vector similarity for semantic relevance
- Apply metadata filters for precision
- Combine both for optimal results

### 2. **Metadata-Only Filtering**
- Filter by document source
- Filter by content type (headings, links, etc.)
- Filter by confidence scores

### 3. **Hybrid Approaches**
- Start with broad semantic search
- Apply metadata filters for refinement
- Use metadata for result ranking

## Benefits of Metadata-Enhanced Retrieval

### 1. **Improved Precision**
- Filter out irrelevant content by source
- Focus on specific content types
- Use confidence scores for quality control

### 2. **Better Context Understanding**
- Know which document chunks come from
- Understand content structure and type
- Leverage sentiment and topic information

### 3. **Enhanced User Experience**
- Provide source attribution
- Enable targeted searches
- Support complex query requirements

### 4. **Advanced Analytics**
- Analyze content distribution
- Track sentiment across documents
- Monitor confidence scores

## Usage Examples

### Basic Search with Metadata
```python
# Initialize enhanced builder
builder = EnhancedIndexBuilder(model_manager)

# Build index with metadata
stats = builder.build_index_from_folder(extract_chunk_metadata=True)

# Search with metadata filtering
results = builder.search_with_metadata(
    query="banking services",
    metadata_filters={"chunk_sentiment": "positive"}
)
```

### Advanced Filtering
```python
# Search positive content from specific document
results = builder.search_by_document("rewards", "doc_1.txt")
positive_results = [
    node for node in results 
    if node.metadata.get('chunk_sentiment') == 'positive'
]
```

### Metadata Analysis
```python
# Get all chunks from a document
doc_chunks = builder.get_document_chunks("doc_1.txt")

# Analyze sentiment distribution
sentiments = [chunk.metadata.get('chunk_sentiment') for chunk in doc_chunks]
topic_counts = {}
for chunk in doc_chunks:
    topics = chunk.metadata.get('chunk_topics', '')
    if topics:
        for topic in topics.split(', '):
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
```

## Configuration

### Enable Chunk Metadata Extraction
```python
# In config.json
{
  "data": {
    "llm_metadata_extraction": {
      "enabled": true,
      "method": "hybrid"
    }
  }
}
```

### Chunking Parameters
```python
# Adjust chunk size and overlap
{
  "chunking": {
    "chunk_size": 1024,
    "chunk_overlap": 20
  }
}
```

## Performance Considerations

### 1. **Metadata Storage**
- Metadata is stored with each chunk in the vector database
- ChromaDB handles metadata efficiently
- Consider metadata size vs. retrieval performance

### 2. **Processing Time**
- Document-level metadata: ~2-3s per document
- Chunk-level metadata: ~1-2s per chunk
- Total processing time scales with document count and chunk count

### 3. **Memory Usage**
- Rich metadata increases memory usage
- Consider metadata field limits
- Use lazy loading for large datasets

## Best Practices

### 1. **Metadata Design**
- Keep metadata fields relevant to retrieval needs
- Use consistent naming conventions
- Consider metadata size limits

### 2. **Retrieval Strategy**
- Start with semantic search
- Apply metadata filters for refinement
- Use confidence scores for quality control

### 3. **Performance Optimization**
- Cache frequently used metadata
- Use efficient filtering algorithms
- Consider metadata indexing strategies

## Conclusion

Metadata-enhanced retrieval provides powerful capabilities for building sophisticated RAG systems. By combining document-level and chunk-level metadata with vector similarity search, you can achieve:

- **Higher precision** through targeted filtering
- **Better context understanding** through rich metadata
- **Enhanced user experience** through intelligent retrieval
- **Advanced analytics** through metadata analysis

The hybrid approach ensures both deterministic reliability and semantic understanding, making it suitable for production RAG applications.

## Author

Emad Noorizadeh
