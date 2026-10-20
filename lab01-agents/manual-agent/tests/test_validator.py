"""Тести валідатора рішень моделі (вимога 9)."""

import pytest
from agent.errors import DecisionError
from agent.validator import validate_decision


def test_valid_lookup():
    validate_decision({"action": "lookup_http_status", "arguments": {"code": "200"}})


def test_valid_list_class():
    validate_decision({"action": "list_status_class", "arguments": {"status_class": "4xx"}})


def test_valid_finish():
    validate_decision({"action": "finish", "arguments": {"answer": "Відповідь готова."}})


@pytest.mark.parametrize(
    "decision",
    [
        {"action": "delete_all_files", "arguments": {}},
        {"action": "lookup_http_status", "arguments": {}},
        {"action": "lookup_http_status", "arguments": {"code": 404}},
        {"action": "lookup_http_status", "arguments": {"code": "   "}},
        {"action": "list_status_class", "arguments": {"class": "2xx"}},
        {"action": "finish"},
        {"action": "finish", "arguments": {"answer": ""}},
        "not a dictionary",
    ],
)
def test_invalid_decisions(decision):
    with pytest.raises(DecisionError):
        validate_decision(decision)
