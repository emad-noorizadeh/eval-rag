# Authority Scores Configuration

## Overview

The Authority Scores system provides configurable trustworthiness and reliability metrics for documents in the RAG system. These scores help prioritize sources and provide confidence indicators to users.

## Files

- `authority_scores.py` - Main Python module with authority score logic
- `authority_scores_config.json` - JSON configuration file for easy modification
- `AUTHORITY_SCORES_README.md` - This documentation file

## Configuration

### Domain Authority Scores

Domain scores represent the trustworthiness of different websites and domains:

```json
{
  "domain_authority_scores": {
    "www.bankofamerica.com": 0.95,        // Main website (highest)
    "bankofamerica.com": 0.9,             // Official domain
    "promotions.bankofamerica.com": 0.9,  // Official promotions
    "merrill.com": 0.85,                  // Merrill Lynch
    "sec.gov": 0.9,                       // Government regulatory
    "local": 0.5,                         // Local files (default)
    "unknown.com": 0.5                    // Unknown domains (default)
  }
}
```

### Document Type Authority Scores

Document type scores represent the reliability of different content types:

```json
{
  "document_type_authority_scores": {
    "disclosure": 1.0,      // Legal disclosures (highest trust)
    "terms": 0.95,          // Terms and conditions
    "privacy": 0.95,        // Privacy policy
    "faq": 0.8,             // Frequently asked questions
    "landing": 0.7,         // Landing pages
    "form": 0.6,            // Forms and applications
    "promo": 0.5,           // Promotional content (lowest trust)
    "blog": 0.4             // Blog posts
  }
}
```

### Default Scores

```json
{
  "default_scores": {
    "domain": 0.5,          // Default for unknown domains
    "document_type": 0.5    // Default for unknown document types
  }
}
```

## Usage

### Python API

```python
from authority_scores import calculate_authority_score, add_domain_score, add_document_type_score

# Calculate authority score
score = calculate_authority_score('bankofamerica.com', 'terms')
# Returns: 0.93 (93%)

# Add new domain score
add_domain_score('new-partner.com', 0.7)

# Add new document type score
add_document_type_score('whitepaper', 0.9)
```

### Configuration Management

```python
from authority_scores import load_config_from_file, save_config_to_file

# Load configuration from JSON file
load_config_from_file()

# Save current scores to JSON file
save_config_to_file()
```

## Score Calculation

The final authority score is calculated as:

```
authority_score = (domain_score + type_score) / 2
```

### Examples

- `bankofamerica.com` + `terms`: (0.9 + 0.95) / 2 = **0.93 (93%)**
- `local` + `landing`: (0.5 + 0.7) / 2 = **0.6 (60%)**
- `unknown.com` + `promo`: (0.5 + 0.5) / 2 = **0.5 (50%)**

## Modifying Scores

### Method 1: Edit JSON Configuration File

1. Edit `authority_scores_config.json`
2. Add new domains or document types
3. Modify existing scores
4. Restart the application

### Method 2: Programmatic Updates

```python
from authority_scores import add_domain_score, add_document_type_score, save_config_to_file

# Add new scores
add_domain_score('trusted-partner.com', 0.8)
add_document_type_score('whitepaper', 0.9)

# Save to configuration file
save_config_to_file()
```

## Score Guidelines

### Domain Scores (0.0 to 1.0)

- **0.95-1.0**: Official main websites, government sites
- **0.85-0.94**: Official subdomains, trusted partners
- **0.70-0.84**: Partner sites, third-party integrations
- **0.50-0.69**: Unknown or less trusted domains
- **0.0-0.49**: Untrusted or suspicious domains

### Document Type Scores (0.0 to 1.0)

- **0.95-1.0**: Legal documents (disclosures, terms, privacy)
- **0.80-0.94**: Official information (FAQs, policies, technical docs)
- **0.60-0.79**: Informational content (landing pages, guides)
- **0.40-0.59**: Interactive content (forms, surveys)
- **0.0-0.39**: Promotional content (ads, marketing)

## Testing

Run the authority scores module to test configuration:

```bash
python authority_scores.py
```

This will:
1. Load configuration from JSON file
2. Display all current scores
3. Run test examples
4. Show any configuration errors

## Integration

The authority scores are automatically used by the enhanced metadata extractor:

```python
from processors.enhanced_metadata_extractor import EnhancedMetadataExtractor

# Authority scores are automatically calculated during metadata extraction
extractor = EnhancedMetadataExtractor(model_manager)
metadata = extractor.extract_document_metadata(text, file_path)
print(f"Authority Score: {metadata.authority_score}")
```

## Future Enhancements

- **Weighted Scoring**: Different weights for domain vs document type
- **Dynamic Scoring**: ML-based authority calculation
- **External APIs**: Integration with domain authority services
- **User Feedback**: Learning from user interactions
- **Time-based Scoring**: Scores that change over time
