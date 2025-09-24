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

This script demonstrates the specific mechanisms LlamaIndex uses
to leverage metadata during retrieval operations.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.core.vector_stores.types import VectorStoreQueryResult

from model_manager import ModelManager
from config.database_config import DatabaseConfig
from config import get_config, get_data_folder, get_database_path, get_collection_name
from processors.hybrid_metadata_extractor import HybridMetadataExtractor


class MetadataRetrievalDemo:
    """
    Demonstrates how LlamaIndex uses metadata for retrieval
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.db_config = DatabaseConfig()
        self.index = None
        self.retriever = None
        self.query_engine = None
    
    def build_demo_index(self):
        """Build a demo index with rich metadata"""
        print("🔧 Building demo index with metadata...")
        
        # Create sample documents with metadata
        documents = [
            Document(
                text="""
                # Bank of America Preferred Rewards Program
                
                The Preferred Rewards program offers exclusive benefits to customers who maintain 
                higher balances across their Bank of America accounts. This program provides 
                enhanced rewards, reduced fees, and priority customer service.
                
                Benefits include:
                - Higher interest rates on savings accounts
                - Reduced fees on checking accounts
                - Priority customer service
                - Exclusive credit card offers
                
                Contact: support@bankofamerica.com
                """,
                metadata={
                    "source": "banking_services.txt",
                    "title": "Bank of America Preferred Rewards",
                    "category": "Banking",
                    "sentiment": "positive",
                    "topics": "Rewards, Benefits, Customer Service",
                    "document_type": "Service Information",
                    "word_count": 89,
                    "created_at": "2024-01-15"
                }
            ),
            Document(
                text="""
                # Investment Advisory Services
                
                Our investment advisory services help clients build and manage their portfolios
                through professional guidance and personalized strategies. We offer comprehensive
                financial planning and investment management solutions.
                
                Services include:
                - Portfolio management
                - Financial planning
                - Risk assessment
                - Retirement planning
                
                For more information, visit our website or call 1-800-BANK-USA.
                """,
                metadata={
                    "source": "investment_services.txt",
                    "title": "Investment Advisory Services",
                    "category": "Investment",
                    "sentiment": "neutral",
                    "topics": "Investment, Portfolio, Financial Planning",
                    "document_type": "Service Information",
                    "word_count": 76,
                    "created_at": "2024-01-20"
                }
            ),
            Document(
                text="""
                # Credit Card Terms and Conditions
                
                Please review these terms carefully. By using your Bank of America credit card,
                you agree to be bound by these terms and conditions. Interest rates, fees, and
                other charges may apply.
                
                Important terms:
                - Annual Percentage Rate (APR) varies by creditworthiness
                - Late payment fees may apply
                - Foreign transaction fees: 3% of transaction amount
                - Cash advance fees: 3% or $10, whichever is greater
                
                Contact: cards@bankofamerica.com
                """,
                metadata={
                    "source": "credit_card_terms.txt",
                    "title": "Credit Card Terms and Conditions",
                    "category": "Credit",
                    "sentiment": "neutral",
                    "topics": "Terms, Conditions, Fees, Rates",
                    "document_type": "Legal Document",
                    "word_count": 95,
                    "created_at": "2024-01-25"
                }
            )
        ]
        
        # Parse documents into chunks
        node_parser = SentenceSplitter(chunk_size=200, chunk_overlap=20)
        all_nodes = []
        
        for doc in documents:
            nodes = node_parser.get_nodes_from_documents([doc])
            
            # Add chunk-specific metadata
            for i, node in enumerate(nodes):
                node.metadata.update({
                    "chunk_id": f"{doc.metadata['source']}_chunk_{i}",
                    "chunk_index": i,
                    "chunk_sentiment": doc.metadata["sentiment"],
                    "chunk_topics": doc.metadata["topics"],
                    "chunk_category": doc.metadata["category"],
                    "has_headings": "#" in node.text,
                    "contains_email": "@" in node.text,
                    "contains_phone": "1-800" in node.text,
                    "word_count": len(node.text.split()),
                    "created_at": doc.metadata["created_at"]
                })
            
            all_nodes.extend(nodes)
        
        print(f"✅ Created {len(all_nodes)} chunks with metadata")
        
        # Build vector index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.db_config.vector_store,
            storage_context=self.db_config.storage_context
        )
        
        # Add nodes to index
        for node in all_nodes:
            self.index.insert(node)
        
        # Initialize retriever and query engine
        self.retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=10
        )
        self.query_engine = RetrieverQueryEngine.from_args(
            retriever=self.retriever
        )
        
        print("✅ Demo index built successfully!")
        return all_nodes
    
    def demonstrate_basic_retrieval(self):
        """Demonstrate basic vector similarity retrieval"""
        print("\n🔍 === BASIC VECTOR SIMILARITY RETRIEVAL ===")
        
        query = "banking services and rewards"
        print(f"Query: '{query}'")
        
        # Basic retrieval using vector similarity
        nodes = self.retriever.retrieve(query)
        
        print(f"\nFound {len(nodes)} results:")
        for i, node in enumerate(nodes[:3]):
            print(f"\nResult {i+1}:")
            print(f"  Text: {node.text[:100]}...")
            print(f"  Source: {node.metadata.get('source', 'unknown')}")
            print(f"  Category: {node.metadata.get('category', 'unknown')}")
            print(f"  Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
            print(f"  Score: {node.score:.3f}")
    
    def demonstrate_metadata_filtering(self):
        """Demonstrate metadata-based filtering"""
        print("\n🔍 === METADATA-BASED FILTERING ===")
        
        query = "banking services"
        print(f"Query: '{query}'")
        
        # Get all results first
        all_nodes = self.retriever.retrieve(query)
        print(f"\nTotal results: {len(all_nodes)}")
        
        # Filter by category
        banking_nodes = [node for node in all_nodes if node.metadata.get('category') == 'Banking']
        investment_nodes = [node for node in all_nodes if node.metadata.get('category') == 'Investment']
        credit_nodes = [node for node in all_nodes if node.metadata.get('category') == 'Credit']
        
        print(f"\nBy Category:")
        print(f"  Banking: {len(banking_nodes)} chunks")
        print(f"  Investment: {len(investment_nodes)} chunks")
        print(f"  Credit: {len(credit_nodes)} chunks")
        
        # Filter by sentiment
        positive_nodes = [node for node in all_nodes if node.metadata.get('chunk_sentiment') == 'positive']
        neutral_nodes = [node for node in all_nodes if node.metadata.get('chunk_sentiment') == 'neutral']
        
        print(f"\nBy Sentiment:")
        print(f"  Positive: {len(positive_nodes)} chunks")
        print(f"  Neutral: {len(neutral_nodes)} chunks")
        
        # Filter by content type
        with_headings = [node for node in all_nodes if node.metadata.get('has_headings', False)]
        with_emails = [node for node in all_nodes if node.metadata.get('contains_email', False)]
        with_phones = [node for node in all_nodes if node.metadata.get('contains_phone', False)]
        
        print(f"\nBy Content Type:")
        print(f"  With headings: {len(with_headings)} chunks")
        print(f"  With emails: {len(with_emails)} chunks")
        print(f"  With phone numbers: {len(with_phones)} chunks")
    
    def demonstrate_combined_filtering(self):
        """Demonstrate combined vector similarity + metadata filtering"""
        print("\n🔍 === COMBINED VECTOR SIMILARITY + METADATA FILTERING ===")
        
        query = "rewards and benefits"
        print(f"Query: '{query}'")
        
        # Get vector similarity results
        all_nodes = self.retriever.retrieve(query)
        print(f"\nVector similarity results: {len(all_nodes)}")
        
        # Apply multiple metadata filters
        filtered_nodes = [
            node for node in all_nodes
            if (node.metadata.get('category') == 'Banking' and
                node.metadata.get('chunk_sentiment') == 'positive' and
                node.metadata.get('has_headings', False))
        ]
        
        print(f"After filtering (Banking + Positive + Has Headings): {len(filtered_nodes)}")
        
        for i, node in enumerate(filtered_nodes):
            print(f"\nFiltered Result {i+1}:")
            print(f"  Text: {node.text[:100]}...")
            print(f"  Source: {node.metadata.get('source', 'unknown')}")
            print(f"  Category: {node.metadata.get('category', 'unknown')}")
            print(f"  Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
            print(f"  Has Headings: {node.metadata.get('has_headings', False)}")
            print(f"  Score: {node.score:.3f}")
    
    def demonstrate_metadata_ranking(self):
        """Demonstrate how metadata can influence ranking"""
        print("\n🔍 === METADATA-INFLUENCED RANKING ===")
        
        query = "banking services"
        print(f"Query: '{query}'")
        
        # Get vector similarity results
        nodes = self.retriever.retrieve(query)
        
        # Create custom ranking based on metadata
        def custom_ranking_score(node, query):
            base_score = node.score
            
            # Boost score for positive sentiment
            if node.metadata.get('chunk_sentiment') == 'positive':
                base_score += 0.1
            
            # Boost score for banking category
            if node.metadata.get('category') == 'Banking':
                base_score += 0.05
            
            # Boost score for chunks with headings
            if node.metadata.get('has_headings', False):
                base_score += 0.03
            
            # Boost score for recent content
            if node.metadata.get('created_at') == '2024-01-15':
                base_score += 0.02
            
            return base_score
        
        # Apply custom ranking
        ranked_nodes = sorted(nodes, key=lambda node: custom_ranking_score(node, query), reverse=True)
        
        print(f"\nCustom ranked results:")
        for i, node in enumerate(ranked_nodes[:3]):
            custom_score = custom_ranking_score(node, query)
            print(f"\nRanked Result {i+1}:")
            print(f"  Text: {node.text[:100]}...")
            print(f"  Original Score: {node.score:.3f}")
            print(f"  Custom Score: {custom_score:.3f}")
            print(f"  Category: {node.metadata.get('category', 'unknown')}")
            print(f"  Sentiment: {node.metadata.get('chunk_sentiment', 'unknown')}")
            print(f"  Has Headings: {node.metadata.get('has_headings', False)}")
    
    def demonstrate_metadata_queries(self):
        """Demonstrate different types of metadata-based queries"""
        print("\n🔍 === METADATA-BASED QUERIES ===")
        
        # Query 1: Find all chunks from a specific document
        print("\n1. Find all chunks from 'banking_services.txt':")
        all_nodes = self.retriever.retrieve("")  # Empty query to get all
        banking_chunks = [node for node in all_nodes if node.metadata.get('source') == 'banking_services.txt']
        print(f"   Found {len(banking_chunks)} chunks")
        
        # Query 2: Find chunks with specific sentiment
        print("\n2. Find positive sentiment chunks:")
        positive_chunks = [node for node in all_nodes if node.metadata.get('chunk_sentiment') == 'positive']
        print(f"   Found {len(positive_chunks)} positive chunks")
        
        # Query 3: Find chunks with headings
        print("\n3. Find chunks with headings:")
        heading_chunks = [node for node in all_nodes if node.metadata.get('has_headings', False)]
        print(f"   Found {len(heading_chunks)} chunks with headings")
        
        # Query 4: Find chunks containing contact information
        print("\n4. Find chunks with contact information:")
        contact_chunks = [node for node in all_nodes if 
                         node.metadata.get('contains_email', False) or 
                         node.metadata.get('contains_phone', False)]
        print(f"   Found {len(contact_chunks)} chunks with contact info")
        
        # Query 5: Find recent content
        print("\n5. Find recent content (2024-01-15):")
        recent_chunks = [node for node in all_nodes if node.metadata.get('created_at') == '2024-01-15']
        print(f"   Found {len(recent_chunks)} recent chunks")
    
    def demonstrate_metadata_analytics(self):
        """Demonstrate metadata analytics capabilities"""
        print("\n📊 === METADATA ANALYTICS ===")
        
        # Get all nodes for analysis
        all_nodes = self.retriever.retrieve("")
        
        # Category distribution
        categories = [node.metadata.get('category', 'unknown') for node in all_nodes]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print("\nCategory Distribution:")
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
        with_headings = sum(1 for node in all_nodes if node.metadata.get('has_headings', False))
        with_emails = sum(1 for node in all_nodes if node.metadata.get('contains_email', False))
        with_phones = sum(1 for node in all_nodes if node.metadata.get('contains_phone', False))
        
        print(f"\nContent Type Analysis:")
        print(f"  Chunks with headings: {with_headings}")
        print(f"  Chunks with emails: {with_emails}")
        print(f"  Chunks with phone numbers: {with_phones}")
        
        # Word count analysis
        word_counts = [node.metadata.get('word_count', 0) for node in all_nodes]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        
        print(f"\nWord Count Analysis:")
        print(f"  Average words per chunk: {avg_word_count:.1f}")
        print(f"  Min words: {min(word_counts) if word_counts else 0}")
        print(f"  Max words: {max(word_counts) if word_counts else 0}")
    
    def run_demonstration(self):
        """Run the complete metadata retrieval demonstration"""
        print("🚀 === LLAMAINDEX METADATA RETRIEVAL DEMONSTRATION ===\n")
        
        try:
            # Build demo index
            self.build_demo_index()
            
            # Run demonstrations
            self.demonstrate_basic_retrieval()
            self.demonstrate_metadata_filtering()
            self.demonstrate_combined_filtering()
            self.demonstrate_metadata_ranking()
            self.demonstrate_metadata_queries()
            self.demonstrate_metadata_analytics()
            
            print("\n✅ Metadata retrieval demonstration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    demo = MetadataRetrievalDemo()
    demo.run_demonstration()
