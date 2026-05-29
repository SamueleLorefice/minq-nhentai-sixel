import os

from .constants import DONE_POSTFIX, HENTAIS_DIR
from .image_backend import render_image
from .net import receive_raw


class HentaiCache:
    def __init__(self, hentai_id):
        self.hentai_id = hentai_id

    def image_path(self, img):
        path = os.path.join(HENTAIS_DIR, str(self.hentai_id), img)
        dir_ = os.path.dirname(path)
        os.makedirs(dir_, exist_ok=True)
        return path

    def image_cached(self, img):
        done = self.image_path(img) + DONE_POSTFIX
        return os.path.isfile(done)

    def image_set_cached(self, img):
        done = self.image_path(img) + DONE_POSTFIX
        with open(done, "w"):
            pass

    def image_unset_cached(self, img):
        done = self.image_path(img) + DONE_POSTFIX
        if os.path.isfile(done):
            os.remove(done)

    def image_cache(self, url, img, silent=False):
        self.image_unset_cached(img)
        data = receive_raw(url, silent=silent)
        with open(self.image_path(img), "wb") as f:
            f.write(data)
        self.image_set_cached(img)

    def image_cache_any(self, urls, img, silent=False):
        last_exc = None
        for url in urls:
            try:
                self.image_cache(url, img, silent=silent)
                return
            except Exception as exc:
                last_exc = exc
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"No download URLs available for {img}")

    def image_print(self, img):
        assert self.image_cached(img)
        render_image(self.image_path(img))

    def image_print_cache(self, url, img, silent=False):
        if not self.image_cached(img):
            self.image_cache(url, img, silent=silent)
        self.image_print(img)

    def image_print_cache_any(self, urls, img, silent=False):
        if not self.image_cached(img):
            self.image_cache_any(urls, img, silent=silent)
        self.image_print(img)


