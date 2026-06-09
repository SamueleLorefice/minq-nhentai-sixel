import threading
from pathlib import Path
from typing import Any

from .constants import DONE_POSTFIX, HENTAIS_DIR
from .image_backend import render_image
from .net import receive_raw


class HentaiCache:
    def __init__(self, hentai_id: int) -> None:
        self.hentai_id: int = hentai_id
        self._lock: threading.RLock = threading.RLock()

    def _base_dir(self) -> Path:
        return Path(HENTAIS_DIR) / str(self.hentai_id)

    def image_path(self, img: Any) -> str:
        path: Path = self._base_dir() / str(img)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def _cache_path(self, img: Any) -> Path:
        return self._base_dir() / str(img)

    def _done_path(self, img: Any) -> Path:
        return Path(self.image_path(img) + DONE_POSTFIX)

    def image_cached(self, img: Any) -> bool:
        return self._done_path(img).is_file()

    def image_set_cached(self, img: Any) -> None:
        self._done_path(img).parent.mkdir(parents=True, exist_ok=True)
        self._done_path(img).write_text("")

    def image_unset_cached(self, img: Any) -> None:
        self._done_path(img).unlink(missing_ok=True)

    def image_cache(self, url: str, img: Any, silent: bool = False) -> None:
        with self._lock:
            self.image_unset_cached(img)
            data: bytes = receive_raw(url, silent=silent)
            path: Path = self._cache_path(img)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.image_set_cached(img)

    def image_cache_any(self, urls: list[str], img: Any, silent: bool = False) -> None:
        last_exc: BaseException | None = None
        for url in urls:
            try:
                self.image_cache(url, img, silent=silent)
                return
            except Exception as exc:
                last_exc = exc
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"No download URLs available for {img}")

    def image_print(self, img: Any) -> None:
        if not self.image_cached(img):
            raise RuntimeError(f"Image {img} is not cached")
        render_image(self.image_path(img))

    def image_print_cache(self, url: str, img: Any, silent: bool = False) -> None:
        if not self.image_cached(img):
            self.image_cache(url, img, silent=silent)
        self.image_print(img)

    def image_print_cache_any(self, urls: list[str], img: Any, silent: bool = False) -> None:
        if not self.image_cached(img):
            self.image_cache_any(urls, img, silent=silent)
        self.image_print(img)
