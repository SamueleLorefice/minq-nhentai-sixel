"""Shared fixtures for minq_nhentai tests."""

from pathlib import Path
from typing import Any

import pytest
import responses

from minq_nhentai.constants import API_BASE

SAMPLE_GALLERY_ID: int = 649474


@pytest.fixture
def mock_responses() -> Any:
    """Enable responses HTTP mock for the test session."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def sample_gallery_detail() -> dict[str, Any]:
    """Minimal gallery detail response from the nhentai API v2."""
    return {
        "id": SAMPLE_GALLERY_ID,
        "title": {
            "pretty": "[Test] Sample Gallery",
            "english": "Sample Gallery",
            "japanese": None,
        },
        "thumbnail": {"path": "/thumb/test.jpg", "width": 250, "height": 350},
        "num_pages": 2,
        "pages": [
            {"path": "/1.jpg", "thumbnail": "/1t.jpg", "width": 1200, "height": 800},
            {"path": "/2.jpg", "thumbnail": "/2t.jpg", "width": 1200, "height": 800},
        ],
        "tags": [
            {"id": 1, "name": "test", "type": "tag", "url": "/tag/test/", "count": 100},
            {"id": 2, "name": "english", "type": "language", "url": "/language/english/", "count": 500},
        ],
        "upload_date": 1700000000,
    }


@pytest.fixture
def mock_gallery_detail(mock_responses: Any, sample_gallery_detail: dict[str, Any]) -> str:
    """Register mock response for the gallery detail endpoint."""
    url: str = f"{API_BASE}/galleries/{SAMPLE_GALLERY_ID}"
    mock_responses.add(
        responses.GET,
        url,
        json=sample_gallery_detail,
        status=200,
    )
    return url


@pytest.fixture
def tmp_hentais_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect HENTAIS_DIR to a temporary directory for hermetic cache tests."""
    cache_dir: Path = tmp_path / "hentai_sources"
    cache_dir.mkdir(parents=True)
    value: str = str(cache_dir) + "/"
    monkeypatch.setattr("minq_nhentai.constants.HENTAIS_DIR", value)
    monkeypatch.setattr("minq_nhentai.cache.HENTAIS_DIR", value)
    return cache_dir


@pytest.fixture
def mock_cdn_servers(mock_responses: Any) -> str:
    """Register mock response for the CDN endpoint."""
    url: str = f"{API_BASE}/cdn"
    mock_responses.add(
        responses.GET,
        url,
        json={
            "image_servers": ["https://i1.nhentai.net", "https://i2.nhentai.net"],
            "thumb_servers": ["https://t1.nhentai.net", "https://t2.nhentai.net"],
        },
        status=200,
    )
    return url
