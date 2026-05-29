import sys
import urllib.parse

from .constants import URL_INDEX, URL_PAGE_POSTFIX, URL_SEARCH
from .scrape import get_hentai_by_id, scrape_hentais, tag_exists
from .ui import alert, input, print, print_tmp


def _quote_filter_value(value):
    return value.replace('"', r'\"')


def _build_search_query(search_term, required_tags, required_language, required_artist):
    parts = []

    if search_term is not None and search_term.strip() != "":
        parts.append(search_term.strip())

    for tag in required_tags:
        parts.append(f'tag:"{_quote_filter_value(tag)}"')

    if required_language is not None and required_language.strip() != "":
        parts.append(f'language:"{_quote_filter_value(required_language)}"')

    if required_artist is not None and required_artist.strip() != "":
        parts.append(f'artist:"{_quote_filter_value(required_artist)}"')

    return " ".join(parts)


def interactive_hentai_enjoyment(
    search_term=None, required_tags=None, required_language=None, required_artist=None, gallery_id=None
):
    cmds = []
    cmds.append(cmd_quit := ["quit", "q", "exit", "e"])
    cmds.append(cmd_next := ["next hentai", "next", "n"])
    cmds.append(cmd_prev := ["previous hentai", "previous", "prev", "p"])
    cmds.append(cmd_read := ["read hentai", "read", "r", "enjoy", "cum", "wank", "sex"])
    cmds.append(cmd_download := ["download hentai", "download", "d"])

    assert type(required_tags) in (list, tuple)
    assert type(required_language) in (str, type(None))

    if gallery_id is not None:
        try:
            hentai = get_hentai_by_id(gallery_id, silent=True)
        except Exception as exc:
            print(f"Could not load gallery {gallery_id}: {exc}")
            sys.exit(1)

        running = True
        while running:
            hentai.show()

            c = input("> ", cmd_quit[0])
            if c == "":
                c = cmd_read[0]

            if c in cmd_quit:
                running = False
            elif c in cmd_read:
                hentai.reading_loop()
            elif c in cmd_download:
                hentai.download_in_background()
            elif c in cmd_next or c in cmd_prev:
                alert("Direct gallery mode only has one gallery loaded")
            else:
                print(f"Unknown command: {c}")
                print("List of available commands:")
                for cmd in cmds:
                    print(f"-> {cmd}")
                alert()
        return

    if required_artist is not None:
        if not tag_exists("artist", required_artist):
            print(f"Artist doesn't exist: {required_artist}")
            sys.exit(1)

    for tag in required_tags:
        if not tag_exists("tag", tag):
            print(f"Tag doesn't exist: {tag}")
            sys.exit(1)

    if required_language is not None:
        if not tag_exists("language", required_language):
            print(f"Language doesn't exist: {required_language}")
            sys.exit(1)

    search_query = _build_search_query(
        search_term,
        required_tags,
        required_language,
        required_artist,
    )

    if search_query:
        encoded_query = urllib.parse.quote_plus(search_query)
        url_page = URL_SEARCH.format(search=encoded_query)
        # Filters are handled by API search query now; no client-side skipping needed.
        required_tags = []
        required_language = None
        required_artist = None
    else:
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
                    find_new_hentai = f"missing language: {required_language}"

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
