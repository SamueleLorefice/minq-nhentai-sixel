import os
from typing import Final

from .image_backend import ImageBackend

CACHE_DIR: Final[str] = os.path.expanduser(r"~/.cache/minq_nhentai/")
SETTINGS_DIR: Final[str] = os.path.expanduser(r"~/.config/minq_nhentai/")
HENTAIS_DIR: Final[str] = CACHE_DIR + r"hentai_sources/"

NET_TOO_MANY_REQUESTS_SLEEP: Final[float] = 3
WAIT_FOR_PAGE_DOWNLOAD_SLEEP: Final[float] = 0.2

URL_INDEX: Final[str] = r"https://nhentai.net/"
URL_SEARCH: Final[str] = URL_INDEX + r"search/?q={search}"
URL_READ: Final[str] = URL_INDEX + r"g/{id}/{page}/"
URL_TAG: Final[str] = URL_INDEX + r"tag/{tag}/"
URL_LANG: Final[str] = URL_INDEX + r"language/{lang}/"
URL_ARTIST: Final[str] = URL_INDEX + r"artist/{artist}/"
URL_PAGE_POSTFIX: Final[str] = r"page={page}"

API_BASE: Final[str] = r"https://nhentai.net/api/v2"

SOUP_PARSER: Final[str] = "lxml"

THUMB_NAME: Final[str] = "thumb"
DONE_POSTFIX: Final[str] = ".done"

IMAGE_BACKEND_AUTO: Final[str] = ImageBackend.AUTO.value
IMAGE_BACKEND_SIXEL: Final[str] = ImageBackend.SIXEL.value
IMAGE_BACKEND_VIU: Final[str] = ImageBackend.VIU.value
IMAGE_BACKEND_DEFAULT: Final[str] = IMAGE_BACKEND_AUTO
