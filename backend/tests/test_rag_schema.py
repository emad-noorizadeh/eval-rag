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
