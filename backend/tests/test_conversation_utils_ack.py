"""Unit tests for acknowledgment/coreference helper."""

from backend.utils.conversation_utils import is_ack_or_coref


def test_acknowledgement_tokens():
    assert is_ack_or_coref("yes") is True
    assert is_ack_or_coref("Sounds good") is True


def test_pronoun_acknowledgements():
    assert is_ack_or_coref("that") is True
    assert is_ack_or_coref("that one") is True
    assert is_ack_or_coref("those") is True


def test_short_frustrations_not_ack():
    assert is_ack_or_coref("it is hard") is False
    assert is_ack_or_coref("it is difficult") is False
    assert is_ack_or_coref("hard") is False


def test_non_ack_long_phrase():
    assert is_ack_or_coref("tell me about gold tier") is False
