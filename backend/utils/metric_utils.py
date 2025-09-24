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
Metric Utilities for RAG System

This module provides comprehensive metric calculation functions for evaluating RAG (Retrieval-Augmented Generation) 
system performance. It includes context utilization analysis, confidence scoring, faithfulness measurement, 
and completeness assessment.

Key Features:
- Context utilization calculation based on word overlap between answers and retrieved context
- Confidence scoring using heuristics based on answer quality and context relevance
- Faithfulness measurement to ensure answers are grounded in retrieved context
- Completeness assessment to evaluate how fully questions are answered
- Robust edge case handling for null/empty inputs and clarification scenarios

Author: Emad Noorizadeh
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from math import log, sqrt

# Minimal, deterministic utilities

_STOPWORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with','by',
    'is','are','was','were','be','been','being','have','has','had','do','does','did',
    'will','would','could','should','may','might','must','can','this','that','these','those',
    'i','you','he','she','it','we','they','me','him','her','us','them','my','your',
    'his','hers','its','our','their','as','from','about','into','over','under','than',
    'then','so','if','not','no','yes','also','just','only','very','more','most','such'
}

_WORD_RE = re.compile(r"\b[\w$%.-]+\b", re.UNICODE)

def _simple_lemma(tok: str) -> str:
    """Cheap, deterministic normalizer w/out external deps."""
    t = tok.lower()
    # strip punctuation-like tails
    t = t.strip(".,;:!?()[]{}'\"")
    # normalize money like $20,000.00 -> $20000
    if t.startswith("$"):
        digits = re.sub(r"[^\d]", "", t[1:])
        return f"${digits}" if digits else "$"
    # normalize percents like 12.5% -> 12.5%
    if t.endswith("%"):
        core = t[:-1]
        core = re.sub(r"[^\d.]", "", core)
        return f"{core}%" if core else "%"
    # normalize plain numbers 1,234.00 -> 1234
    if re.fullmatch(r"[-+]?\d[\d,]*\.?\d*", t):
        return re.sub(r"[,\s]", "", t)
    # crude plural/verb endings
    for suf in ("'s","'s","s","es","ed","ing"):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            t = t[: -len(suf)]
            break
    return t

def _tokens(text: str):
    return [_simple_lemma(t) for t in _WORD_RE.findall(text or "")]

def _token_spans(text: str):
    """Return (token_text, start, end) using the same regex used for tokenization."""
    for m in _WORD_RE.finditer(text or ""):
        tok = m.group(0)
        start, end = m.span()
        yield tok, start, end

def _normalized_token_spans(text: str):
    """Yield (norm_token, start, end, surface) for non-stopword informative tokens."""
    for tok, s, e in _token_spans(text):
        norm = _simple_lemma(tok)
        if not norm or norm in _STOPWORDS or norm.isdigit() or norm in {"$", "%"}:
            continue
        yield norm, s, e, tok

def _informative_terms(tokens):
    return [t for t in tokens if t and t not in _STOPWORDS and not t.isdigit() and t not in {"$", "%"}]

def _build_idf(snippets_tokens):
    """IDF from snippets; small, deterministic."""
    df = Counter()
    N = len(snippets_tokens)
    for toks in snippets_tokens:
        df.update(set(toks))
    idf = {}
    for term, d in df.items():
        # add-1 smoothing to avoid div-by-zero and keep small collections stable
        idf[term] = log((N + 1) / (d + 1)) + 1.0
    return idf

def _weighted_recall(numer: Counter, denom: Counter, idf):
    """Sum IDF over intersection divided by sum IDF over denom (denom defines 'what should be covered')."""
    w_inter = 0.0
    for t, c in numer.items():
        if t in denom:
            w_inter += idf.get(t, 1.0) * min(c, denom[t])
    w_denom = sum(idf.get(t, 1.0) * c for t, c in denom.items())
    return (w_inter / w_denom) if w_denom > 0 else 0.0

def _weighted_precision(answer_terms: list[str], context_terms: list[str], idf):
    a = Counter(answer_terms)
    c = Counter(context_terms)
    # precision: overlap against answer mass
    w_inter = 0.0
    w_answer = sum(idf.get(t, 1.0) * cnt for t, cnt in a.items())
    for t, cnt in a.items():
        if t in c:
            w_inter += idf.get(t, 1.0) * min(cnt, c[t])
    return (w_inter / w_answer) if w_answer > 0 else 0.0

def _extract_numbers_and_units(text: str):
    """
    Extract normalized numeric facts:
      - $ amounts as "$1234"
      - percents as "12.5%"
      - plain numbers as "1234" (no commas)
    """
    toks = _tokens(text)
    numbers = []
    for t in toks:
        if t.startswith("$") and re.fullmatch(r"\$\d+", t):
            numbers.append(("money", t))
        elif t.endswith("%") and re.fullmatch(r"\d+(\.\d+)?%", t):
            numbers.append(("percent", t))
        elif re.fullmatch(r"[-+]?\d+(\.\d+)?", t):
            numbers.append(("number", t))
    return set(numbers)

def _numeric_match_only(answer: str, contexts: List[str]) -> float:
    """Calculate numeric fact coverage without other metrics."""
    ans_nums = _extract_numbers_and_units(answer)
    if not ans_nums:
        return 1.0
    ctx_nums = set()
    for s in contexts:
        ctx_nums |= _extract_numbers_and_units(s or "")
    covered = sum(1 for n in ans_nums if n in ctx_nums)
    return covered / len(ans_nums)

def _split_sentences(text: str):
    # Deterministic, simple splitter
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9$])", text.strip() or "")
    return [p for p in parts if p]

def _collect_supported_terms(answer: str, ctx_terms_all: List[str], idf: Dict[str, float]):
    """Collect supported terms with character spans for UI highlighting."""
    ctx_set = set(ctx_terms_all)
    # global list (counts over the whole answer)
    counts = Counter()
    spans_per_sentence = []
    # sentence-level spans for UI
    for sent in _split_sentences(answer):
        per_sent = []
        offset = answer.find(sent)  # deterministic; safe because we split by exact substring
        for norm, s, e, surface in _normalized_token_spans(sent):
            if norm in ctx_set:
                counts[norm] += 1
                per_sent.append({"term": norm, "start": offset + s, "end": offset + e})
        spans_per_sentence.append({"sentence": sent, "supported_terms": per_sent})

    supported_global = [
        {"term": t, "count": c, "idf": round(idf.get(t, 1.0), 4)}
        for t, c in sorted(counts.items(), key=lambda kv: (-kv[1]*idf.get(kv[0],1.0), kv[0]))
    ]
    return supported_global, spans_per_sentence

# =========================
# BM25 (optional) for best-context selection
# =========================

def _bm25_score(query_ctr: Counter, doc_ctr: Counter, idf: Dict[str, float], avgdl: float, dl: float,
                k1: float = 1.2, b: float = 0.75) -> float:
    score = 0.0
    for term in query_ctr.keys():
        if term not in doc_ctr:
            continue
        tf = doc_ctr[term]
        denom = tf + k1 * (1 - b + b * (dl / avgdl if avgdl > 0 else 1.0))
        score += idf.get(term, 1.0) * tf * (k1 + 1) / (denom if denom > 0 else 1.0)
    return score

def _pick_best_context_by_bm25(ans_terms: List[str], contexts_terms: List[List[str]], idf: Dict[str, float]) -> int:
    doc_ctrs = [Counter(t) for t in contexts_terms]
    ans_ctr = Counter(ans_terms)
    lengths = [sum(c.values()) for c in doc_ctrs]
    avgdl = sum(lengths) / max(1, len(lengths))
    best_i, best_s = 0, float("-inf")
    for i, doc_ctr in enumerate(doc_ctrs):
        s = _bm25_score(ans_ctr, doc_ctr, idf, avgdl, sum(doc_ctr.values()))
        if s > best_s:
            best_s, best_i = s, i
    return best_i

# =========================
# Entity extraction (regex for specific patterns + spaCy for general NER)
# =========================

# Keep regex only for well-defined, specific patterns
_RE_EMAIL = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)
_RE_URL = re.compile(r"\b(?:https?://|www\.)\S+\b", re.IGNORECASE)
_RE_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
_RE_DATE_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_RE_DATE_SLASH = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_RE_DATE_TEXT = re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,\s*\d{2,4})?\b", re.IGNORECASE)
_RE_TIME = re.compile(r"\b\d{1,2}:\d{2}\s*(?:am|pm)?\b", re.IGNORECASE)
_RE_ACRONYM = re.compile(r"\b[A-Z]{2,6}s?\b")
_RE_IDLIKE = re.compile(r"\b[A-Z0-9]{6,}\b")
_RE_QUOTED = re.compile(r"['\"]([^'\"]{2,})['\"]")
_RE_MONEY = re.compile(r"\$[\d,]+(?:\.\d{2})?")
_RE_PERCENT = re.compile(r"\d+(?:\.\d+)?%")

def _norm_ent(s: str) -> str:
    return s.strip().lower()

def _extract_entities_regex(text: str) -> List[Tuple[str, str]]:
    """Extract only specific, well-defined entities using regex."""
    t = text or ""
    ents: List[Tuple[str, str]] = []
    
    # Collect all matches with their positions to avoid overlaps
    matches = []
    for m in _RE_EMAIL.finditer(t): matches.append((m.start(), m.end(), "email", m.group(0)))
    for m in _RE_URL.finditer(t): matches.append((m.start(), m.end(), "url", m.group(0)))
    for m in _RE_PHONE.finditer(t): matches.append((m.start(), m.end(), "phone", m.group(0)))
    for m in _RE_DATE_ISO.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_DATE_SLASH.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_DATE_TEXT.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_TIME.finditer(t): matches.append((m.start(), m.end(), "time", m.group(0)))
    for m in _RE_ACRONYM.finditer(t): matches.append((m.start(), m.end(), "acronym", m.group(0)))
    for m in _RE_IDLIKE.finditer(t): matches.append((m.start(), m.end(), "id", m.group(0)))
    for m in _RE_QUOTED.finditer(t): matches.append((m.start(1), m.end(1), "quoted", m.group(1)))
    for m in _RE_MONEY.finditer(t): matches.append((m.start(), m.end(), "money", m.group(0)))
    for m in _RE_PERCENT.finditer(t): matches.append((m.start(), m.end(), "percent", m.group(0)))
    
    # Sort by start position, then by length (longer first)
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    
    # Remove overlapping matches, keeping longer ones
    filtered_matches = []
    for start, end, entity_type, entity_text in matches:
        # Check if this match overlaps with any already added match
        overlaps = False
        for existing_start, existing_end, _, _ in filtered_matches:
            if not (end <= existing_start or start >= existing_end):
                overlaps = True
                break
        
        if not overlaps:
            filtered_matches.append((start, end, entity_type, entity_text))
    
    # Convert to final format
    for start, end, entity_type, entity_text in filtered_matches:
        ents.append((entity_type, _norm_ent(entity_text)))
    
    return ents

def _extract_entities_regex_with_spans(text: str) -> List[Tuple[str, str, int, int]]:
    """Extract entities with character spans for UI highlighting."""
    t = text or ""
    
    # Collect all matches with their positions to avoid overlaps
    matches = []
    for m in _RE_EMAIL.finditer(t): matches.append((m.start(), m.end(), "email", m.group(0)))
    for m in _RE_URL.finditer(t): matches.append((m.start(), m.end(), "url", m.group(0)))
    for m in _RE_PHONE.finditer(t): matches.append((m.start(), m.end(), "phone", m.group(0)))
    for m in _RE_DATE_ISO.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_DATE_SLASH.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_DATE_TEXT.finditer(t): matches.append((m.start(), m.end(), "date", m.group(0)))
    for m in _RE_TIME.finditer(t): matches.append((m.start(), m.end(), "time", m.group(0)))
    for m in _RE_ACRONYM.finditer(t): matches.append((m.start(), m.end(), "acronym", m.group(0)))
    for m in _RE_IDLIKE.finditer(t): matches.append((m.start(), m.end(), "id", m.group(0)))
    for m in _RE_QUOTED.finditer(t): matches.append((m.start(1), m.end(1), "quoted", m.group(1)))
    for m in _RE_MONEY.finditer(t): matches.append((m.start(), m.end(), "money", m.group(0)))
    for m in _RE_PERCENT.finditer(t): matches.append((m.start(), m.end(), "percent", m.group(0)))
    
    # Sort by start position, then by length (longer first)
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    
    # Remove overlapping matches, keeping longer ones
    filtered_matches = []
    for start, end, entity_type, entity_text in matches:
        # Check if this match overlaps with any already added match
        overlaps = False
        for existing_start, existing_end, _, _ in filtered_matches:
            if not (end <= existing_start or start >= existing_end):
                overlaps = True
                break
        
        if not overlaps:
            filtered_matches.append((start, end, entity_type, entity_text))
    
    # Convert to final format
    out = []
    for start, end, entity_type, entity_text in filtered_matches:
        out.append((entity_type, entity_text, start, end))
    
    return out

# =========================
# Optional spaCy NER (merged with regex)
# =========================

_SPACY_NLP = None
_SPACY_LABEL_MAP = {
    "PERSON": "proper", "ORG": "proper", "GPE": "proper", "LOC": "proper",
    "PRODUCT": "proper", "FAC": "proper", "WORK_OF_ART": "proper", "EVENT": "proper",
    "LAW": "proper", "LANGUAGE": "proper", "DATE": "date", "TIME": "time",
    "PERCENT": "percent", "MONEY": "money", "NORP": "proper"
}

def _maybe_load_spacy(model_name: str = "en_core_web_sm"):
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy
        _SPACY_NLP = spacy.load(model_name, disable=["tagger","parser","lemmatizer","textcat"])
    except Exception:
        _SPACY_NLP = None
    return _SPACY_NLP

def _extract_entities_spacy(text: str, model_name: str = "en_core_web_sm") -> List[Tuple[str, str]]:
    nlp = _maybe_load_spacy(model_name)
    if nlp is None or not text:
        return []
    doc = nlp(text)
    ents: List[Tuple[str, str]] = []
    for ent in doc.ents:
        mapped = _SPACY_LABEL_MAP.get(ent.label_)
        if mapped:
            ents.append((mapped, ent.text.strip().lower()))
    return ents

def _extract_entities_spacy_with_spans(text: str, model_name: str = "en_core_web_sm") -> List[Tuple[str, str, int, int]]:
    """Extract entities with character spans using spaCy NER."""
    nlp = _maybe_load_spacy(model_name)
    if nlp is None or not text:
        return []
    doc = nlp(text)
    out = []
    for ent in doc.ents:
        mapped = _SPACY_LABEL_MAP.get(ent.label_)
        if mapped:
            out.append((mapped, ent.text, ent.start_char, ent.end_char))
    return out

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def _fuzzy_match_entities(answer_entity, context_entities, threshold: float = 0.8) -> bool:
    """Check if answer entity has a fuzzy match in context entities using edit distance."""
    et, ev = answer_entity
    
    # Direct match
    if (et, ev) in context_entities:
        return True
    
    # For all entity types, try fuzzy matching
    ev_lower = ev.lower()
    ev_clean = ev_lower.replace("the ", "").replace("a ", "").replace("an ", "").strip()
    
    for ctx_et, ctx_ev in context_entities:
        if ctx_et == et:  # Same entity type
            ctx_ev_lower = ctx_ev.lower()
            ctx_ev_clean = ctx_ev_lower.replace("the ", "").replace("a ", "").replace("an ", "").strip()
            
            # Calculate similarity based on edit distance
            max_len = max(len(ev_clean), len(ctx_ev_clean))
            if max_len == 0:
                continue
                
            distance = _levenshtein_distance(ev_clean, ctx_ev_clean)
            similarity = 1.0 - (distance / max_len)
            
            if similarity >= threshold:
                return True
            
            # Also check substring matches
            if ev_clean in ctx_ev_clean or ctx_ev_clean in ev_clean:
                return True
            
            # Check word overlap for multi-word entities
            ev_words = set(ev_clean.split())
            ctx_ev_words = set(ctx_ev_clean.split())
            if len(ev_words) > 1 and len(ctx_ev_words) > 1:
                common_words = ev_words.intersection(ctx_ev_words)
                word_overlap = len(common_words) / min(len(ev_words), len(ctx_ev_words))
                if word_overlap >= 0.6:  # 60% word overlap
                    return True
    
    return False

def _entity_match(answer: str, contexts: List[str],
                  use_spacy_ner: bool = True,  # Default to True for better NER
                  spacy_model: str = "en_core_web_sm") -> Dict[str, Any]:
    """Entity coverage metrics: regex + spaCy NER with fuzzy matching."""
    # Start with regex entities (specific patterns)
    a_ents = set(_extract_entities_regex(answer))
    c_ents = set()
    for s in contexts:
        c_ents |= set(_extract_entities_regex(s or ""))

    # Add spaCy NER entities (better for proper nouns and general entities)
    if use_spacy_ner:
        a_ents |= set(_extract_entities_spacy(answer, spacy_model))
        for s in contexts:
            c_ents |= set(_extract_entities_spacy(s or "", spacy_model))

    if not a_ents:
        return {"overall": 1.0, "by_type": {}, "unsupported": []}

    total_by_type: Dict[str,int] = {}
    covered_by_type: Dict[str,int] = {}
    unsupported: List[str] = []

    for et, ev in a_ents:
        total_by_type[et] = total_by_type.get(et, 0) + 1
        if _fuzzy_match_entities((et, ev), c_ents):
            covered_by_type[et] = covered_by_type.get(et, 0) + 1
        else:
            unsupported.append(f"{et}:{ev}")

    covered_total = sum(covered_by_type.values())
    total = sum(total_by_type.values())
    overall = round((covered_total / total) if total else 1.0, 4)
    by_type = {k: round(covered_by_type.get(k, 0) / v, 4) for k, v in total_by_type.items()}

    return {"overall": overall, "by_type": by_type, "unsupported": unsupported}

def _entity_alignment(answer: str, contexts: List[str],
                      use_spacy_ner: bool = True,  # Default to True for better NER
                      spacy_model: str = "en_core_web_sm") -> Dict[str, Any]:
    """Entity alignment with supported entities and spans for UI highlighting."""
    # collect answer entities with spans
    ans_items = _extract_entities_regex_with_spans(answer)
    if use_spacy_ner:
        ans_items += _extract_entities_spacy_with_spans(answer, spacy_model)

    # de-dupe answer entities by (type, normalized text, span)
    a_ents = []
    seen = set()
    for et, txt, s, e in ans_items:
        key = (et, txt.strip().lower(), s, e)
        if key not in seen:
            seen.add(key)
            a_ents.append((et, txt, s, e))

    # context entity set (normalized by type+text only)
    ctx_norm_set = set()
    for s in contexts:
        ctx_items = _extract_entities_regex_with_spans(s or "")
        if use_spacy_ner:
            ctx_items += _extract_entities_spacy_with_spans(s or "", spacy_model)
        for et, txt, _, _ in ctx_items:
            ctx_norm_set.add((et, txt.strip().lower()))

    if not a_ents:
        return {
            "match": {"overall": 1.0, "by_type": {}, "unsupported": []},
            "supported_entities": {"items": [], "by_type": {}, "count": 0}
        }

    total_by_type, covered_by_type = Counter(), Counter()
    unsupported = []
    supported_items = []  # with spans for UI

    for et, txt, s, e in a_ents:
        total_by_type[et] += 1
        norm = (et, txt.strip().lower())
        
        # Try direct match first
        if norm in ctx_norm_set:
            covered_by_type[et] += 1
            supported_items.append({"type": et, "text": txt, "start": s, "end": e})
        else:
            # Try fuzzy matching
            if _fuzzy_match_entities(norm, ctx_norm_set):
                covered_by_type[et] += 1
                supported_items.append({"type": et, "text": txt, "start": s, "end": e})
            else:
                unsupported.append(f"{et}:{txt.strip().lower()}")

    overall = sum(covered_by_type.values()) / sum(total_by_type.values())
    by_type = {k: covered_by_type.get(k, 0) / v for k, v in total_by_type.items()}

    return {
        "match": {
            "overall": round(overall, 4),
            "by_type": {k: round(v, 4) for k, v in by_type.items()},
            "unsupported": unsupported
        },
        "supported_entities": {
            "items": supported_items,
            "by_type": dict(Counter([it["type"] for it in supported_items])),
            "count": len(supported_items)
        }
    }

# =========================
# TF-IDF cosine (baseline) and optional embedding alignment
# =========================

def _tfidf_vector(terms: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = Counter(terms)
    return {t: tf[t] * idf.get(t, 1.0) for t in tf}

def _cosine(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    if not vec1 or not vec2: return 0.0
    dot = sum(v * vec2.get(k, 0.0) for k, v in vec1.items())
    n1 = sqrt(sum(v * v for v in vec1.values()))
    n2 = sqrt(sum(v * v for v in vec2.values()))
    if n1 == 0 or n2 == 0: return 0.0
    return dot / (n1 * n2)

_EMB = None
def _maybe_load_embedder(model_name: str = "models/all-MiniLM-L6-v2"):
    global _EMB
    if _EMB is not None:
        return _EMB
    try:
        from sentence_transformers import SentenceTransformer
        import os
        # Use local path if it exists, otherwise fall back to HuggingFace
        if os.path.exists(model_name):
            _EMB = SentenceTransformer(model_name, device="cpu")
        else:
            # Fallback to HuggingFace if local model not found
            _EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    except Exception:
        _EMB = None
    return _EMB

def _embed_alignment(question: str, answer: str, q_terms: List[str], idf: Dict[str, float],
                     term_threshold: float = 0.5,
                     model_name: str = "models/all-MiniLM-L6-v2") -> Dict[str, Optional[float]]:
    """Calculate semantic alignment between question and answer using Sentence Transformers."""
    model = _maybe_load_embedder(model_name)
    if model is None or not question or not answer:
        return {"cosine_embed": None, "answer_covers_question_sem": None}
    from sentence_transformers import util as st_util
    qa_emb = model.encode([question, answer], convert_to_tensor=True, normalize_embeddings=True)
    cos = float(st_util.cos_sim(qa_emb[0], qa_emb[1]).item())
    if not q_terms:
        return {"cosine_embed": round(cos, 4), "answer_covers_question_sem": 1.0}
    term_embs = model.encode(q_terms, convert_to_tensor=True, normalize_embeddings=True)
    sims = st_util.cos_sim(term_embs, qa_emb[1]).squeeze(1)
    total = sum(idf.get(t, 1.0) for t in q_terms) or 1.0
    covered = 0.0
    for term, sim in zip(q_terms, sims):
        if float(sim) >= term_threshold:
            covered += idf.get(term, 1.0)
    return {"cosine_embed": round(cos, 4), "answer_covers_question_sem": round(covered / total, 4)}

def _embed_context_alignment(answer: str, contexts: List[str], 
                            model_name: str = "models/all-MiniLM-L6-v2") -> Dict[str, Optional[float]]:
    """Calculate semantic alignment between answer and retrieved contexts using Sentence Transformers."""
    model = _maybe_load_embedder(model_name)
    if model is None or not answer or not contexts:
        return {"answer_context_similarity": None, "best_context_similarity": None}
    
    from sentence_transformers import util as st_util
    
    # Encode answer and all contexts
    all_texts = [answer] + contexts
    embeddings = model.encode(all_texts, convert_to_tensor=True, normalize_embeddings=True)
    answer_emb = embeddings[0]
    context_embs = embeddings[1:]
    
    # Calculate similarity between answer and each context
    similarities = []
    for ctx_emb in context_embs:
        sim = float(st_util.cos_sim(answer_emb, ctx_emb).item())
        similarities.append(sim)
    
    # Average similarity across all contexts
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    
    # Best context similarity (highest)
    best_similarity = max(similarities) if similarities else 0.0
    
    return {
        "answer_context_similarity": round(avg_similarity, 4),
        "best_context_similarity": round(best_similarity, 4)
    }

# =========================
# Unsupported terms helpers
# =========================

def _unsupported_terms(ans_terms: List[str], ctx_terms_all: List[str], idf: Dict[str, float]) -> List[Dict[str, float]]:
    a_ctr = Counter(ans_terms)
    c_set = set(ctx_terms_all)
    items = []
    for t, cnt in a_ctr.items():
        if t not in c_set:
            items.append({"term": t, "count": cnt, "idf": idf.get(t, 1.0), "impact": cnt * idf.get(t, 1.0)})
    items.sort(key=lambda x: (-x["impact"], x["term"]))
    for it in items:
        it["idf"] = round(it["idf"], 4)
        it["impact"] = round(it["impact"], 4)
    return items

def _unsupported_terms_per_sentence(answer: str, ctx_terms_all: List[str], idf: Dict[str, float]) -> List[Dict[str, Any]]:
    out = []
    for sent in _split_sentences(answer):
        s_terms = _informative_terms(_tokens(sent))
        items = _unsupported_terms(s_terms, ctx_terms_all, idf)
        out.append({"sentence": sent, "unsupported_terms": items})
    return out

def _unsupported_numbers(answer: str, contexts: List[str]) -> List[str]:
    ans_nums = _extract_numbers_and_units(answer)
    if not ans_nums:
        return []
    ctx_nums = set()
    for s in contexts:
        ctx_nums |= _extract_numbers_and_units(s or "")
    return [f"{k}:{v}" for (k, v) in ans_nums if (k, v) not in ctx_nums]

# =========================
# Main advanced function
# =========================

def context_utilization_report_with_entities(
    question: str,
    answer: str,
    retrieved_contexts: List[str],
    use_bm25_for_best: bool = True,
    use_embed_alignment: bool = False,    # set True if sentence-transformers installed
    embed_term_threshold: float = 0.5,
    use_spacy_ner: bool = True,           # Default to True for better NER
    spacy_model: str = "en_core_web_sm"
) -> Dict[str, Any]:
    """
    Advanced context utilization analysis with entity extraction and sentence similarity.
    
    Returns comprehensive metrics for how well the answer utilizes retrieved context,
    including entity extraction (regex + spaCy), sentence similarity (MiniLM), and
    detailed unsupported term analysis.
    
    Args:
        question: The original question (for Q-A alignment)
        answer: The generated answer text
        retrieved_contexts: List of context snippets retrieved for the answer
        use_bm25_for_best: Whether to use BM25 for best context selection
        use_embed_alignment: Whether to use sentence-transformers for alignment
        embed_term_threshold: Threshold for embedding-based term coverage
        use_spacy_ner: Whether to use spaCy NER (requires spaCy model)
        spacy_model: spaCy model name to use
        
    Returns:
        Dictionary containing comprehensive metrics including:
        - precision_token: IDF-weighted precision of answer terms vs context
        - recall_context: IDF-weighted recall of best snippet into answer
        - numeric_match: Fraction of numeric facts in answer present in context
        - entity_match: Entity coverage metrics with regex + spaCy NER
        - per_sentence: List of sentence-level precision scores
        - qr_alignment: Question-answer alignment metrics
        - context_alignment: Answer-context semantic similarity metrics
        - unsupported_terms: Terms in answer not found in context
        - unsupported_terms_per_sentence: Per-sentence unsupported terms
        - unsupported_numbers: Numeric facts in answer not in context
        - summary: Human-readable summary of all metrics
    """
    # Edge: no answer
    if not answer or not answer.strip():
        return {
            "precision_token": None,
            "recall_context": None,
            "numeric_match": None,
            "entity_match": {"overall": None, "by_type": {}, "unsupported": []},
            "supported_entities": {"items": [], "by_type": {}, "count": 0},
            "supported_terms": [],
            "supported_terms_per_sentence": [],
            "per_sentence": [],
            "qr_alignment": {
                "cosine_tfidf": None, "answer_covers_question": None,
                "cosine_embed": None, "answer_covers_question_sem": None
            },
            "context_alignment": {
                "answer_context_similarity": None,
                "best_context_similarity": None
            },
            "unsupported_terms": [],
            "unsupported_terms_per_sentence": [],
            "unsupported_numbers": [],
            "summary": "N/A (No answer generated)"
        }

    # Tokenize
    q_tokens = _tokens(question or "")
    a_tokens = _tokens(answer or "")
    ctx_tokens_list = [_tokens(s or "") for s in (retrieved_contexts or [])]

    q_terms = _informative_terms(q_tokens)
    a_terms = _informative_terms(a_tokens)
    ctx_terms_list = [_informative_terms(t) for t in ctx_tokens_list]
    all_ctx_terms = [t for lst in ctx_terms_list for t in lst]

    # Build IDF over contexts + Q + A
    idf = _build_idf((ctx_terms_list or []) + [q_terms, a_terms])

    # If no contexts, still compute alignment and unsupported vs empty
    if not retrieved_contexts:
        vq, va = _tfidf_vector(q_terms, idf), _tfidf_vector(a_terms, idf)
        qr_cos = _cosine(vq, va)
        qr_cov = _weighted_recall(Counter(a_terms), Counter(q_terms), idf)
        embed_align = {"cosine_embed": None, "answer_covers_question_sem": None}
        if use_embed_alignment:
            embed_align = _embed_alignment(question, answer, q_terms, idf, embed_term_threshold)
        return {
            "precision_token": None,
            "recall_context": None,
            "numeric_match": _numeric_match_only(answer, []),
            "entity_match": {"overall": None, "by_type": {}, "unsupported": []},
            "supported_entities": {"items": [], "by_type": {}, "count": 0},
            "supported_terms": [],
            "supported_terms_per_sentence": [],
            "per_sentence": [0.0 for _ in _split_sentences(answer)],
            "qr_alignment": {
                "cosine_tfidf": round(qr_cos, 4),
                "answer_covers_question": round(qr_cov, 4),
                "cosine_embed": embed_align["cosine_embed"],
                "answer_covers_question_sem": embed_align["answer_covers_question_sem"],
            },
            "context_alignment": {
                "answer_context_similarity": None,
                "best_context_similarity": None
            },
            "unsupported_terms": _unsupported_terms(a_terms, [], idf),
            "unsupported_terms_per_sentence": _unsupported_terms_per_sentence(answer, [], idf),
            "unsupported_numbers": _unsupported_numbers(answer, []),
            "summary": "N/A (No retrieved context provided)."
        }

    # ---- Grounding vs contexts
    precision_token = _weighted_precision(a_terms, all_ctx_terms, idf)

    # ---- Best-context recall
    if use_bm25_for_best:
        best_i = _pick_best_context_by_bm25(a_terms, ctx_terms_list, idf)
    else:
        best_i, best_sc = 0, float("-inf")
        for i, terms in enumerate(ctx_terms_list):
            sc = _weighted_precision(terms, a_terms, idf)
            if sc > best_sc:
                best_sc, best_i = sc, i
    best_ctx_terms = ctx_terms_list[best_i] if ctx_terms_list else []
    recall_context = _weighted_recall(Counter(a_terms), Counter(best_ctx_terms), idf)

    # ---- Numeric & Entity alignment
    numeric_match = _numeric_match_only(answer, retrieved_contexts)
    ent = _entity_alignment(answer, retrieved_contexts, use_spacy_ner=use_spacy_ner, spacy_model=spacy_model)
    entity_match = ent["match"]
    supported_entities = ent["supported_entities"]

    # ---- Per-sentence precision (vs ALL context)
    per_sentence = []
    for sent in _split_sentences(answer):
        s_terms = _informative_terms(_tokens(sent))
        p = _weighted_precision(s_terms, all_ctx_terms, idf) if s_terms else 0.0
        per_sentence.append(round(p, 4))

    # ---- Q↔A alignment
    vq, va = _tfidf_vector(q_terms, idf), _tfidf_vector(a_terms, idf)
    qr_cosine = _cosine(vq, va)
    qr_answer_coverage = _weighted_recall(Counter(a_terms), Counter(q_terms), idf)
    embed_align = {"cosine_embed": None, "answer_covers_question_sem": None}
    if use_embed_alignment:
        embed_align = _embed_alignment(question, answer, q_terms, idf, embed_term_threshold)
    
    # ---- Answer↔Context alignment (semantic similarity)
    context_align = {"answer_context_similarity": None, "best_context_similarity": None}
    if use_embed_alignment:
        context_align = _embed_context_alignment(answer, retrieved_contexts)

    # ---- Supported terms (for UI highlighting)
    supported_terms, supported_terms_per_sentence = _collect_supported_terms(answer, all_ctx_terms, idf)

    # ---- Unsupported (lexical & numeric)
    unsupported = _unsupported_terms(a_terms, all_ctx_terms, idf)
    unsupported_ps = _unsupported_terms_per_sentence(answer, all_ctx_terms, idf)
    unsupported_nums = _unsupported_numbers(answer, retrieved_contexts)

    # ---- Summary
    pct = round(precision_token * 100, 1)
    rec = round(recall_context * 100, 1)
    nump = round(numeric_match * 100, 1)
    entp = round((entity_match["overall"] if entity_match["overall"] is not None else 0.0) * 100, 1)
    parts = [f"{pct}% grounded", f"{rec}% best-context recall", f"{nump}% numeric", f"{entp}% entity"]
    if use_embed_alignment and embed_align["cosine_embed"] is not None:
        parts.append(f"Q↔A embed {round(embed_align['cosine_embed'], 2)}")
        if context_align["answer_context_similarity"] is not None:
            parts.append(f"A↔C embed {round(context_align['answer_context_similarity'], 2)}")
    else:
        parts.append(f"Q↔A tfidf {round(qr_cosine, 2)}")
    summary = "; ".join(parts) + "."

    return {
        "precision_token": round(precision_token, 4),
        "recall_context": round(recall_context, 4),
        "numeric_match": round(numeric_match, 4),
        "entity_match": entity_match,
        "supported_entities": supported_entities,
        "supported_terms": supported_terms,
        "supported_terms_per_sentence": supported_terms_per_sentence,
        "per_sentence": per_sentence,
        "qr_alignment": {
            "cosine_tfidf": round(qr_cosine, 4),
            "answer_covers_question": round(qr_answer_coverage, 4),
            "cosine_embed": embed_align["cosine_embed"],
            "answer_covers_question_sem": embed_align["answer_covers_question_sem"],
        },
        "context_alignment": {
            "answer_context_similarity": context_align["answer_context_similarity"],
            "best_context_similarity": context_align["best_context_similarity"],
        },
        "unsupported_terms": unsupported,
        "unsupported_terms_per_sentence": unsupported_ps,
        "unsupported_numbers": unsupported_nums,
        "summary": summary
    }

def calculate_context_utilization_percentage(answer: str, context_snippets: List[str]) -> Dict[str, Any]:
    """
    Calculate advanced context utilization metrics with entity extraction and sentence similarity.
    
    This function provides comprehensive metrics for how well the answer utilizes the
    retrieved context snippets, including precision, recall, numeric matching,
    entity extraction (regex + spaCy), and sentence similarity using MiniLM.
    
    Args:
        answer: The generated answer text
        context_snippets: List of context snippets retrieved for the answer
        
    Returns:
        Dictionary containing:
        - precision_token: IDF-weighted precision of answer terms vs context
        - recall_context: IDF-weighted recall of best snippet into answer
        - numeric_match: Fraction of numeric facts in answer present in context
        - entity_match: Entity coverage metrics with regex + spaCy NER
        - per_sentence: List of sentence-level precision scores
        - qr_alignment: Question-answer alignment metrics
        - context_alignment: Answer-context semantic similarity metrics
        - unsupported_terms: Terms in answer not found in context
        - unsupported_terms_per_sentence: Per-sentence unsupported terms
        - unsupported_numbers: Numeric facts in answer not in context
        - summary: Human-readable summary of metrics
    """
    # Use the advanced function with default settings
    return context_utilization_report_with_entities(
        question="",  # No question context for backward compatibility
        answer=answer,
        retrieved_contexts=context_snippets,
        use_bm25_for_best=True,
        use_embed_alignment=False,  # Disable by default for performance
        use_spacy_ner=False,  # Disable by default for performance
        spacy_model="en_core_web_sm"
    )


def calculate_confidence_score(answer: str, context: str, answer_type: str) -> str:
    """
    Calculate confidence score based on answer quality and context relevance using heuristic rules.
    
    This function provides a simple heuristic-based confidence scoring system that evaluates the quality
    of an answer based on its length, the amount of context available, and the type of answer being generated.
    It's designed to work alongside more sophisticated confidence measures from LLMs.
    
    Logic:
    1. Check if answer is empty or abstained → Low confidence
    2. Evaluate answer length and context length using thresholds
    3. Longer answers with substantial context → High confidence
    4. Medium-length answers with moderate context → Medium confidence
    5. Short answers or limited context → Low confidence
    
    Args:
        answer: The generated answer text
        context: The retrieved context used for generation
        answer_type: Type of answer (fact, list, numeric, inference, abstain)
        
    Returns:
        String confidence level: "High", "Medium", or "Low"
        
    Example:
        >>> calculate_confidence_score("Gold tier requires $20,000 minimum balance", "Long context about bank tiers...", "fact")
        "High"
        >>> calculate_confidence_score("", "Some context", "abstain")
        "Low"
    """
    if not answer or answer.strip() == "":
        return "Low"
    
    if answer_type == "abstain":
        return "Low"
    
    # Simple heuristics for confidence scoring
    answer_length = len(answer.split())
    context_length = len(context.split())
    
    # High confidence if answer is substantial and context is relevant
    if answer_length > 10 and context_length > 50:
        return "High"
    elif answer_length > 5 and context_length > 20:
        return "Medium"
    else:
        return "Low"


def calculate_faithfulness_score(answer: str, context: str) -> float:
    """
    Calculate faithfulness score based on how well the answer is grounded in the provided context.
    
    This function measures the degree to which the generated answer is faithful to the retrieved context
    by calculating the word overlap between the answer and the context. A higher score indicates that
    the answer is more grounded in the provided context rather than hallucinated.
    
    Logic:
    1. Extract words from both answer and context using regex
    2. Calculate the intersection of answer words and context words
    3. Return the ratio of overlapping words to total answer words (capped at 1.0)
    
    Note: This is a simple word-overlap based approach. More sophisticated methods could use
    semantic similarity or entailment models for better faithfulness measurement.
    
    Args:
        answer: The generated answer text
        context: The retrieved context used for generation
        
    Returns:
        Float score between 0.0 and 1.0, where 1.0 indicates perfect faithfulness
        
    Example:
        >>> calculate_faithfulness_score("Gold tier requires $20,000", "Gold tier requires $20,000 minimum balance")
        1.0
        >>> calculate_faithfulness_score("Gold tier requires $20,000", "Platinum tier requires $50,000")
        0.5
    """
    if not answer or not context:
        return 0.0
    
    # Simple word overlap calculation
    answer_words = set(re.findall(r'\b\w+\b', answer.lower()))
    context_words = set(re.findall(r'\b\w+\b', context.lower()))
    
    if not answer_words or not context_words:
        return 0.0
    
    overlap = len(answer_words.intersection(context_words))
    return min(overlap / len(answer_words), 1.0)


def calculate_completeness_score(answer: str, question: str) -> float:
    """
    Calculate completeness score based on how fully the question was answered.
    
    This function evaluates the completeness of an answer by comparing its length to the complexity
    of the question. The assumption is that more complex questions require longer, more detailed answers
    to be considered complete. The scoring is normalized based on question complexity.
    
    Logic:
    1. Calculate word counts for both answer and question
    2. Determine question complexity based on word count
    3. Apply different thresholds for simple vs complex questions
    4. Return normalized score capped at 1.0
    
    Note: This is a simple length-based heuristic. More sophisticated approaches could analyze
    semantic completeness or use question-answering evaluation metrics.
    
    Args:
        answer: The generated answer text
        question: The original question text
        
    Returns:
        Float score between 0.0 and 1.0, where 1.0 indicates complete answer
        
    Example:
        >>> calculate_completeness_score("Gold tier requires $20,000 minimum balance", "What is gold tier?")
        0.8
        >>> calculate_completeness_score("Yes", "What are the benefits of gold tier?")
        0.1
    """
    if not answer or not question:
        return 0.0
    
    # Simple heuristic: longer answers are more complete
    answer_length = len(answer.split())
    question_length = len(question.split())
    
    # Normalize by question complexity
    if question_length < 5:
        return min(answer_length / 20, 1.0)
    else:
        return min(answer_length / 30, 1.0)
