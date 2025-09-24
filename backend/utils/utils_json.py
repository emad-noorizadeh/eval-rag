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

# utils_json.py

import json
import re
from typing import Any, Optional


def coerce_json(text: str) -> Optional[dict]:
    """
    Try to coerce a model's output into a Python dict.

    1. Try json.loads directly.
    2. Strip common wrappers like ```json ... ```.
    3. Regex-extract the first {...} or [...] block and try to parse that.
    4. If all else fails, return None.

    Parameters
    ----------
    text : str
        Raw string returned by the LLM.

    Returns
    -------
    dict or None
        Parsed JSON object if successful, otherwise None.
    """
    if not text:
        return None

    # Step 1: direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Step 2: strip common wrappers
    stripped = (
        text.strip()
        .lstrip("```json")
        .lstrip("```")
        .rstrip("```")
        .strip()
    )
    try:
        return json.loads(stripped)
    except Exception:
        pass

    # Step 3: regex extract JSON object or array
    match = re.search(r"(\{.*\}|$begin:math:display$.*$end:math:display$)", text, re.DOTALL)
    if match:
        snippet = match.group(1)
        try:
            return json.loads(snippet)
        except Exception:
            pass

    # Nothing worked
    return None


if __name__ == "__main__":
    # quick test
    samples = [
        '{"answer": "42", "confidence": "High"}',
        "```json\n{\"answer\":\"ok\"}\n```",
        "some text before {\"answer\": \"hi\"} after",
    ]
    for s in samples:
        print("IN :", s)
        print("OUT:", coerce_json(s))
        print("---")
