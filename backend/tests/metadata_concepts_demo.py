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
Demonstration: How LlamaIndex Uses Metadata for Retrieval
Author: Emad Noorizadeh

This script demonstrates the key concepts of how LlamaIndex uses metadata
for retrieval without the insertion complexity.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever

from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config, get_data_folder


def demonstrate_metadata_concepts():
    """Demonstrate how LlamaIndex uses metadata for retrieval"""
    print("🚀 === LLAMAINDEX METADATA RETRIEVAL CONCEPTS ===\n")
    
    # Initialize components
    model_manager = ModelManager()
    db_config = DatabaseConfig()
    
    # Load existing data
    data_folder = get_data_folder()
    print(f"📁 Loading data from: {data_folder}")
    
    # Load documents
    reader = SimpleDirectoryReader(input_dir=data_folder)
    documents = reader.load_data()
    
    # Add metadata to documents
    for i, doc in enumerate(documents):
        doc.metadata.update({
            "document_id": f"doc_{i+1}",
            "category": "Banking" if i == 0 else "Financial Services",
            "sentiment": "positive" if i == 0 else "neutral",
            "topics": "Rewards, Benefits" if i == 0 else "Services, Information",
            "word_count": len(doc.text.split()),
            "has_headings": "#" in doc.text,
            "contains_emails": "@" in doc.text
        })
    
    print(f"✅ Loaded {len(documents)} documents with metadata")
    
    # Parse into chunks
    node_parser = SentenceSplitter(chunk_size=500, chunk_overlap=50)
    all_nodes = []
    
    for doc in documents:
        nodes = node_parser.get_nodes_from_documents([doc])
        
        # Add chunk-specific metadata
        for j, node in enumerate(nodes):
            node.metadata.update({
                "chunk_id": f"{doc.metadata['document_id']}_chunk_{j}",
                "chunk_index": j,
                "chunk_sentiment": doc.metadata["sentiment"],
                "chunk_topics": doc.metadata["topics"],
                "chunk_category": doc.metadata["category"],
                "has_headings": "#" in node.text,
                "contains_email": "@" in node.text,
                "word_count": len(node.text.split())
            })
        
        all_nodes.extend(nodes)
    
    print(f"✅ Created {len(all_nodes)} chunks with metadata")
    
    # Show metadata structure
    print("\n📋 === METADATA STRUCTURE ===")
    print("Document-level metadata example:")
    print(f"  {documents[0].metadata}")
    
    print("\nChunk-level metadata example:")
    print(f"  {all_nodes[0].metadata}")
    
    # Demonstrate retrieval concepts
    print("\n🔍 === RETRIEVAL CONCEPTS ===")
    
    # 1. Vector Similarity + Metadata Storage
    print("\n1. VECTOR SIMILARITY + METADATA STORAGE:")
    print("   - LlamaIndex stores each chunk as a vector in the database")
    print("   - Metadata is stored alongside each vector")
    print("   - During retrieval, both vector similarity and metadata are available")
    
    # 2. Metadata Filtering
    print("\n2. METADATA FILTERING:")
    print("   - Filter results by document source")
    print("   - Filter by content category")
    print("   - Filter by sentiment")
    print("   - Filter by content type (headings, emails, etc.)")
    
    # 3. Combined Retrieval Strategies
    print("\n3. COMBINED RETRIEVAL STRATEGIES:")
    print("   - Vector similarity for semantic relevance")
    print("   - Metadata filtering for precision")
    print("   - Custom ranking based on metadata")
    
    # 4. Metadata Analytics
    print("\n4. METADATA ANALYTICS:")
    print("   - Content distribution analysis")
    print("   - Sentiment analysis across documents")
    print("   - Content type analysis")
    
    # Show practical examples
    print("\n💡 === PRACTICAL EXAMPLES ===")
    
    # Example 1: Basic retrieval
    print("\nExample 1: Basic Vector Retrieval")
    print("   Query: 'banking services'")
    print("   Process:")
    print("   1. Convert query to vector")
    print("   2. Find similar vectors in database")
    print("   3. Return chunks with similarity scores")
    print("   4. Metadata available for each result")
    
    # Example 2: Metadata filtering
    print("\nExample 2: Metadata Filtering")
    print("   Query: 'banking services'")
    print("   Filter: category = 'Banking' AND sentiment = 'positive'")
    print("   Process:")
    print("   1. Get vector similarity results")
    print("   2. Filter by metadata criteria")
    print("   3. Return filtered results")
    
    # Example 3: Custom ranking
    print("\nExample 3: Custom Ranking")
    print("   Query: 'banking services'")
    print("   Ranking factors:")
    print("   - Base vector similarity score")
    print("   - +0.1 for positive sentiment")
    print("   - +0.05 for banking category")
    print("   - +0.03 for chunks with headings")
    
    # Show metadata distribution
    print("\n📊 === METADATA DISTRIBUTION ===")
    
    # Category distribution
    categories = [node.metadata.get('chunk_category', 'unknown') for node in all_nodes]
    category_counts = {}
    for cat in categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("Category Distribution:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} chunks")
    
    # Sentiment distribution
    sentiments = [node.metadata.get('chunk_sentiment', 'unknown') for node in all_nodes]
    sentiment_counts = {}
    for sent in sentiments:
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1
    
    print("\nSentiment Distribution:")
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment}: {count} chunks")
    
    # Content type analysis
    with_headings_count = sum(1 for node in all_nodes if node.metadata.get('has_headings', False))
    with_emails_count = sum(1 for node in all_nodes if node.metadata.get('contains_email', False))
    
    print("\nContent Type Analysis:")
    print(f"  Chunks with headings: {with_headings_count}")
    print(f"  Chunks with emails: {with_emails_count}")
    
    # Show how metadata enhances retrieval
    print("\n🎯 === HOW METADATA ENHANCES RETRIEVAL ===")
    
    print("\n1. PRECISION IMPROVEMENT:")
    print("   - Filter out irrelevant content by source")
    print("   - Focus on specific content types")
    print("   - Use confidence scores for quality control")
    
    print("\n2. CONTEXT UNDERSTANDING:")
    print("   - Know which document chunks come from")
    print("   - Understand content structure and type")
    print("   - Leverage sentiment and topic information")
    
    print("\n3. USER EXPERIENCE:")
    print("   - Provide source attribution")
    print("   - Enable targeted searches")
    print("   - Support complex query requirements")
    
    print("\n4. ANALYTICS CAPABILITIES:")
    print("   - Analyze content distribution")
    print("   - Track sentiment across documents")
    print("   - Monitor confidence scores")
    
    # Show code examples
    print("\n💻 === CODE EXAMPLES ===")
    
    print("\nBasic Retrieval with Metadata:")
    print("""
    # Get vector similarity results
    nodes = retriever.retrieve(query)
    
    # Access metadata for each result
    for node in nodes:
        print(f"Text: {node.text}")
        print(f"Source: {node.metadata.get('source')}")
        print(f"Category: {node.metadata.get('category')}")
        print(f"Sentiment: {node.metadata.get('sentiment')}")
        print(f"Score: {node.score}")
    """)
    
    print("\nMetadata Filtering:")
    print("""
    # Filter by category
    banking_chunks = [
        node for node in nodes 
        if node.metadata.get('category') == 'Banking'
    ]
    
    # Filter by sentiment
    positive_chunks = [
        node for node in nodes 
        if node.metadata.get('sentiment') == 'positive'
    ]
    
    # Combined filtering
    filtered_chunks = [
        node for node in nodes
        if (node.metadata.get('category') == 'Banking' and
            node.metadata.get('sentiment') == 'positive')
    ]
    """)
    
    print("\nCustom Ranking:")
    print("""
    def custom_ranking_score(node):
        base_score = node.score
        
        # Boost for positive sentiment
        if node.metadata.get('sentiment') == 'positive':
            base_score += 0.1
        
        # Boost for banking category
        if node.metadata.get('category') == 'Banking':
            base_score += 0.05
        
        return base_score
    
    # Apply custom ranking
    ranked_nodes = sorted(nodes, key=custom_ranking_score, reverse=True)
    """)
    
    print("\n✅ Metadata concepts demonstration completed!")


if __name__ == "__main__":
    demonstrate_metadata_concepts()
