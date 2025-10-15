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

"""Tests for RAG schema validation helpers."""

from backend.rag import RAG


def _make_rag_stub():
    rag = object.__new__(RAG)
    return rag


def test_validate_response_schema_success():
    rag = _make_rag_stub()
    payload = {
        "answer": "Test",
        "evidence": ["C1"],
        "missing": "",
        "confidence": "High",
        "faithfulness_score": 0.9,
        "completeness_score": 0.8,
        "answer_type": "answer",
        "abstained": False,
        "reasoning_notes": "",
        "clarifying_question": "",
        "interpreted_question": "What is test?"
    }

    valid, normalized, error = rag._validate_response_schema(payload)

    assert valid is True
    assert error == ""
    assert normalized["answer"] == "Test"
    assert isinstance(normalized["faithfulness_score"], float)
    assert normalized["abstained"] is False


def test_validate_response_schema_failure():
    rag = _make_rag_stub()
    payload = {"answer": "", "evidence": "not-a-list"}

    valid, normalized, error = rag._validate_response_schema(payload)

    assert valid is False
    assert normalized == {}
    assert "Missing field 'missing'" in error
    assert "Field 'evidence' must be a list" in error
