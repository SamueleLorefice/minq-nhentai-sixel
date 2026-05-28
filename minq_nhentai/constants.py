import os

CACHE_DIR = os.path.expanduser(r"~/.cache/minq_nhentai/")
SETTINGS_DIR = os.path.expanduser(r"~/.config/minq_nhentai/")
HENTAIS_DIR = CACHE_DIR + r"hentai_sources/"

NET_TOO_MANY_REQUESTS_SLEEP = 3
WAIT_FOR_PAGE_DOWNLOAD_SLEEP = 0.2

URL_PAGE_POSTFIX = r"page={page}"
URL_INDEX = r"https://nhentai.net/"
URL_SEARCH = URL_INDEX + r"search/?q={search}"
URL_READ = URL_INDEX + r"g/{id}/{page}/"
URL_TAG = URL_INDEX + r"tag/{tag}/"
URL_LANG = URL_INDEX + r"language/{lang}/"
URL_ARTIST = URL_INDEX + r"artist/{artist}/"

SOUP_PARSER = "lxml"

THUMB_NAME = "thumb"
DONE_POSTFIX = ".done"

IMAGE_BACKEND_AUTO = "auto"
IMAGE_BACKEND_SIXEL = "sixel"
IMAGE_BACKEND_VIU = "viu"
IMAGE_BACKEND_DEFAULT = IMAGE_BACKEND_AUTO

