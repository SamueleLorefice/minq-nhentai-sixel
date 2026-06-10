"""Tests for image_backend.py - backend resolution, rendering, and detection."""

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from minq_nhentai.image_backend import (
    IMAGE_BACKEND_AUTO,
    IMAGE_BACKEND_SIXEL,
    IMAGE_BACKEND_VIU,
    ImageBackend,
    _env_truthy,
    _has_bin,
    _is_webp,
    _resolve_image_backend,
    configure_image_backend,
    render_image,
)


class TestImageBackendEnum:
    def test_values(self) -> None:
        assert ImageBackend.AUTO.value == "auto"
        assert ImageBackend.SIXEL.value == "sixel"
        assert ImageBackend.VIU.value == "viu"


class TestIsWebp:
    def test_detects_webp_header(self, tmp_path: Any) -> None:
        path = tmp_path / "test.webp"
        path.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
        assert _is_webp(str(path)) is True

    def test_rejects_png(self, tmp_path: Any) -> None:
        path = tmp_path / "test.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert _is_webp(str(path)) is False

    def test_rejects_missing_file(self) -> None:
        assert _is_webp("/nonexistent/file.webp") is False

    def test_short_file_not_webp(self, tmp_path: Any) -> None:
        path = tmp_path / "short.bin"
        path.write_bytes(b"RIFF")
        assert _is_webp(str(path)) is False


class TestEnvTruthy:
    def test_returns_true_for_1(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "1")
        assert _env_truthy("TEST_VAR") is True

    def test_returns_true_for_true(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "true")
        assert _env_truthy("TEST_VAR") is True

    def test_returns_true_for_yes(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "yes")
        assert _env_truthy("TEST_VAR") is True

    def test_returns_true_for_on(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "on")
        assert _env_truthy("TEST_VAR") is True

    def test_returns_false_for_0(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "0")
        assert _env_truthy("TEST_VAR") is False

    def test_returns_false_for_false(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "false")
        assert _env_truthy("TEST_VAR") is False

    def test_returns_false_when_unset(self) -> None:
        assert _env_truthy("NONEXISTENT_VAR") is False

    def test_is_case_insensitive(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "True")
        assert _env_truthy("TEST_VAR") is True

    def test_strips_whitespace(self, monkeypatch: Any) -> None:
        monkeypatch.setenv("TEST_VAR", "  1  ")
        assert _env_truthy("TEST_VAR") is True


class TestHasBin:
    @patch("minq_nhentai.image_backend.shutil.which")
    def test_returns_true_when_found(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/viu"
        assert _has_bin("viu") is True

    @patch("minq_nhentai.image_backend.shutil.which")
    def test_returns_false_when_not_found(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        assert _has_bin("viu") is False


class TestTerminalSupportsSixel:
    @patch("minq_nhentai.image_backend._env_truthy")
    def test_forced_off(self, mock_env_truthy: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "MINQ_NHENTAI_NO_SIXEL"

        mock_env_truthy.side_effect = side_effect
        from minq_nhentai.image_backend import terminal_supports_sixel

        assert terminal_supports_sixel() is False

    @patch("minq_nhentai.image_backend._env_truthy")
    def test_forced_on(self, mock_env_truthy: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "MINQ_NHENTAI_SIXEL"

        mock_env_truthy.side_effect = side_effect
        from minq_nhentai.image_backend import terminal_supports_sixel

        assert terminal_supports_sixel() is True


class TestResolveImageBackend:
    @patch("minq_nhentai.image_backend._has_bin")
    def test_viu_ok(self, mock_has_bin: MagicMock) -> None:
        mock_has_bin.return_value = True
        assert _resolve_image_backend(IMAGE_BACKEND_VIU) == "viu"

    @patch("minq_nhentai.image_backend._has_bin")
    def test_viu_missing(self, mock_has_bin: MagicMock) -> None:
        mock_has_bin.return_value = False
        with pytest.raises(RuntimeError, match="not found"):
            _resolve_image_backend(IMAGE_BACKEND_VIU)

    @patch("minq_nhentai.image_backend._has_bin")
    @patch("minq_nhentai.image_backend.terminal_supports_sixel")
    def test_sixel_ok(self, mock_term: MagicMock, mock_has_bin: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "img2sixel"

        mock_has_bin.side_effect = side_effect
        mock_term.return_value = True
        assert _resolve_image_backend(IMAGE_BACKEND_SIXEL) == "sixel"

    @patch("minq_nhentai.image_backend._has_bin")
    def test_sixel_no_bin(self, mock_has_bin: MagicMock) -> None:
        mock_has_bin.return_value = False
        with pytest.raises(RuntimeError, match="not found"):
            _resolve_image_backend(IMAGE_BACKEND_SIXEL)

    @patch("minq_nhentai.image_backend._has_bin")
    @patch("minq_nhentai.image_backend.terminal_supports_sixel")
    def test_sixel_no_term(self, mock_term: MagicMock, mock_has_bin: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "img2sixel"

        mock_has_bin.side_effect = side_effect
        mock_term.return_value = False
        with pytest.raises(RuntimeError, match="terminal"):
            _resolve_image_backend(IMAGE_BACKEND_SIXEL)

    @patch("minq_nhentai.image_backend._has_bin")
    @patch("minq_nhentai.image_backend.terminal_supports_sixel")
    def test_auto_sixel(self, mock_term: MagicMock, mock_has_bin: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "img2sixel"

        mock_has_bin.side_effect = side_effect
        mock_term.return_value = True
        assert _resolve_image_backend(IMAGE_BACKEND_AUTO) == "sixel"

    @patch("minq_nhentai.image_backend._has_bin")
    @patch("minq_nhentai.image_backend.terminal_supports_sixel")
    def test_auto_viu_fallback(self, mock_term: MagicMock, mock_has_bin: MagicMock) -> None:
        def side_effect(name: str) -> bool:
            return name == "viu"

        mock_has_bin.side_effect = side_effect
        mock_term.return_value = False
        assert _resolve_image_backend(IMAGE_BACKEND_AUTO) == "viu"

    @patch("minq_nhentai.image_backend._has_bin")
    def test_auto_none(self, mock_has_bin: MagicMock) -> None:
        mock_has_bin.return_value = False
        with pytest.raises(RuntimeError, match="No supported"):
            _resolve_image_backend(IMAGE_BACKEND_AUTO)

    def test_unknown_backend(self) -> None:
        with pytest.raises(RuntimeError, match="Unknown"):
            _resolve_image_backend("foobar")


class TestConfigureImageBackend:
    @patch("minq_nhentai.image_backend.print")
    @patch("minq_nhentai.image_backend._resolve_image_backend")
    def test_updates_state(self, mock_resolve: MagicMock, mock_print: MagicMock) -> None:
        mock_resolve.return_value = "sixel"
        configure_image_backend("sixel")
        from minq_nhentai.image_backend import _state

        assert _state.requested == "sixel"
        assert _state.resolved == "sixel"
        assert _state.fallback_done is False


class TestRenderImage:
    def test_auto_fallback_to_viu(self) -> None:
        import minq_nhentai.image_backend as ib

        ib._state.requested = "auto"
        ib._state.resolved = "sixel"
        ib._state.fallback_done = False

        with (
            patch("minq_nhentai.image_backend._render_with_backend") as mock_render,
            patch("minq_nhentai.image_backend._has_bin", return_value=True),
        ):
            mock_render.side_effect = [
                subprocess.CalledProcessError(1, "img2sixel"),
                None,
            ]
            render_image("/fake/path")

        assert ib._state.resolved == "viu"
        assert ib._state.fallback_done is True

    def test_configure_if_not_resolved(self) -> None:
        import minq_nhentai.image_backend as ib

        ib._state.resolved = None
        ib._state.requested = "auto"

        with (
            patch("minq_nhentai.image_backend._resolve_image_backend", return_value="viu"),
            patch("minq_nhentai.image_backend._render_with_backend") as mock_render,
        ):
            render_image("/fake/path")
            mock_render.assert_called_once_with("/fake/path", "viu")


class TestRenderWithBackend:
    @patch("minq_nhentai.image_backend.subprocess.run")
    def test_sixel_command(self, mock_run: MagicMock) -> None:
        from minq_nhentai.image_backend import _render_with_backend

        _render_with_backend("/test/path", IMAGE_BACKEND_SIXEL)
        mock_run.assert_called_once_with(["img2sixel", "/test/path"], check=True, capture_output=False)

    @patch("minq_nhentai.image_backend.subprocess.run")
    def test_viu_command(self, mock_run: MagicMock) -> None:
        from minq_nhentai.image_backend import _render_with_backend

        _render_with_backend("/test/path", IMAGE_BACKEND_VIU)
        mock_run.assert_called_once_with(["viu", "/test/path"], check=True, capture_output=False)

    def test_unknown_backend(self) -> None:
        from minq_nhentai.image_backend import _render_with_backend

        with pytest.raises(RuntimeError, match="Unsupported"):
            _render_with_backend("/test/path", "foobar")

    @patch("minq_nhentai.image_backend.subprocess.run")
    @patch("minq_nhentai.image_backend._is_webp")
    @patch("minq_nhentai.image_backend._render_with_webp_transcode_fallback")
    def test_webp_fallback(
        self,
        mock_fallback: MagicMock,
        mock_is_webp: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from minq_nhentai.image_backend import _render_with_backend

        mock_run.side_effect = subprocess.CalledProcessError(1, "img2sixel")
        mock_is_webp.return_value = True

        _render_with_backend("/test.webp", IMAGE_BACKEND_SIXEL)
        mock_fallback.assert_called_once_with("/test.webp", IMAGE_BACKEND_SIXEL)
