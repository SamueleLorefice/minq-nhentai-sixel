"""Tests for net.py - HTTP retry and error handling."""

import responses

from minq_nhentai.errors import ExceptionNetPageNotFound, ExceptionNetUnknown
from minq_nhentai.net import does_page_exist, receive, receive_raw


@responses.activate
def test_receive_raw_returns_bytes() -> None:
    responses.get("https://example.com/test", body=b"hello world", status=200)
    result: bytes = receive_raw("https://example.com/test", silent=True)
    assert result == b"hello world"


@responses.activate
def test_receive_returns_decoded_string() -> None:
    responses.get("https://example.com/test", body=b"hello world", status=200)
    result: str = receive("https://example.com/test", silent=True)
    assert result == "hello world"


@responses.activate
def test_receive_raw_404_raises_page_not_found() -> None:
    responses.get("https://example.com/404", status=404)
    try:
        receive_raw("https://example.com/404", silent=True)
        raise AssertionError("Expected ExceptionNetPageNotFound")
    except ExceptionNetPageNotFound:
        pass


@responses.activate
def test_receive_raw_500_raises_unknown() -> None:
    responses.get("https://example.com/500", status=500)
    try:
        receive_raw("https://example.com/500", silent=True)
        raise AssertionError("Expected ExceptionNetUnknown")
    except ExceptionNetUnknown:
        pass


@responses.activate
def test_does_page_exist_returns_true_for_200() -> None:
    responses.get("https://example.com/exists", status=200)
    assert does_page_exist("https://example.com/exists") is True


@responses.activate
def test_does_page_exist_returns_false_for_404() -> None:
    responses.get("https://example.com/missing", status=404)
    assert does_page_exist("https://example.com/missing") is False


@responses.activate
def test_receive_raw_retry_on_429_then_success() -> None:
    responses.get("https://example.com/ratelimit", status=429)
    responses.get("https://example.com/ratelimit", body=b"ok", status=200)
    result: bytes = receive_raw("https://example.com/ratelimit", silent=True)
    assert result == b"ok"
    # Verify both calls were made (first 429, then retry)
    assert len(responses.calls) == 2
