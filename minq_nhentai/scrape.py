"""nhentai API v2 access helpers."""

from __future__ import annotations

import re
import time
import urllib.parse
from functools import lru_cache
from typing import Any, cast

from .api import api_get
from .constants import URL_INDEX
from .errors import ExceptionNetPageNotFound, ExceptionNetUnknown
from .models import Artist, Category, Character, Group, Hentai, Language, Parody, Tag


@lru_cache(maxsize=128)
def _resolve_tag(tag_type: str, slug: str) -> dict[str, Any]:
    """
    Return API TagResponse dict for (tag_type, slug).
    Raises ExceptionNetPageNotFound if the tag does not exist.
    tag_type is one of: tag, language, artist, group, parody, character, category
    """
    return cast(dict[str, Any], api_get(f"/tags/{tag_type}/{slug}"))


def tag_exists(tag_type: str, slug: str) -> bool:
    """Return True when the tag exists in the API, False otherwise."""
    try:
        _resolve_tag(tag_type, slug)
        return True
    except (ExceptionNetPageNotFound, ExceptionNetUnknown):
        return False


def _build_hentai(detail: dict[str, Any]) -> Hentai:
    """Convert a full GalleryDetailResponse dict into a Hentai model object."""
    id_: int = detail["id"]

    title_obj: dict[str, Any] = detail.get("title", {})
    title: str = title_obj.get("pretty") or title_obj.get("english") or title_obj.get("japanese") or str(id_)

    link: str = f"{URL_INDEX}g/{id_}/"

    thumb_obj: Any = detail.get("thumbnail", {})
    thumb: str | None = thumb_obj.get("path") if isinstance(thumb_obj, dict) else thumb_obj

    tags: list[Tag] = []
    languages: list[Language] = []
    categories: list[Category] = []
    parodies: list[Parody] = []
    characters: list[Character] = []
    artists: list[Artist] = []
    groups: list[Group] = []

    for t in detail.get("tags", []):
        name: str = t.get("name", "")
        url_path: str = t.get("url", "")
        tag_url: str = URL_INDEX.rstrip("/") + url_path
        count: str = str(t.get("count", ""))
        tag_type: str = t.get("type", "tag")

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

    pages: int = detail.get("num_pages") or 0
    page_assets: list[dict[str, Any]] = []
    for page in detail.get("pages", []) or []:
        if not isinstance(page, dict):
            page_assets.append({})
            continue
        page_assets.append(
            {
                "page_path": page.get("path"),
                "thumb_path": page.get("thumbnail"),
                "width": page.get("width"),
                "height": page.get("height"),
                "thumb_width": page.get("thumbnail_width"),
                "thumb_height": page.get("thumbnail_height"),
            }
        )

    upload_date: Any = detail.get("upload_date")
    uploaded: str | None = str(upload_date) if upload_date else None

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
        page_assets,
    )


def get_hentai_by_id(gallery_id: int, silent: bool = True) -> Hentai:
    """Fetch a single gallery directly by nhentai gallery id."""
    detail: dict[str, Any] = api_get(f"/galleries/{gallery_id}", silent=silent)
    return _build_hentai(detail)


def _parse_url_page(url_page: str) -> tuple[str, dict[str, Any]]:
    """
    Parse a legacy HTML URL template (e.g. 'https://nhentai.net/tag/femdom/?page={page}')
    and return (api_path, base_params) suitable for the v2 API.

    Returns a tuple (str, dict).  page number is NOT included; callers add it.
    """
    sample: str = url_page.format(page=1)
    parsed: urllib.parse.ParseResult = urllib.parse.urlparse(sample)
    qs: dict[str, list[str]] = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    path: str = parsed.path.rstrip("/")

    if path in ("", "/"):
        return "/galleries", {}

    if re.fullmatch(r"/?search/?", path):
        query: str = qs.get("q", [""])[0]
        return "/search", {"query": query}

    m: re.Match[str] | None = re.fullmatch(r"/?tag/([^/]+)", path)
    if m:
        t: dict[str, Any] = _resolve_tag("tag", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    m = re.fullmatch(r"/?language/([^/]+)", path)
    if m:
        t = _resolve_tag("language", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    m = re.fullmatch(r"/?artist/([^/]+)", path)
    if m:
        t = _resolve_tag("artist", m.group(1))
        return "/galleries/tagged", {"tag_id": t["id"]}

    return "/galleries", {}


def scrape_hentais(url_page: str) -> Any:
    """
    Yield fully-populated Hentai objects by walking the nhentai API.

    url_page  - legacy URL template string with {page} placeholder
                (kept for backwards compatibility with app.py)
    """
    api_path: str
    base_params: dict[str, Any]
    api_path, base_params = _parse_url_page(url_page)

    page_num: int = 0
    seen_ids: set[int] = set()

    while True:
        page_num += 1
        params: dict[str, Any] = {**base_params, "page": page_num}

        try:
            result: Any = api_get(api_path, params)
        except (ExceptionNetPageNotFound, ExceptionNetUnknown):
            return

        time.sleep(0.3)

        items: list[Any]
        total_pages: int | None
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
            return

        for item in items:
            gallery_id: int | None = item.get("id")
            if gallery_id is None or gallery_id in seen_ids:
                continue
            seen_ids.add(gallery_id)

            try:
                detail: dict[str, Any] = api_get(f"/galleries/{gallery_id}", silent=True)
            except (ExceptionNetPageNotFound, ExceptionNetUnknown):
                continue

            yield _build_hentai(detail)

        if isinstance(total_pages, int) and page_num >= total_pages:
            return
