# How LlamaIndex Uses Metadata for Retrieval

## Overview

LlamaIndex uses metadata in several sophisticated ways to enhance retrieval beyond simple vector similarity. This document explains the specific mechanisms and provides practical examples.

## 1. Metadata Storage Architecture

### Vector + Metadata Storage
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Text Chunk    │───▶│  Vector Embedding│    │    Metadata     │
│                 │    │                 │    │                 │
│ "Banking services│    │ [0.1, 0.3, ...]│    │ {source: "doc1",│
│  and rewards..."│    │                 │    │  sentiment: "+",│
│                 │    │                 │    │  category: "B" }│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Key Points:**
- Each chunk is stored as a vector in the database
- Metadata is stored alongside each vector
- During retrieval, both vector similarity and metadata are available
- Metadata is accessible for filtering, ranking, and analytics

## 2. Retrieval Mechanisms

### A. Basic Vector Similarity Retrieval
```python
# 1. Convert query to vector
query_vector = embedding_model.encode("banking services")

# 2. Find similar vectors in database
similar_vectors = vector_store.similarity_search(query_vector, top_k=10)

# 3. Return chunks with similarity scores
results = [
    NodeWithScore(
        node=chunk,
        score=similarity_score,
        metadata=chunk.metadata  # Metadata available here
    )
]
```

### B. Metadata Filtering
```python
# Get vector similarity results
nodes = retriever.retrieve("banking services")

# Filter by metadata criteria
banking_chunks = [
    node for node in nodes 
    if node.metadata.get('category') == 'Banking'
]

positive_chunks = [
    node for node in nodes 
    if node.metadata.get('sentiment') == 'positive'
]

# Combined filtering
filtered_chunks = [
    node for node in nodes
    if (node.metadata.get('category') == 'Banking' and
        node.metadata.get('sentiment') == 'positive' and
        node.metadata.get('has_headings', False))
]
```

### C. Custom Ranking with Metadata
```python
def custom_ranking_score(node):
    base_score = node.score
    
    # Boost for positive sentiment
    if node.metadata.get('sentiment') == 'positive':
        base_score += 0.1
    
    # Boost for banking category
    if node.metadata.get('category') == 'Banking':
        base_score += 0.05
    
    # Boost for chunks with headings
    if node.metadata.get('has_headings', False):
        base_score += 0.03
    
    return base_score

# Apply custom ranking
ranked_nodes = sorted(nodes, key=custom_ranking_score, reverse=True)
```

## 3. Metadata Types and Usage

### Document-Level Metadata
```json
{
  "source": "doc_1.txt",
  "title": "Bank of America Preferred Rewards",
  "category": "Banking",
  "sentiment": "positive",
  "topics": "Rewards, Benefits",
  "word_count": 3419,
  "has_headings": true,
  "contains_emails": false,
  "created_at": "2024-01-15"
}
```

### Chunk-Level Metadata
```json
{
  "chunk_id": "doc_1_chunk_0",
  "chunk_index": 0,
  "chunk_sentiment": "positive",
  "chunk_topics": "Rewards, Benefits",
  "chunk_category": "Banking",
  "has_headings": true,
  "contains_email": false,
  "word_count": 90
}
```

## 4. Practical Retrieval Strategies

### Strategy 1: Source-Specific Search
```python
# Search within specific document
def search_by_document(query, document_source):
    all_results = retriever.retrieve(query)
    return [
        node for node in all_results
        if node.metadata.get('source') == document_source
    ]

# Usage
doc1_results = search_by_document("rewards program", "doc_1.txt")
```

### Strategy 2: Sentiment-Based Search
```python
# Search for positive content
def search_by_sentiment(query, sentiment):
    all_results = retriever.retrieve(query)
    return [
        node for node in all_results
        if node.metadata.get('sentiment') == sentiment
    ]

# Usage
positive_results = search_by_sentiment("banking", "positive")
```

### Strategy 3: Content Type Search
```python
# Search chunks with specific content types
def search_by_content_type(query, content_type):
    all_results = retriever.retrieve(query)
    
    if content_type == "headings":
        return [node for node in all_results if node.metadata.get('has_headings', False)]
    elif content_type == "emails":
        return [node for node in all_results if node.metadata.get('contains_email', False)]
    # ... other content types
```

### Strategy 4: Multi-Criteria Search
```python
# Complex filtering with multiple criteria
def advanced_search(query, filters):
    all_results = retriever.retrieve(query)
    
    filtered_results = all_results
    for key, value in filters.items():
        filtered_results = [
            node for node in filtered_results
            if node.metadata.get(key) == value
        ]
    
    return filtered_results

# Usage
results = advanced_search("banking services", {
    "category": "Banking",
    "sentiment": "positive",
    "has_headings": True
})
```

## 5. Metadata Analytics

### Content Distribution Analysis
```python
def analyze_content_distribution(nodes):
    # Category distribution
    categories = [node.metadata.get('category', 'unknown') for node in nodes]
    category_counts = {}
    for cat in categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Sentiment distribution
    sentiments = [node.metadata.get('sentiment', 'unknown') for node in nodes]
    sentiment_counts = {}
    for sent in sentiments:
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1
    
    return {
        "categories": category_counts,
        "sentiments": sentiment_counts
    }
```

### Quality Metrics
```python
def analyze_quality_metrics(nodes):
    # Confidence scores
    confidence_scores = [node.metadata.get('confidence_score', 0) for node in nodes]
    avg_confidence = sum(confidence_scores) / len(confidence_scores)
    
    # Content completeness
    with_headings = sum(1 for node in nodes if node.metadata.get('has_headings', False))
    with_emails = sum(1 for node in nodes if node.metadata.get('contains_email', False))
    
    return {
        "avg_confidence": avg_confidence,
        "headings_ratio": with_headings / len(nodes),
        "emails_ratio": with_emails / len(nodes)
    }
```

## 6. Integration with RAG Pipeline

### Enhanced RAG with Metadata
```python
class MetadataEnhancedRAG:
    def __init__(self, index_builder, model_manager):
        self.index_builder = index_builder
        self.model_manager = model_manager
        self.retriever = VectorIndexRetriever(
            index=index_builder.index,
            similarity_top_k=10
        )
    
    def generate_response(self, query, metadata_filters=None):
        # Retrieve with metadata filtering
        if metadata_filters:
            all_nodes = self.retriever.retrieve(query)
            nodes = [
                node for node in all_nodes
                if all(node.metadata.get(key) == value for key, value in metadata_filters.items())
            ]
        else:
            nodes = self.retriever.retrieve(query)
        
        # Generate response with context
        context = "\n".join([node.text for node in nodes])
        response = self.model_manager.generate_text([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ])
        
        return {
            "response": response,
            "sources": [node.metadata.get('source') for node in nodes],
            "metadata": [node.metadata for node in nodes]
        }
```

## 7. Performance Considerations

### Metadata Storage
- **Size**: Rich metadata increases storage requirements
- **Efficiency**: ChromaDB handles metadata efficiently
- **Indexing**: Consider metadata field indexing for large datasets

### Retrieval Performance
- **Filtering**: Metadata filtering adds minimal overhead
- **Ranking**: Custom ranking can be computationally expensive
- **Caching**: Cache frequently used metadata filters

### Memory Usage
- **Loading**: Metadata is loaded with each chunk
- **Processing**: Consider lazy loading for large datasets
- **Optimization**: Use only necessary metadata fields

## 8. Best Practices

### Metadata Design
1. **Relevance**: Only include metadata that enhances retrieval
2. **Consistency**: Use consistent naming conventions
3. **Types**: Use appropriate data types (strings, booleans, numbers)
4. **Size**: Keep metadata fields reasonably sized

### Retrieval Strategy
1. **Start Simple**: Begin with basic vector similarity
2. **Add Filters**: Gradually add metadata filtering
3. **Test Performance**: Monitor retrieval speed and accuracy
4. **Iterate**: Refine based on user feedback

### Code Organization
1. **Modularity**: Separate metadata extraction from retrieval
2. **Reusability**: Create reusable filtering functions
3. **Testing**: Test metadata extraction and retrieval separately
4. **Documentation**: Document metadata schema and usage

## 9. Real-World Examples

### Example 1: Customer Support RAG
```python
# Find positive customer service content
positive_support = search_by_sentiment("customer service", "positive")

# Find content from specific product documentation
product_docs = search_by_document("installation guide", "product_manual.txt")

# Find content with troubleshooting information
troubleshooting = search_by_content_type("troubleshooting", "headings")
```

### Example 2: Legal Document RAG
```python
# Find recent legal updates
recent_updates = search_by_metadata("legal changes", {"created_at": "2024"})

# Find specific document types
terms_conditions = search_by_metadata("terms", {"document_type": "legal"})

# Find high-confidence legal content
high_confidence = search_by_metadata("liability", {"confidence_score": 0.9})
```

### Example 3: Technical Documentation RAG
```python
# Find API documentation
api_docs = search_by_metadata("API", {"content_type": "api_documentation"})

# Find code examples
code_examples = search_by_metadata("example", {"has_code": True})

# Find beginner-friendly content
beginner_content = search_by_metadata("tutorial", {"difficulty": "beginner"})
```

## 10. Conclusion

LlamaIndex's metadata system provides powerful capabilities for enhancing retrieval:

- **Precision**: Filter results by specific criteria
- **Context**: Understand content structure and source
- **Ranking**: Customize result ordering based on metadata
- **Analytics**: Analyze content distribution and quality
- **Flexibility**: Support complex query requirements

By combining vector similarity with rich metadata, you can build sophisticated RAG systems that provide precise, contextual, and user-friendly responses.

## Author

Emad Noorizadeh
