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
Test script for LLM metadata extractor
Author: Emad Noorizadeh
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.llm_metadata_extractor import LLMMetadataExtractor, HybridMetadataExtractor, ExtractionConfig, ExtractionMethod
from model_manager import ModelManager
from config import get_config

def test_llm_metadata_extractor():
    """Test the LLM metadata extractor"""
    print("=== Testing LLM Metadata Extractor ===\n")
    
    # Test 1: Initialize extractor
    print("🔧 Test 1: Initialize LLM Metadata Extractor...")
    model_manager = ModelManager()
    
    if not model_manager.list_models()['openai']:
        print("❌ OpenAI client not available. Please set OPENAI_API_KEY environment variable.")
        return False
    
    config = ExtractionConfig(
        method=ExtractionMethod.HYBRID,
        model="gpt-3.5-turbo",
        temperature=0.1,
        enable_structured_output=True,
        fallback_to_regex=True
    )
    
    extractor = LLMMetadataExtractor(get_config, model_manager, config)
    print("✓ LLM Metadata Extractor initialized")
    
    # Test 2: Extract metadata from sample text
    print("\n🔧 Test 2: Extract metadata from sample text...")
    sample_text = """
    [Skip to content](https://example.com/skip)
    
    # Bank of America Preferred Rewards Program
    
    ## Overview
    The Bank of America Preferred Rewards program offers exclusive benefits to customers who maintain higher balances across their Bank of America accounts. This program provides enhanced rewards, reduced fees, and priority customer service.
    
    ### Program Tiers
    - **Gold**: $20,000 - $49,999 in combined balances
    - **Platinum**: $50,000 - $99,999 in combined balances  
    - **Platinum Honors**: $100,000+ in combined balances
    
    ### Benefits
    - Increased credit card rewards
    - Reduced or waived fees
    - Priority customer service
    - Special mortgage rates
    - Investment account benefits
    
    For more information, contact us at support@bankofamerica.com or visit https://www.bankofamerica.com/preferredrewards
    """
    
    try:
        result = extractor.extract_metadata(sample_text)
        print(f"✓ Metadata extracted using {result.extraction_method}")
        print(f"Title: {result.title}")
        print(f"Summary: {result.summary}")
        print(f"Categories: {result.categories}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Document Type: {result.document_type}")
        print(f"Confidence: {result.confidence_scores}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        
        if result.entities:
            print(f"Entities: {result.entities}")
        if result.topics:
            print(f"Topics: {result.topics}")
        if result.key_phrases:
            print(f"Key Phrases: {result.key_phrases}")
            
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        return False
    
    # Test 3: Test different extraction methods
    print("\n🔧 Test 3: Test different extraction methods...")
    
    # Test regex fallback
    try:
        regex_result = extractor.extract_metadata(sample_text, use_llm=False)
        print(f"✓ Regex extraction: {regex_result.extraction_method}")
        print(f"Regex title: {regex_result.title}")
    except Exception as e:
        print(f"❌ Regex extraction failed: {e}")
    
    # Test 4: Test batch extraction
    print("\n🔧 Test 4: Test batch extraction...")
    texts = [
        "This is a simple document about banking services.",
        sample_text,
        "A technical manual for software installation and configuration."
    ]
    
    try:
        batch_results = extractor.batch_extract(texts)
        print(f"✓ Batch processed {len(batch_results)} documents")
        
        # Get statistics
        stats = extractor.get_extraction_stats(batch_results)
        print(f"Success rate: {stats['success_rate']:.2%}")
        print(f"Average confidence: {stats['average_confidence']:.2f}")
        print(f"Average processing time: {stats['average_processing_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Batch extraction failed: {e}")
    
    print(f"\n✅ LLM Metadata Extractor test completed!")
    return True

def test_hybrid_extractor():
    """Test the hybrid metadata extractor"""
    print("\n=== Testing Hybrid Metadata Extractor ===\n")
    
    # Test 1: Initialize hybrid extractor
    print("🔧 Test 1: Initialize Hybrid Extractor...")
    model_manager = ModelManager()
    
    if not model_manager.list_models()['openai']:
        print("❌ OpenAI client not available. Skipping hybrid test.")
        return False
    
    hybrid_extractor = HybridMetadataExtractor(get_config, model_manager)
    print("✓ Hybrid Metadata Extractor initialized")
    
    # Test 2: Test different strategies
    print("\n🔧 Test 2: Test different extraction strategies...")
    
    sample_text = """
    # Financial Services Report
    
    This quarterly report covers our banking operations, including loan performance, 
    customer satisfaction metrics, and regulatory compliance updates.
    
    Key findings:
    - Loan default rates decreased by 15%
    - Customer satisfaction improved to 4.2/5
    - All regulatory requirements met
    
    Contact: john.doe@bank.com
    """
    
    strategies = ["smart", "llm_first", "regex_first", "both"]
    
    for strategy in strategies:
        try:
            print(f"\nTesting {strategy} strategy...")
            result = hybrid_extractor.extract_metadata(sample_text, strategy=strategy)
            print(f"✓ {strategy}: {result.get('extraction_method', 'unknown')}")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Categories: {result.get('categories', 'N/A')}")
            if 'confidence' in result:
                print(f"  Confidence: {result['confidence']:.2f}")
        except Exception as e:
            print(f"❌ {strategy} strategy failed: {e}")
    
    print(f"\n✅ Hybrid Metadata Extractor test completed!")
    return True

def test_extraction_reliability():
    """Test the reliability of different extraction methods"""
    print("\n=== Testing Extraction Reliability ===\n")
    
    # Test documents with different complexity levels
    test_documents = [
        {
            "name": "Simple Document",
            "text": "Bank of America offers checking accounts with no monthly fees.",
            "expected_complexity": "low"
        },
        {
            "name": "Medium Document", 
            "text": """
            # Bank of America Preferred Rewards
            
            The Preferred Rewards program provides enhanced benefits to customers 
            based on their combined account balances. Benefits include increased 
            credit card rewards, reduced fees, and priority customer service.
            
            Program tiers range from Gold ($20K) to Platinum Honors ($100K+).
            """,
            "expected_complexity": "medium"
        },
        {
            "name": "Complex Document",
            "text": """
            # Comprehensive Financial Services Analysis
            
            This detailed report examines the performance of our retail banking 
            division, including quantitative analysis of loan portfolios, 
            customer acquisition metrics, and competitive positioning in the 
            financial services market.
            
            Executive Summary:
            Our Q3 performance demonstrates strong growth across all key metrics, 
            with particular strength in digital banking adoption and customer 
            retention rates. The implementation of our new AI-powered fraud 
            detection system has resulted in a 30% reduction in fraudulent 
            transactions while maintaining customer satisfaction scores above 4.0.
            
            Key Performance Indicators:
            - Digital banking adoption: 78% (+12% YoY)
            - Customer retention rate: 94% (+3% YoY)  
            - Fraud detection accuracy: 99.2% (+5% YoY)
            - Customer satisfaction: 4.3/5 (+0.2 YoY)
            
            Strategic Recommendations:
            1. Expand AI capabilities to loan underwriting
            2. Enhance mobile banking features
            3. Develop new financial wellness tools
            4. Strengthen cybersecurity measures
            
            Contact: research@bankofamerica.com
            """,
            "expected_complexity": "high"
        }
    ]
    
    model_manager = ModelManager()
    if not model_manager.list_models()['openai']:
        print("❌ OpenAI client not available. Skipping reliability test.")
        return False
    
    # Test with different extraction methods
    configs = [
        ("Regex Only", ExtractionConfig(method=ExtractionMethod.REGEX_ONLY)),
        ("LLM Only", ExtractionConfig(method=ExtractionMethod.LLM_ONLY)),
        ("Hybrid", ExtractionConfig(method=ExtractionMethod.HYBRID)),
        ("Adaptive", ExtractionConfig(method=ExtractionMethod.ADAPTIVE))
    ]
    
    for config_name, config in configs:
        print(f"\n🔧 Testing {config_name} method...")
        extractor = LLMMetadataExtractor(get_config, model_manager, config)
        
        for doc in test_documents:
            try:
                result = extractor.extract_metadata(doc['text'])
                print(f"  {doc['name']}: {result.extraction_method} "
                      f"(confidence: {result.confidence_scores.get('overall', 0):.2f}, "
                      f"time: {result.processing_time:.2f}s)")
            except Exception as e:
                print(f"  {doc['name']}: Failed - {e}")
    
    print(f"\n✅ Extraction reliability test completed!")
    return True

def run_llm_metadata_tests():
    """Run all LLM metadata extractor tests"""
    print("=== Testing LLM Metadata Extraction System ===\n")
    
    try:
        success = True
        
        # Test basic LLM extractor
        if not test_llm_metadata_extractor():
            success = False
        
        # Test hybrid extractor
        if not test_hybrid_extractor():
            success = False
        
        # Test reliability
        if not test_extraction_reliability():
            success = False
        
        if success:
            print("\n🎉 All LLM metadata extraction tests passed!")
        else:
            print("\n💥 Some LLM metadata extraction tests failed!")
        
        return success
        
    except Exception as e:
        print(f"\n❌ LLM metadata extraction test suite failed: {e}")
        return False

if __name__ == "__main__":
    run_llm_metadata_tests()
