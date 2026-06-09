"""Tests for image_backend.py - WebP detection and sixel support detection."""

from minq_nhentai.image_backend import ImageBackend, _is_webp


class TestImageBackendEnum:
    def test_values(self) -> None:
        assert ImageBackend.AUTO.value == "auto"
        assert ImageBackend.SIXEL.value == "sixel"
        assert ImageBackend.VIU.value == "viu"


class TestIsWebp:
    def test_detects_webp_header(self, tmp_path) -> None:
        path = tmp_path / "test.webp"
        # Minimal WebP file header
        path.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
        assert _is_webp(str(path)) is True

    def test_rejects_png(self, tmp_path) -> None:
        path = tmp_path / "test.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert _is_webp(str(path)) is False

    def test_rejects_missing_file(self) -> None:
        assert _is_webp("/nonexistent/file.webp") is False

    def test_short_file_not_webp(self, tmp_path) -> None:
        path = tmp_path / "short.bin"
        path.write_bytes(b"RIFF")
        assert _is_webp(str(path)) is False
