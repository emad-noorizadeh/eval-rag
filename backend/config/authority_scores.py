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
Authority Score Configuration
Author: Emad Noorizadeh

This module contains configurable authority scores for domain trustworthiness
and document type reliability. These scores are used to calculate the overall
authority score for documents in the RAG system.

Scores range from 0.0 to 1.0 (0% to 100%):
- 1.0 = Highest trust/authority
- 0.5 = Default/unknown
- 0.0 = Lowest trust/authority
"""

from typing import Dict
import json
import os

# Configuration file path
CONFIG_FILE = "authority_scores_config.json"

# Domain Trustworthiness Scores
# Based on official domains, subdomains, and partner sites
DOMAIN_AUTHORITY_SCORES: Dict[str, float] = {
    # Bank of America Official Domains
    'www.bankofamerica.com': 0.95,        # Main website (highest)
    'bankofamerica.com': 0.9,             # Official domain
    'promotions.bankofamerica.com': 0.9,  # Official promotions
    'online.bankofamerica.com': 0.9,      # Online banking
    'secure.bankofamerica.com': 0.95,     # Secure portal
    
    # Merrill Lynch (Bank of America subsidiary)
    'www.merrill.com': 0.85,              # Merrill main site
    'merrill.com': 0.85,                  # Merrill domain
    'ml.com': 0.85,                       # Merrill short domain
    
    # Other Bank of America Properties
    'bofa.com': 0.8,                      # Bank of America short domain
    'bankofamerica.com.au': 0.8,          # International
    'bankofamerica.com.mx': 0.8,          # International
    
    # Partner/Third-party Sites
    'partner.bankofamerica.com': 0.7,     # Partner subdomain
    'api.bankofamerica.com': 0.8,         # API subdomain
    
    # Government/Regulatory (if applicable)
    'sec.gov': 0.9,                       # SEC filings
    'fdic.gov': 0.9,                      # FDIC information
    'federalreserve.gov': 0.9,            # Federal Reserve
    
    # Local/Development
    'local': 0.5,                         # Local files (default)
    'localhost': 0.5,                     # Local development
    '127.0.0.1': 0.5,                     # Local development
}

# Document Type Reliability Scores
# Based on document type and content trustworthiness
DOCUMENT_TYPE_AUTHORITY_SCORES: Dict[str, float] = {
    # Legal/Regulatory Documents (Highest Trust)
    'disclosure': 1.0,                    # Legal disclosures
    'terms': 0.95,                        # Terms and conditions
    'privacy': 0.95,                      # Privacy policy
    'regulatory': 0.95,                   # Regulatory documents
    'compliance': 0.95,                   # Compliance documents
    
    # Official Information (High Trust)
    'faq': 0.8,                           # Frequently asked questions
    'help': 0.8,                          # Help documentation
    'guide': 0.8,                         # User guides
    'manual': 0.8,                        # User manuals
    'policy': 0.85,                       # Official policies
    
    # Marketing/Informational (Medium Trust)
    'landing': 0.7,                       # Landing pages
    'product': 0.7,                       # Product information
    'service': 0.7,                       # Service information
    'feature': 0.7,                       # Feature descriptions
    'benefit': 0.7,                       # Benefit descriptions
    
    # Interactive/Transactional (Medium-Low Trust)
    'form': 0.6,                          # Forms and applications
    'application': 0.6,                   # Application forms
    'registration': 0.6,                  # Registration forms
    'survey': 0.6,                        # Surveys and feedback
    
    # Promotional/Marketing (Lowest Trust)
    'promo': 0.5,                         # Promotional content
    'advertisement': 0.4,                 # Advertisements
    'marketing': 0.5,                     # Marketing materials
    'campaign': 0.5,                      # Marketing campaigns
    'offer': 0.5,                         # Special offers
    
    # News/Media (Variable Trust)
    'news': 0.6,                          # News articles
    'press': 0.7,                         # Press releases
    'blog': 0.4,                          # Blog posts
    'article': 0.6,                       # General articles
    
    # Technical (Medium Trust)
    'api': 0.8,                           # API documentation
    'technical': 0.8,                     # Technical documentation
    'integration': 0.8,                   # Integration guides
    'developer': 0.8,                     # Developer resources
}

# Default scores for unknown domains/types
DEFAULT_DOMAIN_SCORE: float = 0.5
DEFAULT_DOCUMENT_TYPE_SCORE: float = 0.5

def get_domain_authority_score(domain: str) -> float:
    """
    Get authority score for a domain.
    
    Args:
        domain: Domain name to look up
        
    Returns:
        Authority score (0.0 to 1.0)
    """
    return DOMAIN_AUTHORITY_SCORES.get(domain.lower(), DEFAULT_DOMAIN_SCORE)

def get_document_type_authority_score(doc_type: str) -> float:
    """
    Get authority score for a document type.
    
    Args:
        doc_type: Document type to look up
        
    Returns:
        Authority score (0.0 to 1.0)
    """
    return DOCUMENT_TYPE_AUTHORITY_SCORES.get(doc_type.lower(), DEFAULT_DOCUMENT_TYPE_SCORE)

def calculate_authority_score(domain: str, doc_type: str) -> float:
    """
    Calculate overall authority score based on domain and document type.
    
    Args:
        domain: Domain name
        doc_type: Document type
        
    Returns:
        Combined authority score (0.0 to 1.0)
    """
    domain_score = get_domain_authority_score(domain)
    type_score = get_document_type_authority_score(doc_type)
    
    # Simple average - could be weighted differently
    return (domain_score + type_score) / 2

def add_domain_score(domain: str, score: float) -> None:
    """
    Add or update a domain authority score.
    
    Args:
        domain: Domain name
        score: Authority score (0.0 to 1.0)
    """
    DOMAIN_AUTHORITY_SCORES[domain.lower()] = max(0.0, min(1.0, score))

def add_document_type_score(doc_type: str, score: float) -> None:
    """
    Add or update a document type authority score.
    
    Args:
        doc_type: Document type
        score: Authority score (0.0 to 1.0)
    """
    DOCUMENT_TYPE_AUTHORITY_SCORES[doc_type.lower()] = max(0.0, min(1.0, score))

def get_all_domain_scores() -> Dict[str, float]:
    """Get all domain authority scores."""
    return DOMAIN_AUTHORITY_SCORES.copy()

def get_all_document_type_scores() -> Dict[str, float]:
    """Get all document type authority scores."""
    return DOCUMENT_TYPE_AUTHORITY_SCORES.copy()

def load_config_from_file() -> None:
    """Load authority scores from JSON configuration file."""
    global DOMAIN_AUTHORITY_SCORES, DOCUMENT_TYPE_AUTHORITY_SCORES, DEFAULT_DOMAIN_SCORE, DEFAULT_DOCUMENT_TYPE_SCORE
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load domain scores
            if 'domain_authority_scores' in config:
                DOMAIN_AUTHORITY_SCORES.update(config['domain_authority_scores'])
            
            # Load document type scores
            if 'document_type_authority_scores' in config:
                DOCUMENT_TYPE_AUTHORITY_SCORES.update(config['document_type_authority_scores'])
            
            # Load default scores
            if 'default_scores' in config:
                DEFAULT_DOMAIN_SCORE = config['default_scores'].get('domain', DEFAULT_DOMAIN_SCORE)
                DEFAULT_DOCUMENT_TYPE_SCORE = config['default_scores'].get('document_type', DEFAULT_DOCUMENT_TYPE_SCORE)
            
            print(f"✓ Loaded authority scores from {CONFIG_FILE}")
        except Exception as e:
            print(f"⚠ Error loading config from {CONFIG_FILE}: {e}")
            print("Using default scores...")
    else:
        print(f"⚠ Config file {CONFIG_FILE} not found, using default scores...")

def save_config_to_file() -> None:
    """Save current authority scores to JSON configuration file."""
    config = {
        "domain_authority_scores": DOMAIN_AUTHORITY_SCORES,
        "document_type_authority_scores": DOCUMENT_TYPE_AUTHORITY_SCORES,
        "default_scores": {
            "domain": DEFAULT_DOMAIN_SCORE,
            "document_type": DEFAULT_DOCUMENT_TYPE_SCORE
        },
        "description": {
            "domain_authority_scores": "Trustworthiness scores for different domains (0.0 to 1.0)",
            "document_type_authority_scores": "Reliability scores for different document types (0.0 to 1.0)",
            "default_scores": "Default scores for unknown domains and document types",
            "note": "Scores are combined using simple average: (domain_score + type_score) / 2"
        }
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved authority scores to {CONFIG_FILE}")
    except Exception as e:
        print(f"⚠ Error saving config to {CONFIG_FILE}: {e}")

def print_authority_scores() -> None:
    """Print all authority scores for debugging."""
    print("=== Domain Authority Scores ===")
    for domain, score in sorted(DOMAIN_AUTHORITY_SCORES.items()):
        print(f"{domain}: {score:.2f} ({score*100:.0f}%)")
    
    print("\n=== Document Type Authority Scores ===")
    for doc_type, score in sorted(DOCUMENT_TYPE_AUTHORITY_SCORES.items()):
        print(f"{doc_type}: {score:.2f} ({score*100:.0f}%)")

if __name__ == "__main__":
    # Load configuration from file
    load_config_from_file()
    
    # Example usage and testing
    print_authority_scores()
    
    # Test some examples
    print(f"\n=== Test Examples ===")
    print(f"bankofamerica.com + terms: {calculate_authority_score('bankofamerica.com', 'terms'):.2f}")
    print(f"local + landing: {calculate_authority_score('local', 'landing'):.2f}")
    print(f"unknown.com + promo: {calculate_authority_score('unknown.com', 'promo'):.2f}")
