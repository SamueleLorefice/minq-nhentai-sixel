"""Tests for api.py - CDN server resolution and gallery detail."""

from typing import Any

import pytest
import responses

from minq_nhentai.api import build_cdn_url, get_cdn_servers, get_gallery_detail, iter_cdn_urls
from minq_nhentai.constants import API_BASE
from minq_nhentai.errors import ExceptionNetUnknown


class TestGetCdnServers:
    @responses.activate
    def test_returns_servers(self) -> None:
        responses.get(
            f"{API_BASE}/cdn",
            json={
                "image_servers": ["https://i1.nhentai.net/", "https://i2.nhentai.net/"],
                "thumb_servers": ["https://t1.nhentai.net/", "https://t2.nhentai.net/"],
            },
            status=200,
        )
        servers: dict[str, list[str]] = get_cdn_servers(refresh=True, silent=True)
        assert "image" in servers
        assert "thumb" in servers
        assert servers["image"] == ["https://i1.nhentai.net", "https://i2.nhentai.net"]
        assert servers["thumb"] == ["https://t1.nhentai.net", "https://t2.nhentai.net"]

    @responses.activate
    def test_raises_on_malformed_response(self) -> None:
        responses.get(f"{API_BASE}/cdn", json={}, status=200)
        with pytest.raises(ExceptionNetUnknown, match="Malformed CDN"):
            get_cdn_servers(refresh=True, silent=True)


class TestIterCdnUrls:
    @responses.activate
    def test_returns_ordered_urls(self) -> None:
        responses.get(
            f"{API_BASE}/cdn",
            json={
                "image_servers": ["https://i1.nhentai.net", "https://i2.nhentai.net"],
                "thumb_servers": ["https://t1.nhentai.net", "https://t2.nhentai.net"],
            },
            status=200,
        )
        urls: list[str] = iter_cdn_urls("/test/path.jpg", "image")
        assert len(urls) == 2
        assert all(url.startswith("https://") for url in urls)


class TestBuildCdnUrl:
    @responses.activate
    def test_returns_first_url(self) -> None:
        responses.get(
            f"{API_BASE}/cdn",
            json={
                "image_servers": ["https://i1.nhentai.net", "https://i2.nhentai.net"],
                "thumb_servers": ["https://t1.nhentai.net", "https://t2.nhentai.net"],
            },
            status=200,
        )
        url: str | None = build_cdn_url("/test/path.jpg", "image")
        assert url is not None
        assert "/test/path.jpg" in url


class TestGetGalleryDetail:
    @responses.activate
    def test_returns_gallery_data(self) -> None:
        mock_data: dict[str, Any] = {
            "id": 12345,
            "title": {"pretty": "Test"},
            "num_pages": 1,
        }
        responses.get(f"{API_BASE}/galleries/12345", json=mock_data, status=200)
        detail: Any = get_gallery_detail(12345, silent=True)
        assert detail["id"] == 12345
        assert detail["title"]["pretty"] == "Test"
