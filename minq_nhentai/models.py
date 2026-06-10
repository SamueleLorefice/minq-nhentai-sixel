import threading
import time
from typing import Any

from rich.text import Text

from .api import get_gallery_detail, iter_cdn_urls
from .cache import HentaiCache
from .constants import THUMB_NAME, WAIT_FOR_PAGE_DOWNLOAD_SLEEP
from .ui import alert, error, hint, info, input, print, print_tmp, success, warn

_CACHE_DELEGATED: frozenset[str] = frozenset(
    {
        "image_path",
        "image_cached",
        "image_set_cached",
        "image_unset_cached",
        "image_cache",
        "image_cache_any",
        "image_print",
        "image_print_cache",
        "image_print_cache_any",
    }
)


class Tag:
    prefix: str = "Tag"
    style: str = "yellow"

    def __init__(self, name: str, link: str, count: str) -> None:
        self.name: str = name
        self.link: str = link
        self.count: str = count

    def __repr__(self) -> str:
        return f"\u25b8 {self.prefix}: {self.name} ({self.count})"

    def __rich__(self) -> Text:
        return Text.from_markup(
            f"[{self.style}]\u25b8 {self.prefix}:[/] [bold]{self.name}[/] ({self.count})"
        )


class Language(Tag):
    prefix: str = "Language"
    style: str = "green"


class Category(Tag):
    prefix: str = "Category"
    style: str = "bold white"


class Parody(Tag):
    prefix: str = "Parody"
    style: str = "blue"


class Character(Tag):
    prefix: str = "Character"
    style: str = "cyan"


class Artist(Tag):
    prefix: str = "Artist"
    style: str = "magenta"


class Group(Tag):
    prefix: str = "Group"
    style: str = "dim"


class Hentai:
    def __init__(
        self,
        id_: int,
        title: str,
        link: str,
        thumb: str | None,
        tags: list[Tag],
        languages: list[Language],
        categories: list[Category],
        pages: int,
        uploaded: str | None,
        parodies: list[Parody],
        characters: list[Character],
        artists: list[Artist],
        groups: list[Group],
        page_assets: list[dict[str, Any]] | None = None,
    ) -> None:
        self.id_: int = id_
        self.title: str = title
        self.link: str = link
        self.thumb_url: str | None = thumb
        self.tags: list[Tag] = tags
        self.languages: list[Language] = languages
        self.categories: list[Category] = categories
        self.pages: int = pages
        self.uploaded: str | None = uploaded
        self.parodies: list[Parody] = parodies
        self.characters: list[Character] = characters
        self.artists: list[Artist] = artists
        self.groups: list[Group] = groups
        self.page_assets: list[dict[str, Any]] = self._normalize_page_assets(page_assets)
        self.cache: HentaiCache = HentaiCache(self.id_)

        self.downloading_pages_in_background: bool = False
        self._download_lock: threading.Lock = threading.Lock()
        self.stop_downloading_in_background()

    def _normalize_page_assets(self, page_assets: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if not isinstance(page_assets, list):
            blank: list[dict[str, Any]] = [
                {
                    "page_path": None,
                    "thumb_path": None,
                    "width": None,
                    "height": None,
                    "thumb_width": None,
                    "thumb_height": None,
                }
            ] * self.pages
            return blank

        normalized: list[dict[str, Any]] = []
        for index in range(self.pages):
            item: dict[str, Any] = page_assets[index] if index < len(page_assets) else {}
            if not isinstance(item, dict):
                item = {}
            normalized.append(
                {
                    "page_path": item.get("page_path"),
                    "thumb_path": item.get("thumb_path"),
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "thumb_width": item.get("thumb_width"),
                    "thumb_height": item.get("thumb_height"),
                },
            )
        return normalized

    def _page_asset(self, page_num: int) -> dict[str, Any] | None:
        if page_num < 1 or page_num > len(self.page_assets):
            return None
        return self.page_assets[page_num - 1]

    def _thumb_cache_name(self, page_num: int) -> str:
        return f"page_{page_num}_thumb"

    def _page_cache_name(self, page_num: int) -> str:
        return str(page_num)

    def _page_urls(self, page_num: int, kind: str) -> list[str]:
        asset: dict[str, Any] | None = self._page_asset(page_num)
        if asset is None:
            return []
        path: Any = asset.get("thumb_path") if kind == "thumb" else asset.get("page_path")
        if not path:
            return []
        return list(iter_cdn_urls(path, kind))

    def _prefetch_metadata_if_needed(self) -> None:
        needs_metadata: bool = len(self.page_assets) != self.pages or any(
            not isinstance(asset, dict) or (asset.get("page_path") is None and asset.get("thumb_path") is None)
            for asset in self.page_assets
        )
        if not needs_metadata:
            return

        detail: dict[str, Any] = get_gallery_detail(self.id_, silent=True)
        pages: list[Any] = detail.get("pages", []) if isinstance(detail, dict) else []
        page_assets: list[dict[str, Any]] = []
        for page in pages:
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
                },
            )
        self.page_assets = self._normalize_page_assets(page_assets)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.id_ == other.id_

    def __getattr__(self, name: str) -> Any:
        if name in _CACHE_DELEGATED:
            return getattr(self.cache, name)
        msg = f"{type(self).__name__!r} object has no attribute {name!r}"
        raise AttributeError(msg)

    def show(self) -> None:
        print(f"[bold cyan]Title:[/] {self.title}")
        print(f"[green]Pages:[/] {self.pages}")
        print(f"[blue underline]{self.link}[/]")
        for t in self.tags:
            print(t)
        for a in self.artists:
            print(a)
        for lang in self.languages:
            print(lang)
        self.print_thumb()

    def print_thumb(self) -> None:
        if self.thumb_url is None:
            warn("Thumbnail unavailable")
            return
        if not self.image_cached(THUMB_NAME):
            self.image_cache_any(iter_cdn_urls(self.thumb_url, "thumb"), THUMB_NAME)
        self.image_print(THUMB_NAME)

    def ensure_page_thumb_cached(self, page_num: int, silent: bool = False) -> bool:
        cache_name: str = self._thumb_cache_name(page_num)
        if self.image_cached(cache_name):
            return True

        urls: list[str] = self._page_urls(page_num, "thumb")
        if not urls:
            return False

        self.image_cache_any(urls, cache_name, silent=silent)
        return True

    def ensure_page_image_cached(self, page_num: int, silent: bool = False) -> bool:
        cache_name: str = self._page_cache_name(page_num)
        if self.image_cached(cache_name):
            return True

        urls: list[str] = self._page_urls(page_num, "image")
        if not urls:
            return False

        self.image_cache_any(urls, cache_name, silent=silent)
        return True

    def print_page_thumb(self, page_num: int) -> None:
        self.image_print(self._thumb_cache_name(page_num))

    def print_page_image(self, page_num: int) -> None:
        self.image_print(self._page_cache_name(page_num))

    def contains_tag(self, tag: str) -> bool:
        return any(tag == t.name for t in self.tags)

    def contains_language(self, lang: str) -> bool:
        return any(lang == language.name for language in self.languages)

    def contains_artist(self, artist: str) -> bool:
        return any(artist == a.name for a in self.artists)

    def download_in_background(self, asset_kind: str = "image") -> None:
        if asset_kind not in ("thumb", "image"):
            asset_kind = "image"

        def download_all_pages() -> None:
            downloaded: int = 0
            try:
                self._prefetch_metadata_if_needed()

                what: str = "thumbnails" if asset_kind == "thumb" else "pages"
                info(f"Starting background download of {what} for gallery {self.id_}")

                for page_num in range(1, self.pages + 1):
                    if self.downloading_pages_in_background is False:
                        break
                    try:
                        if asset_kind == "thumb":
                            ok: bool = self.ensure_page_thumb_cached(page_num, silent=True)
                        else:
                            ok = self.ensure_page_image_cached(page_num, silent=True)
                        if ok:
                            downloaded += 1
                            if page_num == 1 or page_num == self.pages or page_num % 10 == 0:
                                print_tmp(f"Background download ({what}): {page_num}/{self.pages}")
                    except Exception as e:
                        error(f"Failed to cache {what[:-1]} {page_num} for gallery {self.id_}: {e}")
                success(f"Background download finished: {downloaded}/{self.pages} {what}")
            finally:
                self.downloading_pages_in_background = False

        with self._download_lock:
            if self.downloading_pages_in_background:
                warn("Already downloading")
                return
            self.downloading_pages_in_background = True
        threading.Thread(target=download_all_pages, daemon=True).start()

    def stop_downloading_in_background(self) -> None:
        self.downloading_pages_in_background = False

    def reading_loop(self) -> None:
        self._prefetch_metadata_if_needed()
        self.download_in_background(asset_kind="thumb")

        cmds: list[list[str]] = []
        cmds.append(cmd_quit := ["quit", "q", "exit", "e", "back", "b"])
        cmds.append(cmd_next := ["next page", "next", "n"])
        cmds.append(cmd_prev := ["previous page", "prev", "p"])
        cmds.append(cmd_page := ["go to page", "page", "go to", "goto", "go", "g"])
        cmds.append(cmd_zoom := ["zoom", "z", "full", "f"])
        cmds.append(cmd_thumb := ["thumbnail", "thumb", "t"])

        page_num: int = 1
        view_mode: str = "thumb"
        while page_num <= self.pages and page_num >= 1:
            cache_name: str = (
                self._thumb_cache_name(page_num) if view_mode == "thumb" else self._page_cache_name(page_num)
            )

            if not self.image_cached(cache_name):
                if view_mode == "thumb" and self.downloading_pages_in_background:
                    print_tmp("Downloading thumbnail...")
                    try:
                        while not self.image_cached(cache_name):
                            if not self.downloading_pages_in_background:
                                break
                            time.sleep(WAIT_FOR_PAGE_DOWNLOAD_SLEEP)
                    except KeyboardInterrupt:
                        break

                if not self.image_cached(cache_name):
                    print_tmp("Downloading full page..." if view_mode == "image" else "Downloading thumbnail...")
                    try:
                        if view_mode == "thumb":
                            ok: bool = self.ensure_page_thumb_cached(page_num, silent=False)
                        else:
                            ok = self.ensure_page_image_cached(page_num, silent=False)
                    except KeyboardInterrupt:
                        break
                    except Exception as exc:
                        page_type: str = "full page" if view_mode == "image" else "thumbnail"
                        error(f"Could not download {page_type} {page_num}: {exc}")
                        alert()
                        if view_mode == "image":
                            view_mode = "thumb"
                            continue
                        return
                    if not ok:
                        asset_type: str = "image" if view_mode == "image" else "thumbnail"
                        error(f"No {asset_type} URL available for page {page_num}.")
                        alert()
                        if view_mode == "image":
                            view_mode = "thumb"
                            continue
                        return

            print(f"[bold]Page: {page_num} / {self.pages} [{view_mode}][/]")
            if view_mode == "thumb":
                self.print_page_thumb(page_num)
            else:
                self.print_page_image(page_num)

            c: str = input("[bold cyan]>>[/] ", "q")
            if c == "":
                c = cmd_next[0]

            if c in cmd_quit:
                break
            if c in cmd_next:
                page_num += 1
            elif c in cmd_prev:
                if page_num == 1:
                    warn("This is the first page")
                    alert()
                else:
                    page_num -= 1
            elif c in cmd_page:
                page_input: str | int = input("[bold cyan]Enter page number>>[/] ", -1)
                if page_input == -1:
                    continue
                try:
                    page_num = int(page_input)
                except ValueError:
                    error(f"Not a valid number: {page_input}")
                    alert()
                    continue
                if page_num < 1 or page_num > self.pages:
                    error(f"Invalid page: {page_num} (must be between 0 and {self.pages})")
                    alert()
                    continue
            elif c in cmd_zoom:
                view_mode = "image"
            elif c in cmd_thumb:
                view_mode = "thumb"
            else:
                warn(f"Unknown command: {c}")
                hint("List of available commands:")
                for item in cmds:
                    hint(f"->{item}")
                alert()

        self.stop_downloading_in_background()
