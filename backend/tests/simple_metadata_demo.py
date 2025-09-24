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
Simple demonstration: How LlamaIndex Uses Metadata for Retrieval
Author: Emad Noorizadeh
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
from llama_index.core.query_engine import RetrieverQueryEngine

from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config, get_data_folder


def demonstrate_metadata_retrieval():
    """Demonstrate how LlamaIndex uses metadata for retrieval"""
    print("🚀 === LLAMAINDEX METADATA RETRIEVAL DEMONSTRATION ===\n")
    
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
    
    # Build index
    print("🔧 Building vector index...")
    index = VectorStoreIndex.from_vector_store(
        vector_store=db_config.vector_store,
        storage_context=db_config.storage_context
    )
    
    # Add nodes to index
    for node in all_nodes:
        index.insert(node)
    
    # Initialize retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=10
    )
    
    print("✅ Index built successfully!")
    
    # Demonstrate retrieval mechanisms
    print("\n🔍 === RETRIEVAL MECHANISMS ===")
    
    query = "banking services"
    print(f"Query: '{query}'")
    
    # 1. Basic vector similarity retrieval
    print("\n1. BASIC VECTOR SIMILARITY RETRIEVAL:")
    nodes = retriever.retrieve(query)
    print(f"   Found {len(nodes)} results using vector similarity")
    
    for i, node in enumerate(nodes[:3]):
        print(f"   Result {i+1}:")
        print(f"     Text: {node.text[:100]}...")
        print(f"     Source: {node.metadata.get('document_id', 'unknown')}")
        print(f"     Category: {node.metadata.get('chunk_category', 'unknown')}")
        print(f"     Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
        print(f"     Score: {node.score:.3f}")
    
    # 2. Metadata filtering
    print("\n2. METADATA FILTERING:")
    
    # Filter by category
    banking_chunks = [node for node in nodes if node.metadata.get('chunk_category') == 'Banking']
    financial_chunks = [node for node in nodes if node.metadata.get('chunk_category') == 'Financial Services']
    
    print(f"   Banking category: {len(banking_chunks)} chunks")
    print(f"   Financial Services category: {len(financial_chunks)} chunks")
    
    # Filter by sentiment
    positive_chunks = [node for node in nodes if node.metadata.get('chunk_sentiment') == 'positive']
    neutral_chunks = [node for node in nodes if node.metadata.get('chunk_sentiment') == 'neutral']
    
    print(f"   Positive sentiment: {len(positive_chunks)} chunks")
    print(f"   Neutral sentiment: {len(neutral_chunks)} chunks")
    
    # Filter by content type
    with_headings = [node for node in nodes if node.metadata.get('has_headings', False)]
    with_emails = [node for node in nodes if node.metadata.get('contains_email', False)]
    
    print(f"   With headings: {len(with_headings)} chunks")
    print(f"   With emails: {len(with_emails)} chunks")
    
    # 3. Combined filtering
    print("\n3. COMBINED VECTOR SIMILARITY + METADATA FILTERING:")
    
    # Get positive banking chunks with headings
    filtered_chunks = [
        node for node in nodes
        if (node.metadata.get('chunk_category') == 'Banking' and
            node.metadata.get('chunk_sentiment') == 'positive' and
            node.metadata.get('has_headings', False))
    ]
    
    print(f"   Banking + Positive + Has Headings: {len(filtered_chunks)} chunks")
    
    for i, node in enumerate(filtered_chunks):
        print(f"   Filtered Result {i+1}:")
        print(f"     Text: {node.text[:100]}...")
        print(f"     Category: {node.metadata.get('chunk_category', 'unknown')}")
        print(f"     Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
        print(f"     Has Headings: {node.metadata.get('has_headings', False)}")
        print(f"     Score: {node.score:.3f}")
    
    # 4. Metadata-based ranking
    print("\n4. METADATA-INFLUENCED RANKING:")
    
    def custom_ranking_score(node):
        base_score = node.score
        
        # Boost for positive sentiment
        if node.metadata.get('chunk_sentiment') == 'positive':
            base_score += 0.1
        
        # Boost for banking category
        if node.metadata.get('chunk_category') == 'Banking':
            base_score += 0.05
        
        # Boost for chunks with headings
        if node.metadata.get('has_headings', False):
            base_score += 0.03
        
        return base_score
    
    # Apply custom ranking
    ranked_nodes = sorted(nodes, key=custom_ranking_score, reverse=True)
    
    print("   Custom ranked results:")
    for i, node in enumerate(ranked_nodes[:3]):
        custom_score = custom_ranking_score(node)
        print(f"   Ranked Result {i+1}:")
        print(f"     Text: {node.text[:100]}...")
        print(f"     Original Score: {node.score:.3f}")
        print(f"     Custom Score: {custom_score:.3f}")
        print(f"     Category: {node.metadata.get('chunk_category', 'unknown')}")
        print(f"     Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
    
    # 5. Metadata analytics
    print("\n5. METADATA ANALYTICS:")
    
    # Category distribution
    categories = [node.metadata.get('chunk_category', 'unknown') for node in all_nodes]
    category_counts = {}
    for cat in categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("   Category Distribution:")
    for category, count in category_counts.items():
        print(f"     {category}: {count} chunks")
    
    # Sentiment distribution
    sentiments = [node.metadata.get('chunk_sentiment', 'unknown') for node in all_nodes]
    sentiment_counts = {}
    for sent in sentiments:
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1
    
    print("   Sentiment Distribution:")
    for sentiment, count in sentiment_counts.items():
        print(f"     {sentiment}: {count} chunks")
    
    # Content type analysis
    with_headings_count = sum(1 for node in all_nodes if node.metadata.get('has_headings', False))
    with_emails_count = sum(1 for node in all_nodes if node.metadata.get('contains_email', False))
    
    print("   Content Type Analysis:")
    print(f"     Chunks with headings: {with_headings_count}")
    print(f"     Chunks with emails: {with_emails_count}")
    
    print("\n✅ Metadata retrieval demonstration completed!")


if __name__ == "__main__":
    demonstrate_metadata_retrieval()
