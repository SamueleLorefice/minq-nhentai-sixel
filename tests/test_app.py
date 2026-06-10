"""Tests for app.py - search building, filter validation, and command handling."""

from typing import Any
from unittest.mock import MagicMock, patch

from minq_nhentai.app import (
    _build_page_url,
    _build_search_query,
    _check_missing_filters,
    _handle_command,
    _is_duplicate,
    _print_unknown_command,
    _quote_filter_value,
    _validate_filters,
)
from minq_nhentai.models import Hentai


def _make_hentai(
    id_: int = 1,
    tags: list[str] | None = None,
    languages: list[str] | None = None,
    artists: list[str] | None = None,
) -> Hentai:
    """Helper to build a Hentai instance with minimal fixtures."""
    from minq_nhentai.scrape import _build_hentai

    detail: dict[str, Any] = {
        "id": id_,
        "title": {"pretty": f"Test {id_}"},
        "num_pages": 1,
        "tags": [],
    }
    if tags:
        for t in tags:
            detail["tags"].append({"name": t, "type": "tag", "url": f"/tag/{t}/", "count": 1})
    if languages:
        for lang in languages:
            detail["tags"].append({"name": lang, "type": "language", "url": f"/language/{lang}/", "count": 1})
    if artists:
        for a in artists:
            detail["tags"].append({"name": a, "type": "artist", "url": f"/artist/{a}/", "count": 1})
    return _build_hentai(detail)


class TestQuoteFilterValue:
    def test_replaces_double_quotes(self) -> None:
        assert _quote_filter_value('he"llo') == r"he\"llo"

    def test_noop_when_no_quotes(self) -> None:
        assert _quote_filter_value("hello") == "hello"

    def test_empty_string(self) -> None:
        assert _quote_filter_value("") == ""


class TestIsDuplicate:
    def test_returns_true_when_id_matches(self) -> None:
        a: Hentai = _make_hentai(1)
        b: Hentai = _make_hentai(1)
        assert _is_duplicate(a, [b]) is True

    def test_returns_false_when_id_differs(self) -> None:
        a: Hentai = _make_hentai(1)
        b: Hentai = _make_hentai(2)
        assert _is_duplicate(a, [b]) is False

    def test_empty_list_never_duplicate(self) -> None:
        a: Hentai = _make_hentai(1)
        assert _is_duplicate(a, []) is False

    def test_type_mismatch_not_equal(self) -> None:
        a: Hentai = _make_hentai(1)
        assert _is_duplicate(a, [a]) is True  # same type, same id


class TestCheckMissingFilters:
    def test_returns_none_when_all_match(self) -> None:
        hentai: Hentai = _make_hentai(1, tags=["vanilla"], languages=["english"], artists=["murasaki nyan"])
        result: str | None = _check_missing_filters(hentai, ["vanilla"], "english", "murasaki nyan")
        assert result is None

    def test_missing_artist(self) -> None:
        hentai = _make_hentai(1, tags=["vanilla"])
        result = _check_missing_filters(hentai, ["vanilla"], None, "nonexistent")
        assert result is not None
        assert "artist" in result

    def test_missing_tag(self) -> None:
        hentai = _make_hentai(1, languages=["english"])
        result = _check_missing_filters(hentai, ["vanilla"], "english", None)
        assert result is not None
        assert "tag" in result

    def test_missing_language(self) -> None:
        hentai = _make_hentai(1, tags=["vanilla"])
        result = _check_missing_filters(hentai, ["vanilla"], "japanese", None)
        assert result is not None
        assert "language" in result

    def test_none_filters_pass(self) -> None:
        hentai = _make_hentai(1)
        result = _check_missing_filters(hentai, [], None, None)
        assert result is None


class TestBuildSearchQuery:
    def test_all_fields(self) -> None:
        result: str = _build_search_query("maid", ["vanilla"], "english", "murasaki nyan")
        assert 'language:"english"' in result
        assert 'tag:"vanilla"' in result
        assert 'artist:"murasaki nyan"' in result
        assert result.startswith("maid")

    def test_empty_returns_empty_string(self) -> None:
        assert _build_search_query(None, [], None, None) == ""

    def test_only_tags(self) -> None:
        result = _build_search_query(None, ["vanilla", "wholesome"], None, None)
        assert result == 'tag:"vanilla" tag:"wholesome"'

    def test_only_language(self) -> None:
        result = _build_search_query(None, [], "english", None)
        assert result == 'language:"english"'

    def test_only_artist(self) -> None:
        result = _build_search_query(None, [], None, "murasaki nyan")
        assert result == 'artist:"murasaki nyan"'

    def test_whitespace_search_term_stripped(self) -> None:
        result = _build_search_query("  maid  ", [], None, None)
        assert result == "maid"

    def test_empty_search_after_strip(self) -> None:
        result = _build_search_query("   ", [], None, None)
        assert result == ""


class TestBuildPageUrl:
    def test_with_query(self) -> None:
        url: str = _build_page_url("maid")
        assert "search" in url
        assert "page={page}" in url
        assert "q=maid" in url

    def test_empty_query_uses_index(self) -> None:
        url = _build_page_url("")
        assert "nhentai.net" in url
        assert "search" not in url
        assert "page={page}" in url


class TestValidateFilters:
    @patch("minq_nhentai.app.tag_exists")
    def test_all_valid(self, mock_tag_exists: MagicMock) -> None:
        mock_tag_exists.return_value = True
        assert _validate_filters(["vanilla"], "english", "murasaki nyan") is True

    @patch("minq_nhentai.app.tag_exists")
    def test_invalid_artist(self, mock_tag_exists: MagicMock) -> None:
        def side_effect(tag_type: str, slug: str) -> bool:
            return tag_type != "artist"

        mock_tag_exists.side_effect = side_effect
        assert _validate_filters([], None, "nonexistent") is False

    @patch("minq_nhentai.app.tag_exists")
    def test_invalid_tag(self, mock_tag_exists: MagicMock) -> None:
        def side_effect(tag_type: str, slug: str) -> bool:
            return tag_type != "tag"

        mock_tag_exists.side_effect = side_effect
        assert _validate_filters(["nonexistent"], None, None) is False

    @patch("minq_nhentai.app.tag_exists")
    def test_invalid_language(self, mock_tag_exists: MagicMock) -> None:
        def side_effect(tag_type: str, slug: str) -> bool:
            return tag_type != "language"

        mock_tag_exists.side_effect = side_effect
        assert _validate_filters([], "nonexistent", None) is False

    @patch("minq_nhentai.app.tag_exists")
    def test_empty_filters_pass(self, mock_tag_exists: MagicMock) -> None:
        assert _validate_filters([], None, None) is True
        mock_tag_exists.assert_not_called()


class TestPrintUnknownCommand:
    @patch("minq_nhentai.app.warn")
    @patch("minq_nhentai.app.hint")
    @patch("minq_nhentai.app.alert")
    def test_prints_commands(self, mock_alert: MagicMock, mock_hint: MagicMock, mock_warn: MagicMock) -> None:
        cmds: list[list[str]] = [["quit", "q"], ["next", "n"]]
        _print_unknown_command(cmds)
        mock_warn.assert_called_once_with("Unknown command")
        assert mock_hint.call_count == 3  # header + 2 commands
        mock_alert.assert_called_once()


class TestHandleCommand:
    def test_quit_returns_quit(self) -> None:
        hentai: Hentai = _make_hentai(1)
        result: str = _handle_command("quit", hentai, [], ["quit"], ["read"], ["download"])
        assert result == "quit"

    @patch("minq_nhentai.models.Hentai.reading_loop")
    def test_read_returns_show(self, mock_reading_loop: MagicMock) -> None:
        hentai = _make_hentai(1)
        result = _handle_command("read", hentai, [], ["quit"], ["read"], ["download"])
        assert result == "show"
        mock_reading_loop.assert_called_once()

    @patch("minq_nhentai.models.Hentai.download_in_background")
    def test_download_returns_show(self, mock_download: MagicMock) -> None:
        hentai = _make_hentai(1)
        result = _handle_command("download", hentai, [], ["quit"], ["read"], ["download"])
        assert result == "show"
        mock_download.assert_called_once()

    def test_unknown_command_returns_empty(self) -> None:
        hentai = _make_hentai(1)
        result = _handle_command("foobar", hentai, [], ["quit"], ["read"], ["download"])
        assert result == ""
