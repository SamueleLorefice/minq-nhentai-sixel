"""Tests for scrape.py - model building and URL parsing."""

from typing import Any

import responses

from minq_nhentai.constants import API_BASE
from minq_nhentai.models import Hentai
from minq_nhentai.scrape import _build_hentai, _parse_url_page, tag_exists


class TestBuildHentai:
    def test_builds_from_minimal_detail(self) -> None:
        detail: dict[str, Any] = {
            "id": 1,
            "title": {"pretty": "Test"},
            "num_pages": 1,
            "tags": [],
        }
        hentai: Hentai = _build_hentai(detail)
        assert hentai.id_ == 1
        assert hentai.title == "Test"
        assert hentai.pages == 1

    def test_parses_tag_list(self) -> None:
        detail: dict[str, Any] = {
            "id": 2,
            "title": {"english": "Multi Tag"},
            "num_pages": 1,
            "tags": [
                {"name": "vanilla", "type": "tag", "url": "/tag/vanilla/", "count": 100},
                {"name": "english", "type": "language", "url": "/language/english/", "count": 500},
                {"name": "manga", "type": "category", "url": "/category/manga/", "count": 1000},
                {"name": "artist1", "type": "artist", "url": "/artist/artist1/", "count": 10},
                {"name": "naruto", "type": "parody", "url": "/parody/naruto/", "count": 50},
                {"name": "char1", "type": "character", "url": "/character/char1/", "count": 20},
                {"name": "group1", "type": "group", "url": "/group/group1/", "count": 5},
            ],
        }
        hentai: Hentai = _build_hentai(detail)
        assert len(hentai.tags) == 1
        assert len(hentai.languages) == 1
        assert len(hentai.categories) == 1
        assert len(hentai.artists) == 1
        assert len(hentai.parodies) == 1
        assert len(hentai.characters) == 1
        assert len(hentai.groups) == 1

    def test_falls_back_to_id_when_no_title(self) -> None:
        detail: dict[str, Any] = {"id": 999, "num_pages": 1, "tags": []}
        hentai: Hentai = _build_hentai(detail)
        assert hentai.title == "999"

    def test_handles_missing_pages_field(self) -> None:
        detail: dict[str, Any] = {"id": 3, "title": {"pretty": "No Pages"}, "tags": []}
        hentai: Hentai = _build_hentai(detail)
        assert hentai.pages == 0


class TestParseUrlPage:
    def test_homepage(self) -> None:
        api_path, params = _parse_url_page("https://nhentai.net/?page={page}")
        assert api_path == "/galleries"
        assert params == {}

    def test_search(self) -> None:
        api_path, params = _parse_url_page("https://nhentai.net/search/?q=test&page={page}")
        assert api_path == "/search"
        assert params == {"query": "test"}

    def test_homepage_short(self) -> None:
        api_path, params = _parse_url_page("?page={page}")
        assert api_path == "/galleries"
        assert params == {}


class TestTagExists:
    @responses.activate
    def test_returns_true_when_tag_found(self) -> None:
        responses.get(
            f"{API_BASE}/tags/tag/vanilla",
            json={"id": 1, "name": "vanilla", "count": 100},
            status=200,
        )
        assert tag_exists("tag", "vanilla") is True

    @responses.activate
    def test_returns_false_when_tag_not_found(self) -> None:
        responses.get(f"{API_BASE}/tags/tag/nonexistent", status=404)
        assert tag_exists("tag", "nonexistent") is False
