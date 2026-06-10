"""Tests for ui.py - print helpers, temp line handling, and input."""

from unittest.mock import MagicMock, patch

from minq_nhentai.ui import (
    _clear_tmp_line_if_any,
    _print_tmp_last_count,
    _print_tmp_last_len,
    _print_tmp_last_msg,
    alert,
    error,
    hint,
    info,
    input,
    print_tmp,
    success,
    warn,
)


class TestClearTmpLine:
    def test_clears_when_len_positive(self) -> None:
        import minq_nhentai.ui as ui_mod

        old_len = _print_tmp_last_len
        ui_mod._print_tmp_last_len = 10
        with patch("minq_nhentai.ui.console.print") as mock_print:
            _clear_tmp_line_if_any()
            mock_print.assert_called_once_with(" " * 10, end="\r", markup=False)
        ui_mod._print_tmp_last_len = old_len

    def test_noop_when_len_zero(self) -> None:
        import minq_nhentai.ui as ui_mod

        old_len = _print_tmp_last_len
        ui_mod._print_tmp_last_len = 0
        with patch("minq_nhentai.ui.console.print") as mock_print:
            _clear_tmp_line_if_any()
            mock_print.assert_not_called()
        ui_mod._print_tmp_last_len = old_len


class TestPrintTmp:
    def test_dedup_counting(self) -> None:
        import minq_nhentai.ui as ui_mod

        old_msg = _print_tmp_last_msg
        old_len = _print_tmp_last_len
        old_count = _print_tmp_last_count
        ui_mod._print_tmp_last_msg = ""
        ui_mod._print_tmp_last_len = 0
        ui_mod._print_tmp_last_count = 1

        with patch("minq_nhentai.ui.console.print") as mock_print:
            print_tmp("hello")
            assert ui_mod._print_tmp_last_msg == "hello"

            print_tmp("hello")
            assert ui_mod._print_tmp_last_count == 2
            assert mock_print.call_count >= 2

        ui_mod._print_tmp_last_msg = old_msg
        ui_mod._print_tmp_last_len = old_len
        ui_mod._print_tmp_last_count = old_count

    def test_different_message_resets_count(self) -> None:
        import minq_nhentai.ui as ui_mod

        old_msg = _print_tmp_last_msg
        old_len = _print_tmp_last_len
        old_count = _print_tmp_last_count
        ui_mod._print_tmp_last_msg = ""
        ui_mod._print_tmp_last_len = 0
        ui_mod._print_tmp_last_count = 1

        with patch("minq_nhentai.ui.console.print"):
            print_tmp("first")
            print_tmp("second")

        ui_mod._print_tmp_last_msg = old_msg
        ui_mod._print_tmp_last_len = old_len
        ui_mod._print_tmp_last_count = old_count


class TestInput:
    @patch("minq_nhentai.ui.Prompt.ask")
    def test_returns_value(self, mock_ask: MagicMock) -> None:
        mock_ask.return_value = "test input"
        result: str | int = input("prompt>", -1)
        assert result == "test input"

    @patch("minq_nhentai.ui.Prompt.ask")
    def test_keyboard_interrupt_returns_default(self, mock_ask: MagicMock) -> None:
        mock_ask.side_effect = KeyboardInterrupt()
        result: str | int = input("prompt>", 42)
        assert result == 42


class TestAlert:
    @patch("minq_nhentai.ui.print")
    @patch("minq_nhentai.ui.input")
    def test_alert_calls_print_and_input(self, mock_input: MagicMock, mock_print: MagicMock) -> None:
        alert("test message")
        mock_print.assert_called_once_with("test message")
        mock_input.assert_called_once()


class TestStyledOutput:
    @patch("minq_nhentai.ui.print")
    def test_error_format(self, mock_print: MagicMock) -> None:
        error("something broke")
        args, _ = mock_print.call_args
        assert "✘" in args[0]
        assert "something broke" in args[0]

    @patch("minq_nhentai.ui.print")
    def test_warn_format(self, mock_print: MagicMock) -> None:
        warn("caution")
        args, _ = mock_print.call_args
        assert "⚠" in args[0]
        assert "caution" in args[0]

    @patch("minq_nhentai.ui.print")
    def test_success_format(self, mock_print: MagicMock) -> None:
        success("all good")
        args, _ = mock_print.call_args
        assert "✔" in args[0]
        assert "all good" in args[0]

    @patch("minq_nhentai.ui.print")
    def test_info_format(self, mock_print: MagicMock) -> None:
        info("for your info")
        args, _ = mock_print.call_args
        assert "ℹ" in args[0]
        assert "for your info" in args[0]

    @patch("minq_nhentai.ui.print")
    def test_hint_format(self, mock_print: MagicMock) -> None:
        hint("suggestion")
        args, _ = mock_print.call_args
        assert "dim italic" in args[0]
        assert "suggestion" in args[0]
