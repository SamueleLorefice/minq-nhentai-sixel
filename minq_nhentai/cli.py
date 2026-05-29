import argparse
import sys

from .app import interactive_hentai_enjoyment
from .constants import IMAGE_BACKEND_AUTO, IMAGE_BACKEND_DEFAULT, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU
from .image_backend import configure_image_backend
from .ui import print


def main():
    parser = argparse.ArgumentParser(description="Command line port of nhentai")
    parser.add_argument(
        "gallery",
        nargs="?",
        help="Direct nhentai gallery code to open, e.g. 649474",
    )
    parser.add_argument("--search", help="String to search for")
    parser.add_argument("--tags", nargs="+", help="Tags required for the hentai", default=[])
    parser.add_argument("--language", help="Language required for the hentai")
    parser.add_argument("--artist", help="Artist required for the hentai")
    parser.add_argument(
        "--image-backend",
        choices=[IMAGE_BACKEND_AUTO, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU],
        default=IMAGE_BACKEND_DEFAULT,
        help="Image renderer backend to use",
    )
    parser.add_argument("--sixel", action="store_true", help="Force sixel image backend")
    parser.add_argument("--viu", action="store_true", help="Force viu image backend")
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

