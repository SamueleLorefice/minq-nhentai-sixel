import threading
import time

from .api import get_gallery_detail, iter_cdn_urls
from .cache import HentaiCache
from .constants import THUMB_NAME, WAIT_FOR_PAGE_DOWNLOAD_SLEEP
from .ui import alert, input, print, print_tmp


class Hentai:
    def __init__(
        self,
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
        page_assets=None,
    ):
        self.id_ = id_
        self.title = title
        self.link = link
        self.thumb_url = thumb
        self.tags = tags
        self.languages = languages
        self.categories = categories
        self.pages = pages
        self.uploaded = uploaded
        self.parodies = parodies
        self.characters = characters
        self.artists = artists
        self.groups = groups
        self.page_assets = self._normalize_page_assets(page_assets)
        self.cache = HentaiCache(self.id_)

        self.stop_downloading_in_background()

    def _normalize_page_assets(self, page_assets):
        if not isinstance(page_assets, list):
            return [None] * self.pages

        normalized = []
        for index in range(self.pages):
            item = page_assets[index] if index < len(page_assets) else None
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
                }
            )
        return normalized

    def _page_asset(self, page_num):
        if page_num < 1 or page_num > len(self.page_assets):
            return None
        return self.page_assets[page_num - 1]

    def _thumb_cache_name(self, page_num):
        return f"page_{page_num}_thumb"

    def _page_cache_name(self, page_num):
        return str(page_num)

    def _page_urls(self, page_num, kind):
        asset = self._page_asset(page_num)
        if asset is None:
            return []
        path = asset.get("thumb_path") if kind == "thumb" else asset.get("page_path")
        if not path:
            return []
        return list(iter_cdn_urls(path, kind))

    def _prefetch_metadata_if_needed(self):
        needs_metadata = len(self.page_assets) != self.pages or any(
            not isinstance(asset, dict) or (asset.get("page_path") is None and asset.get("thumb_path") is None)
            for asset in self.page_assets
        )
        if not needs_metadata:
            return

        detail = get_gallery_detail(self.id_, silent=True)
        pages = detail.get("pages", []) if isinstance(detail, dict) else []
        page_assets = []
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
                }
            )
        self.page_assets = self._normalize_page_assets(page_assets)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.id_ == other.id_

    def image_path(self, img):
        return self.cache.image_path(img)

    def image_cached(self, img):
        return self.cache.image_cached(img)

    def image_set_cached(self, img):
        self.cache.image_set_cached(img)

    def image_unset_cached(self, img):
        self.cache.image_unset_cached(img)

    def image_cache(self, url, img, silent=False):
        self.cache.image_cache(url, img, silent=silent)

    def image_cache_any(self, urls, img, silent=False):
        self.cache.image_cache_any(urls, img, silent=silent)

    def image_print(self, img):
        self.cache.image_print(img)

    def image_print_cache(self, url, img):
        self.cache.image_print_cache(url, img)

    def image_print_cache_any(self, urls, img, silent=False):
        self.cache.image_print_cache_any(urls, img, silent=silent)

    def show(self):
        print(f"Title: {self.title}")
        print(f"Pages: {self.pages}")
        print(self.link)
        for t in self.tags:
            print(t)
        for a in self.artists:
            print(a)
        for l in self.languages:
            print(l)
        self.print_thumb()

    def print_thumb(self):
        if self.thumb_url is None:
            print("[Thumbnail unavailable]")
            return
        if not self.image_cached(THUMB_NAME):
            self.image_cache_any(iter_cdn_urls(self.thumb_url, "thumb"), THUMB_NAME)
        self.image_print(THUMB_NAME)

    def ensure_page_thumb_cached(self, page_num, silent=False):
        cache_name = self._thumb_cache_name(page_num)
        if self.image_cached(cache_name):
            return True

        urls = self._page_urls(page_num, "thumb")
        if not urls:
            return False

        self.image_cache_any(urls, cache_name, silent=silent)
        return True

    def ensure_page_image_cached(self, page_num, silent=False):
        cache_name = self._page_cache_name(page_num)
        if self.image_cached(cache_name):
            return True

        urls = self._page_urls(page_num, "image")
        if not urls:
            return False

        self.image_cache_any(urls, cache_name, silent=silent)
        return True

    def print_page_thumb(self, page_num):
        self.image_print(self._thumb_cache_name(page_num))

    def print_page_image(self, page_num):
        self.image_print(self._page_cache_name(page_num))

    def contains_tag(self, tag):
        if len(self.tags) == 0:
            return True
        for t in self.tags:
            if tag == t.name:
                return True
        return False

    def contains_language(self, lang):
        if len(self.languages) == 0:
            return True
        for l in self.languages:
            if lang == l.name:
                return True
        return False

    def contains_artist(self, artist):
        if len(self.artists) == 0:
            return True
        for a in self.artists:
            if artist == a.name:
                return True
        return False

    def download_in_background(self, asset_kind="image"):
        if asset_kind not in ("thumb", "image"):
            asset_kind = "image"

        def download_all_pages():
            downloaded = 0
            try:
                self._prefetch_metadata_if_needed()

                what = "thumbnails" if asset_kind == "thumb" else "pages"
                print(f"Starting background download of {what} for gallery {self.id_}")

                for page_num in range(1, self.pages + 1):
                    if self.downloading_pages_in_background is False:
                        break
                    try:
                        if asset_kind == "thumb":
                            ok = self.ensure_page_thumb_cached(page_num, silent=True)
                        else:
                            ok = self.ensure_page_image_cached(page_num, silent=True)
                        if ok:
                            downloaded += 1
                            if page_num == 1 or page_num == self.pages or page_num % 10 == 0:
                                print_tmp(f"Background download ({what}): {page_num}/{self.pages}")
                    except Exception as e:
                        print(f"Failed to cache {what[:-1]} {page_num} for gallery {self.id_}: {e}")
                print(f"Background download finished: {downloaded}/{self.pages} {what}")
            finally:
                self.downloading_pages_in_background = False

        if self.downloading_pages_in_background:
            print("Already downloading")
            return
        self.downloading_pages_in_background = True
        threading.Thread(target=download_all_pages, daemon=True).start()

    def stop_downloading_in_background(self):
        self.downloading_pages_in_background = False

    def reading_loop(self):
        self._prefetch_metadata_if_needed()
        self.download_in_background(asset_kind="thumb")

        cmds = []
        cmds.append(cmd_quit := ["quit", "q", "exit", "e", "back", "b"])
        cmds.append(cmd_next := ["next page", "next", "n"])
        cmds.append(cmd_prev := ["prevoius page", "prev", "p"])
        cmds.append(cmd_page := ["go to page", "page", "go to", "goto", "go", "g"])
        cmds.append(cmd_zoom := ["zoom", "z", "full", "f"])
        cmds.append(cmd_thumb := ["thumbnail", "thumb", "t"])

        page_num = 1
        view_mode = "thumb"
        while page_num <= self.pages and page_num >= 1:
            cache_name = self._thumb_cache_name(page_num) if view_mode == "thumb" else self._page_cache_name(page_num)

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
                            ok = self.ensure_page_thumb_cached(page_num, silent=False)
                        else:
                            ok = self.ensure_page_image_cached(page_num, silent=False)
                    except KeyboardInterrupt:
                        break
                    except Exception as exc:
                        alert(f"Could not download {'full page' if view_mode == 'image' else 'thumbnail'} {page_num}: {exc}")
                        if view_mode == "image":
                            view_mode = "thumb"
                            continue
                        return
                    if not ok:
                        alert(f"No {'image' if view_mode == 'image' else 'thumbnail'} URL available for page {page_num}.")
                        if view_mode == "image":
                            view_mode = "thumb"
                            continue
                        return

            print(f"Page: {page_num} / {self.pages} [{view_mode}]")
            if view_mode == "thumb":
                self.print_page_thumb(page_num)
            else:
                self.print_page_image(page_num)

            c = input(">> ", "q")
            if c == "":
                c = cmd_next[0]

            if c in cmd_quit:
                break
            elif c in cmd_next:
                page_num += 1
            elif c in cmd_prev:
                if page_num == 1:
                    alert("This is the first page")
                else:
                    page_num -= 1
            elif c in cmd_page:
                page = input("Enter page number>> ", -1)
                if page == -1:
                    continue
                try:
                    page = int(page)
                except ValueError:
                    alert(f"Not a valid number: {page}")
                    continue
                if page < 1 or page > self.pages:
                    alert(f"Invalid page: {page} (must be between 0 and {self.pages})")
                    continue
                page_num = page
            elif c in cmd_zoom:
                view_mode = "image"
            elif c in cmd_thumb:
                view_mode = "thumb"
            else:
                print(f"Unknown command: {c}")
                print("List of available commands:")
                for item in cmds:
                    print(f"->{item}")
                alert()

        self.stop_downloading_in_background()


class Tag:
    prefix = "Tag"

    def __init__(self, name, link, count):
        self.name = name
        self.link = link
        self.count = count

    def __repr__(self):
        return f"-> {self.prefix}: {self.name} ({self.count}) {self.link}"


class Language(Tag):
    prefix = "Language"


class Category(Tag):
    prefix = "Category"


class Parody(Tag):
    prefix = "Parody"


class Character(Tag):
    prefix = "Character"


class Artist(Tag):
    prefix = "Artist"


class Group(Tag):
    prefix = "Group"

