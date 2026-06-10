"""Tests for cache.py - HentaiCache path and cache state."""

from pathlib import Path
from unittest.mock import patch

import pytest

from minq_nhentai.cache import HentaiCache
from minq_nhentai.constants import DONE_POSTFIX


class TestHentaiCache:
    def test_image_path_returns_expected_path(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(12345)
        path: str = cache.image_path("thumb")
        assert "12345" in path
        assert path.endswith("thumb")

    def test_image_not_cached_initially(self, tmp_hentais_dir: Path) -> None:
        cache = HentaiCache(99999)
        assert cache.image_cached("test_img") is False

    def test_image_set_then_cached(self, tmp_hentais_dir: Path) -> None:
        cache = HentaiCache(99999)
        assert cache.image_cached("test_img") is False
        cache.image_set_cached("test_img")
        done_path = Path(cache.image_path("test_img") + DONE_POSTFIX)
        assert done_path.exists()
        assert cache.image_cached("test_img") is True

    def test_image_unset_removes_cache_flag(self, tmp_hentais_dir: Path) -> None:
        cache = HentaiCache(88888)
        assert cache.image_cached("test_img") is False
        cache.image_set_cached("test_img")
        assert cache.image_cached("test_img") is True
        cache.image_unset_cached("test_img")
        assert cache.image_cached("test_img") is False

    def test_cache_isolation_by_id(self, tmp_hentais_dir: Path) -> None:
        cache_a: HentaiCache = HentaiCache(1)
        cache_b: HentaiCache = HentaiCache(2)
        assert cache_a.image_path("img") != cache_b.image_path("img")

    def test_image_print_raises_on_uncached(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(77777)
        with (
            pytest.raises(RuntimeError, match="not cached"),
            patch("minq_nhentai.cache.render_image") as mock_render,
        ):
            cache.image_print("missing_img")
        mock_render.assert_not_called()

    def test_image_cache_downloads_and_sets_flag(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(55555)
        with patch("minq_nhentai.cache.receive_raw", return_value=b"fake_image_data"):
            cache.image_cache("https://example.com/img.jpg", "test_img")
        assert cache.image_cached("test_img") is True
        cached_path: Path = Path(cache.image_path("test_img"))
        assert cached_path.read_bytes() == b"fake_image_data"

    def test_image_cache_any_first_url_succeeds(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(44444)
        with patch("minq_nhentai.cache.receive_raw", return_value=b"data"):
            cache.image_cache_any(
                ["https://example.com/1.jpg", "https://example.com/2.jpg"],
                "multi_img",
            )
        assert cache.image_cached("multi_img") is True

    def test_image_cache_any_all_fail(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(33333)
        with (
            patch("minq_nhentai.cache.receive_raw", side_effect=ConnectionError("no network")),
            pytest.raises(ConnectionError, match="no network"),
        ):
            cache.image_cache_any(
                ["https://example.com/1.jpg", "https://example.com/2.jpg"],
                "fail_img",
            )

    def test_image_cache_any_empty_urls(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(22222)
        with pytest.raises(RuntimeError, match="No download URLs"):
            cache.image_cache_any([], "empty_img")

    def test_image_print_cache_already_cached(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(11111)
        cache.image_set_cached("cached_img")
        with (
            patch("minq_nhentai.cache.receive_raw") as mock_receive,
            patch("minq_nhentai.cache.render_image") as mock_render,
        ):
            cache.image_print_cache("https://example.com/img.jpg", "cached_img")
        mock_receive.assert_not_called()
        mock_render.assert_called_once()

    def test_image_print_cache_not_cached(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(66666)
        with (
            patch("minq_nhentai.cache.receive_raw", return_value=b"data"),
            patch("minq_nhentai.cache.render_image") as mock_render,
        ):
            cache.image_print_cache("https://example.com/img.jpg", "new_img")
        assert cache.image_cached("new_img") is True
        mock_render.assert_called_once()

    def test_image_print_cache_any_already_cached(self, tmp_hentais_dir: Path) -> None:
        cache: HentaiCache = HentaiCache(77777)
        cache.image_set_cached("any_cached")
        with (
            patch("minq_nhentai.cache.receive_raw") as mock_receive,
            patch("minq_nhentai.cache.render_image") as mock_render,
        ):
            cache.image_print_cache_any(
                ["https://example.com/1.jpg", "https://example.com/2.jpg"],
                "any_cached",
            )
        mock_receive.assert_not_called()
        mock_render.assert_called_once()
