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
