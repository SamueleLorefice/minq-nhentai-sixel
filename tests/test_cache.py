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
