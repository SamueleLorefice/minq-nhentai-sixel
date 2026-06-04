import argparse
import sys

from .app import interactive_hentai_enjoyment
from .constants import IMAGE_BACKEND_AUTO, IMAGE_BACKEND_DEFAULT, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU
from .image_backend import configure_image_backend
from .ui import print


def main():
    parser = argparse.ArgumentParser(
        description="Browse nhentai galleries from your terminal.",
        epilog=(
            "Examples:\n"
            "  python -m minq_nhentai 649474\n"
            "  python -m minq_nhentai --search \"maid\"\n"
            "  python -m minq_nhentai --tags vanilla wholesome --language english\n"
            "  python -m minq_nhentai --artist \"murasaki nyan\" --image-backend sixel"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "gallery",
        nargs="?",
        metavar="GALLERY_ID",
        help="Open one gallery directly by numeric ID (for example: 649474)",
    )
    parser.add_argument(
        "--search",
        metavar="QUERY",
        help="Free-text search query (for example: \"school uniform\")",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        metavar="TAG",
        help="Require one or more tags (space-separated), for example: --tags vanilla romance",
        default=[],
    )
    parser.add_argument(
        "--language",
        metavar="LANGUAGE",
        help="Require a language tag (for example: english, japanese)",
    )
    parser.add_argument(
        "--artist",
        metavar="ARTIST",
        help="Require an artist tag (for example: \"murasaki nyan\")",
    )
    parser.add_argument(
        "--image-backend",
        choices=[IMAGE_BACKEND_AUTO, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU],
        default=IMAGE_BACKEND_DEFAULT,
        help="Image renderer backend (choices: auto, sixel, viu)",
    )
    parser.add_argument(
        "--sixel",
        action="store_true",
        help="Shortcut for --image-backend sixel",
    )
    parser.add_argument(
        "--viu",
        action="store_true",
        help="Shortcut for --image-backend viu",
    )
    args = parser.parse_args()

    if args.sixel and args.viu:
        print("Cannot use both --sixel and --viu at the same time")
        sys.exit(1)

    image_backend = args.image_backend
    if args.sixel:
        image_backend = IMAGE_BACKEND_SIXEL
    elif args.viu:
        image_backend = IMAGE_BACKEND_VIU

    try:
        configure_image_backend(image_backend)
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)

    gallery_id = None
    if args.gallery is not None:
        gallery_text = args.gallery.strip()
        if gallery_text == "":
            print("Gallery code cannot be empty")
            sys.exit(1)
        if not gallery_text.isdigit():
            print(f"Gallery code must be numeric: {args.gallery}")
            sys.exit(1)
        gallery_id = int(gallery_text)

    call_args = [args.search, args.tags, args.language, args.artist, gallery_id]
    interactive_hentai_enjoyment(*call_args)

