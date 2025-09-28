# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# utils_json.py
import json, ast, re
from typing import Any, Optional, Union

# ---------- Internal helpers ----------

def _strip_code_fences(s: str) -> str:
    # Remove fenced code markers while preserving inner content
    s = re.sub(r"^\s*```(?:json)?\s*", "", s, flags=re.IGNORECASE | re.MULTILINE)
    s = re.sub(r"\s*```\s*$", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*'''(?:json\.?|JSON\.?)?\s*", "", s, flags=re.IGNORECASE | re.MULTILINE)
    s = re.sub(r"\s*'''\s*$", "", s, flags=re.MULTILINE)
    return s.strip()

def _normalize_unicode_quotes(s: str) -> str:
    return (
        s.replace("\u201c", '"').replace("\u201d", '"')  # " "
         .replace("\u2018", "'").replace("\u2019", "'")  # ' '
    )

def _repair_common_glitches(s: str) -> str:
    t = s

    # Remove leading labels like: "json:", "Here is the JSON:", "Output:"
    t = re.sub(r"^\s*(json|output|result)\s*:\s*", "", t, flags=re.IGNORECASE)

    # Fix: "confidence"" "low"  ->  "confidence": "low"
    t = re.sub(r'("confidence")\s*"\s*("low"|"medium"|"high")', r'\1:\2', t, flags=re.IGNORECASE)

    # Remove trailing commas before } or ]
    t = re.sub(r',\s*([}\]])', r'\1', t)

    # Ensure bareword keys are quoted: confidence: "Low" -> "confidence": "Low"
    t = re.sub(r'(?m)(?P<pre>[\{\s,])(?P<key>[A-Za-z_][A-Za-z0-9_\-]*)\s*:', r'\g<pre>"\g<key>":', t)

    # Normalize Python literals to JSON
    t = re.sub(r"\bTrue\b", "true", t)
    t = re.sub(r"\bFalse\b", "false", t)
    t = re.sub(r"\bNone\b", "null", t)

    return t.strip()

def _balanced_substring(s: str, opener: str, closer: str) -> Optional[str]:
    depth = 0
    start = -1
    for i, ch in enumerate(s):
        if ch == opener:
            if depth == 0:
                start = i
            depth += 1
        elif ch == closer and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                return s[start:i+1]
    return None

def _extract_first_balanced_json(s: str) -> Optional[str]:
    # Try object first
    obj = _balanced_substring(s, "{", "}")
    if obj:
        return obj
    # Then array
    arr = _balanced_substring(s, "[", "]")
    if arr:
        return arr
    return None

# ---------- Public API ----------

def coerce_json(raw: Union[str, bytes, dict, list, Any]) -> Optional[dict]:
    """
    Robustly coerce LLM output into a dict.
    - strips ```/```json and '''/'''json fences
    - normalizes smart quotes
    - repairs common mistakes
    - extracts the first balanced JSON object/array
    - falls back to ast.literal_eval
    Returns a dict (preferred) or {"answer": "..."} fallback. Never raises.
    """
    # Already structured?
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"answer": "", "items": raw}

    # Bytes -> str
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")

    if not isinstance(raw, str):
        return {"answer": str(raw)}

    s = raw.strip()
    if not s:
        return {"answer": ""}

    # 1) strip code fences & normalize quotes
    s = _strip_code_fences(s)
    s = _normalize_unicode_quotes(s)

    # 2) try direct parse
    try:
        obj = json.loads(s)
        if isinstance(obj, str):
            # handle double-encoded json
            try:
                obj2 = json.loads(obj)
                return obj2 if isinstance(obj2, dict) else {"answer": obj}
            except Exception:
                return {"answer": obj}
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            return {"answer": "", "items": obj}
    except Exception:
        pass

    # 3) extract first balanced JSON block
    candidate = _extract_first_balanced_json(s)
    if candidate:
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else {"answer": "", "items": obj}
        except Exception:
            repaired = _repair_common_glitches(candidate)
            try:
                obj = json.loads(repaired)
                return obj if isinstance(obj, dict) else {"answer": "", "items": obj}
            except Exception:
                try:
                    lit = ast.literal_eval(repaired)
                    if isinstance(lit, dict):
                        return json.loads(json.dumps(lit, ensure_ascii=False))
                    if isinstance(lit, list):
                        return {"answer": "", "items": lit}
                except Exception:
                    pass

    # 4) attempt repairs on full string
    s2 = _repair_common_glitches(s)
    try:
        obj = json.loads(s2)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            return {"answer": "", "items": obj}
    except Exception:
        try:
            lit = ast.literal_eval(s2)
            if isinstance(lit, dict):
                return json.loads(json.dumps(lit, ensure_ascii=False))
            if isinstance(lit, list):
                return {"answer": "", "items": lit}
        except Exception:
            pass

    # 4.5) last-ditch inner-JSON if the text still contains JSON inside
    inner = _extract_first_balanced_json(s)
    if inner and inner != s:
        repaired = _repair_common_glitches(inner)
        try:
            obj = json.loads(repaired)
            if isinstance(obj, dict):
                return obj
            if isinstance(obj, list):
                return {"answer": "", "items": obj}
        except Exception:
            try:
                lit = ast.literal_eval(repaired)
                if isinstance(lit, dict):
                    return json.loads(json.dumps(lit, ensure_ascii=False))
                if isinstance(lit, list):
                    return {"answer": "", "items": lit}
            except Exception:
                pass

    # 5) give up → wrap as plain answer
    return {"answer": s}