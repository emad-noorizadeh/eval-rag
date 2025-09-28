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

# answer_schema.py  (Pydantic v2)
from typing import List, Any
from pydantic import BaseModel, Field, field_validator

class AnswerSchema(BaseModel):
    """
    Canonical schema for RAG answers.
    All fields are normalized to stable types for downstream pipelines.
    """
    answer: str = Field("", description="Concise grounded answer.")
    evidence: List[str] = Field(default_factory=list, description="Chunk IDs or supporting snippets.")
    missing: str = Field("", description="What's missing; 'None' if complete.")
    confidence: str = Field("", description="High | Medium | Low")
    faithfulness_score: float = 0.0
    completeness_score: float = 0.0
    answer_type: str = Field("", description="fact | list | numeric | inference | abstain")
    abstained: bool = False
    reasoning_notes: str = ""

    # ---------- Validators (Pydantic v2) ----------

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_confidence(cls, v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip().lower()
        if s in {"high", "h"}:
            return "High"
        if s in {"medium", "med", "m"}:
            return "Medium"
        if s in {"low", "l"}:
            return "Low"
        # pass through as-is (capitalization left to the model caller)
        return str(v)

    @field_validator("faithfulness_score", "completeness_score", mode="before")
    @classmethod
    def _to_float(cls, v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return 0.0

    @field_validator("answer", "missing", "answer_type", "reasoning_notes", mode="before")
    @classmethod
    def _stringify(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)

    @field_validator("evidence", mode="before")
    @classmethod
    def _evidence_list(cls, v: Any) -> List[str]:
        """
        Coerce evidence into a list[str].
        - None -> []
        - "C1" -> ["C1"]
        - ["C1", 2, {"x":1}] -> ["C1","2","{'x': 1}"]
        """
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(x) for x in v]
        # any other type -> single stringified item
        return [str(v)]
