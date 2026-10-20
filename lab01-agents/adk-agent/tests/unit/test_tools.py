"""Unit tests for ADK agent tools."""

from app.environment import NOT_FOUND, list_status_class, lookup_http_status


def test_lookup_http_status_valid():
    res = lookup_http_status("400")
    assert res.startswith("400:")
    assert "Bad Request" in res


def test_lookup_http_status_not_found():
    res = lookup_http_status("499")
    assert res.startswith(NOT_FOUND)


def test_list_status_class():
    res_4xx = list_status_class("4xx")
    assert "400" in res_4xx
    assert "401" in res_4xx
    assert "403" in res_4xx
    assert "404" in res_4xx
    assert "409" in res_4xx
