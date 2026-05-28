import sys

from .constants import URL_ARTIST, URL_INDEX, URL_LANG, URL_PAGE_POSTFIX, URL_SEARCH, URL_TAG
from .net import does_page_exist
from .scrape import scrape_hentais
from .ui import alert, input, print, print_tmp


def interactive_hentai_enjoyment(
    search_term=None, required_tags=None, required_language=None, required_artist=None
):
    cmds = []
    cmds.append(cmd_quit := ["quit", "q", "exit", "e"])
    cmds.append(cmd_next := ["next hentai", "next", "n"])
    cmds.append(cmd_prev := ["previous hentai", "previous", "prev", "p"])
    cmds.append(cmd_read := ["read hentai", "read", "r", "enjoy", "cum", "wank", "sex"])
    cmds.append(cmd_download := ["download hentai", "download", "d"])

    assert type(required_tags) in (list, tuple)
    assert type(required_language) in (str, type(None))

    url_page = None

    if search_term is not None:
        assert url_page is None
        url_page = URL_SEARCH.format(search=search_term)

    if required_artist is not None:
        if not does_page_exist(URL_ARTIST.format(artist=required_artist)):
            print(f"Artist doesn't exist: {required_artist}")
            sys.exit(1)

        if url_page is None:
            url_page = URL_ARTIST.format(artist=required_artist)
            required_artist = None

    for tag in required_tags:
        if not does_page_exist(URL_TAG.format(tag=tag)):
            print(f"Tag doesn't exist: {tag}")
            sys.exit(1)

    if url_page is None:
        if len(required_tags) != 0:
            url_page = URL_TAG.format(tag=required_tags[0])
            required_tags = required_tags[1:]

    if required_language is not None:
        if not does_page_exist(URL_LANG.format(lang=required_language)):
            print(f"Language doesn't exist: {required_language}")
            sys.exit(1)

        if url_page is None:
            url_page = URL_LANG.format(lang=required_language)
            required_language = None

    if url_page is None:
        url_page = URL_INDEX

    if "?" in url_page:
        url_page += "&"
    else:
        url_page += "?"

    url_page += URL_PAGE_POSTFIX

    running = True
    hentais = []
    ind = 0

    for hentai in scrape_hentais(url_page):
        if hentai is None:
            if len(hentais) == 0:
                alert("No hentais with the specified parameters")
                break
            else:
                alert("This was the last hentai")
            ind = len(hentais) - 1
        else:
            find_new_hentai = False

            for h in hentais:
                if h == hentai:
                    find_new_hentai = "duplicate"
                    break

            if required_artist is not None:
                if not hentai.contains_artist(required_artist):
                    find_new_hentai = f"missing artist: {required_artist}"

            for tag in required_tags:
                if not hentai.contains_tag(tag):
                    find_new_hentai = f"missing tag: {tag}"
                    break

            if required_language is not None:
                if not hentai.contains_language(required_language):
                    find_new_hentai = f"missing langiage: {required_language}"

            if find_new_hentai:
                print_tmp(
                    f"Hentai rejected (reason: {find_new_hentai}), searching for another one..."
                )
                continue

            hentais.append(hentai)

        while running:
            if ind >= len(hentais):
                break
            hentai = hentais[ind]

            hentai.show()

            c = input("> ", cmd_quit[0])

            if c == "":
                c = cmd_next[0]

            if c in cmd_quit:
                running = False
            elif c in cmd_next:
                ind += 1
            elif c in cmd_prev:
                ind -= 1
            elif c in cmd_read:
                hentai.reading_loop()
            elif c in cmd_download:
                hentai.download_in_background()
            else:
                print(f"Unknown command: {c}")
                print("List of available commands:")
                for cmd in cmds:
                    print(f"-> {cmd}")
                alert()

        else:
            break

