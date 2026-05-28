import os
import threading
import time

import bs4

from .constants import DONE_POSTFIX, HENTAIS_DIR, SOUP_PARSER, THUMB_NAME, URL_READ, WAIT_FOR_PAGE_DOWNLOAD_SLEEP
from .image_backend import render_image
from .net import receive, receive_raw
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

        self.stop_downloading_in_background()

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.id_ == other.id_

    def image_path(self, img):
        path = HENTAIS_DIR + str(self.id_) + "/" + img
        dir_ = os.path.dirname(path)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)
        return path

    def image_cached(self, img):
        path = self.image_path(img)
        done = path + DONE_POSTFIX
        return os.path.isfile(done)

    def image_set_cached(self, img):
        path = self.image_path(img)
        done = path + DONE_POSTFIX
        with open(done, "w"):
            pass

    def image_unset_cached(self, img):
        path = self.image_path(img)
        done = path + DONE_POSTFIX
        if os.path.isfile(done):
            os.remove(done)

    def image_cache(self, url, img, silent=False):
        self.image_unset_cached(img)
        data = receive_raw(url, silent=silent)
        with open(self.image_path(img), "wb") as f:
            f.write(data)
        self.image_set_cached(img)

    def image_print(self, img):
        assert self.image_cached(img)
        path = self.image_path(img)
        render_image(path)

    def image_print_cache(self, url, img):
        if not self.image_cached(img):
            self.image_cache(url, img)
        self.image_print(img)

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
        if not self.image_cached(THUMB_NAME):
            self.image_cache(self.thumb_url, THUMB_NAME)
        self.image_print(THUMB_NAME)

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

    def download_in_background(self):
        def download_all_pages():
            try:
                for page_num in range(1, self.pages + 1):
                    if self.downloading_pages_in_background is False:
                        break

                    url = URL_READ.format(id=self.id_, page=page_num)
                    data = receive(url, silent=True)

                    soup = bs4.BeautifulSoup(data, SOUP_PARSER)
                    link = soup.find(id="image-container").img["minq_nhentai"]
                    self.image_cache(link, str(page_num), silent=False)
            finally:
                self.downloading_pages_in_background = False

        if self.downloading_pages_in_background:
            print("Already downloading")
            return
        self.downloading_pages_in_background = True
        threading.Thread(target=download_all_pages).start()

    def stop_downloading_in_background(self):
        self.downloading_pages_in_background = False

    def reading_loop(self):
        self.download_in_background()

        cmds = []
        cmds.append(cmd_quit := ["quit", "q", "exit", "e", "back", "b"])
        cmds.append(cmd_next := ["next page", "next", "n"])
        cmds.append(cmd_prev := ["prevoius page", "prev", "p"])
        cmds.append(cmd_page := ["go to page", "page", "go to", "goto", "go", "g"])

        page_num = 1
        while page_num <= self.pages and page_num >= 1:
            if not self.image_cached(str(page_num)):
                print_tmp("Downloading...")
                try:
                    while not self.image_cached(str(page_num)):
                        time.sleep(WAIT_FOR_PAGE_DOWNLOAD_SLEEP)
                except KeyboardInterrupt:
                    break

            print(f"Page: {page_num} / {self.pages}")
            self.image_print(str(page_num))

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

