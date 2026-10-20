"""Тести детермінованого середовища кодів стану HTTP (вимога 9)."""

from agent.environment import (
    NOT_FOUND,
    lookup_http_status,
    list_status_class,
    normalize_code,
)


def test_existing_status():
    result = lookup_http_status("200")
    assert result.startswith("200:")
    assert "200 OK" in result


def test_normalization():
    assert lookup_http_status("400 Bad Request").startswith("400:")
    assert lookup_http_status("  404  ").startswith("404:")
    assert lookup_http_status("unauthorized").startswith("401:")
    assert lookup_http_status("no-content").startswith("204:")


def test_unknown_status():
    result = lookup_http_status("418")
    assert result.startswith(NOT_FOUND)
    assert "418" in result


def test_list_status_class():
    res_2xx = list_status_class("2xx")
    assert "Class 2xx" in res_2xx
    assert "200" in res_2xx
    assert "201" in res_2xx
    assert "204" in res_2xx

    res_unknown = list_status_class("9xx")
    assert res_unknown.startswith(NOT_FOUND)
