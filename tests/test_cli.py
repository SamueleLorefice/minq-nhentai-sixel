"""Tests for cli.py - argument parsing and dispatching."""

from unittest.mock import MagicMock, patch

import pytest

from minq_nhentai.constants import IMAGE_BACKEND_AUTO, IMAGE_BACKEND_DEFAULT, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU


class TestMain:
    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "12345"])
    def test_gallery_id(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_configure.assert_called_once_with(IMAGE_BACKEND_AUTO)
        mock_interactive.assert_called_once_with(
            search_term=None,
            required_tags=[],
            required_language=None,
            required_artist=None,
            gallery_id=12345,
        )

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--search", "maid"])
    def test_search(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_interactive.assert_called_once_with(
            search_term="maid",
            required_tags=[],
            required_language=None,
            required_artist=None,
            gallery_id=None,
        )

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--tags", "vanilla", "wholesome"])
    def test_tags(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_interactive.assert_called_once_with(
            search_term=None,
            required_tags=["vanilla", "wholesome"],
            required_language=None,
            required_artist=None,
            gallery_id=None,
        )

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--language", "english"])
    def test_language(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_interactive.assert_called_once_with(
            search_term=None,
            required_tags=[],
            required_language="english",
            required_artist=None,
            gallery_id=None,
        )

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--artist", "murasaki nyan"])
    def test_artist(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_interactive.assert_called_once_with(
            search_term=None,
            required_tags=[],
            required_language=None,
            required_artist="murasaki nyan",
            gallery_id=None,
        )

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--sixel", "12345"])
    def test_sixel_flag(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_configure.assert_called_once_with(IMAGE_BACKEND_SIXEL)

    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "--viu", "12345"])
    def test_viu_flag(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_configure.assert_called_once_with(IMAGE_BACKEND_VIU)

    @patch("minq_nhentai.cli.print")
    @patch("sys.argv", ["prog", "--sixel", "--viu"])
    def test_sixel_and_viu_conflict(self, mock_print: MagicMock) -> None:
        from minq_nhentai.cli import main

        with pytest.raises(SystemExit):
            main()
        mock_print.assert_called_once_with("Cannot use both --sixel and --viu at the same time")

    @patch("minq_nhentai.cli.print")
    @patch("sys.argv", ["prog", ""])
    def test_empty_gallery(self, mock_print: MagicMock) -> None:
        from minq_nhentai.cli import main

        with pytest.raises(SystemExit):
            main()
        mock_print.assert_called_once_with("Gallery code cannot be empty")

    @patch("minq_nhentai.cli.print")
    @patch("sys.argv", ["prog", "abc"])
    def test_non_numeric_gallery(self, mock_print: MagicMock) -> None:
        from minq_nhentai.cli import main

        with pytest.raises(SystemExit):
            main()
        mock_print.assert_called_once_with("Gallery code must be numeric: abc")

    @patch("minq_nhentai.cli.print")
    @patch("minq_nhentai.cli.sys.exit", side_effect=SystemExit(1))
    @patch("minq_nhentai.cli.configure_image_backend")
    @patch("minq_nhentai.cli.interactive_hentai_enjoyment")
    @patch("sys.argv", ["prog", "12345"])
    def test_default_image_backend(
        self,
        mock_interactive: MagicMock,
        mock_configure: MagicMock,
        mock_exit: MagicMock,
        mock_print: MagicMock,
    ) -> None:
        from minq_nhentai.cli import main

        main()
        mock_configure.assert_called_once_with(IMAGE_BACKEND_DEFAULT)
        mock_exit.assert_not_called()
