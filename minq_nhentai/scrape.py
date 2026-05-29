"""
nhentai API v2

Data fetched from the official REST API.

Rate limits (anonymous / no API key):
  GET /api/v2/galleries              – 15 req/min per IP
  GET /api/v2/galleries/tagged       – 15 req/min per IP
  GET /api/v2/search                 – 10 req/min per IP
  GET /api/v2/galleries/{id}         – 20 req/min per IP
  GET /api/v2/tags/{type}/{slug}     – 15 req/min per IP

All 429 responses carry a Retry-After header; we honor it.
"""

import json
import re
import urllib.parse

from .constants import API_BASE, CDN_BASE, NET_TOO_MANY_REQUESTS_SLEEP, URL_INDEX
from .errors import Exception_net_page_not_found
from .models import Artist, Category, Character, Group, Hentai, Language, Parody, Tag
from .net import receive_raw
from .ui import print_tmp

def _api_get(path, params=None, silent=False):
    """Make a GET request to the nhentai API v2 and return the parsed JSON response as a dict or list."""
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )
    raw = receive_raw(url, silent=silent)
    return json.loads(raw)

def _cdn_url(path):
    """Build a full CDN URL from a relative path (e.g. 'galleries/123/thumb.webp')."""
    if not path:
        return None
    return f"{CDN_BASE}/{path}"

_tag_cache: dict = {}

def _resolve_tag(tag_type, slug):
    """
    Return API TagResponse dict for (tag_type, slug).
    Raises Exception_net_page_not_found if the tag does not exist.
    tag_type is one of: tag, language, artist, group, parody, character, category
    """
    key = (tag_type, slug)
    if key in _tag_cache:
        return _tag_cache[key]
    data = _api_get(f"/tags/{tag_type}/{slug}")
    _tag_cache[key] = data
    return data


def tag_exists(tag_type, slug):
    """Return True when the tag exists in the API, False otherwise."""
    try:
        _resolve_tag(tag_type, slug)
        return True
    except Exception:
        return False

def _build_hentai(detail):
    """Convert a full GalleryDetailResponse dict into a Hentai model object."""
    id_ = detail["id"]

    title_obj = detail.get("title", {})
    title = (
        title_obj.get("pretty")
        or title_obj.get("english")
        or title_obj.get("japanese")
        or str(id_)
    )

    link = f"{URL_INDEX}g/{id_}/"

    # thumbnail is CoverInfo {path, width, height}
    thumb_obj = detail.get("thumbnail", {})
    thumb_path = thumb_obj.get("path") if isinstance(thumb_obj, dict) else thumb_obj
    thumb = _cdn_url(thumb_path)

    tags = []
    languages = []
    categories = []
    parodies = []
    characters = []
    artists = []
    groups = []

    for t in detail.get("tags", []):
        name = t.get("name", "")
        url_path = t.get("url", "")
        tag_url = URL_INDEX.rstrip("/") + url_path
        count = str(t.get("count", ""))
        tag_type = t.get("type", "tag")

        if tag_type == "tag":
            tags.append(Tag(name, tag_url, count))
        elif tag_type == "language":
            languages.append(Language(name, tag_url, count))
        elif tag_type == "category":
            categories.append(Category(name, tag_url, count))
        elif tag_type == "parody":
            parodies.append(Parody(name, tag_url, count))
        elif tag_type == "character":
            characters.append(Character(name, tag_url, count))
        elif tag_type == "artist":
            artists.append(Artist(name, tag_url, count))
        elif tag_type == "group":
            groups.append(Group(name, tag_url, count))

    pages = detail.get("num_pages")

    upload_date = detail.get("upload_date")
    uploaded = str(upload_date) if upload_date else None

    return Hentai(
        id_,
        title,
        link,
        thumb,
        tags,
        languages,
        categories,
        pages,
        uploaded,
        parodies,
        characters,
        artists,
        groups,
    )

def _parse_url_page(url_page):
    """
    Parse a legacy HTML URL template (e.g. 'https://nhentai.net/tag/femdom/?page={page}')
    and return (api_path, base_params) suitable for the v2 API.

    Returns a tuple (str, dict).  page number is NOT included; callers add it.
    """
    # Fill in a dummy page so urllib.parse can read the query string
    sample = url_page.format(page=1)
    parsed = urllib.parse.urlparse(sample)
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    path = parsed.path.rstrip("/")

    # ── Homepage (/  or empty)
    if path in ("", "/"):
        return "/galleries", {}

    # ── Search  /search/?q=...
    if re.fullmatch(r"/?search/?", path):
        query = qs.get("q", [""])[0]
        return "/search", {"query": query}

    # ── Tag  /tag/{slug}
    m = re.fullmatch(r"/?tag/([^/]+)", path)
    if m:
        t = _resolve_tag("tag", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    # ── Language  /language/{slug}
    m = re.fullmatch(r"/?language/([^/]+)", path)
    if m:
        t = _resolve_tag("language", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    # ── Artist  /artist/{slug}
    m = re.fullmatch(r"/?artist/([^/]+)", path)
    if m:
        t = _resolve_tag("artist", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    # Fallback: treat as homepage listing
    return "/galleries", {}

def scrape_hentais(url_page):
    """
    Yield fully-populated Hentai objects by walking the nhentai API.

    url_page  – legacy URL template string with {page} placeholder
                (kept for backwards compatibility with app.py)
    """
    api_path, base_params = _parse_url_page(url_page)

    page_num = 0
    seen_ids: set = set()

    while True:
        page_num += 1
        params = {**base_params, "page": page_num}

        try:
            result = _api_get(api_path, params)
        except Exception:
            # No more pages or unrecoverable error → signal end of stream
            while True:
                yield
            return

        # PaginatedResponse_GalleryListItem_ uses "result" (not "results")
        if isinstance(result, list):
            items = result
            total_pages = None
        elif isinstance(result, dict):
            items = result.get("result", [])
            total_pages = result.get("num_pages")
        else:
            items = []
            total_pages = None

        if not items:
            while True:
                yield
            return

        for item in items:
            gallery_id = item.get("id")
            if gallery_id is None or gallery_id in seen_ids:
                continue
            seen_ids.add(gallery_id)

            # Fetch full gallery detail for tags, page list, precise thumbnail
            try:
                detail = _api_get(f"/galleries/{gallery_id}", silent=True)
            except Exception:
                continue

            yield _build_hentai(detail)

        # Stop iterating when we've consumed all pages
        if total_pages is not None and page_num >= total_pages:
            while True:
                yield
            return

