import sys
import urllib.parse

from .constants import URL_INDEX, URL_SEARCH
from .models import Hentai
from .scrape import get_hentai_by_id, scrape_hentais, tag_exists
from .ui import alert, error, hint, info, input, print_tmp, warn


def _quote_filter_value(value: str) -> str:
    return value.replace('"', r"\"")


def _is_duplicate(hentai: Hentai, hentais: list[Hentai]) -> bool:
    return any(h == hentai for h in hentais)


def _check_missing_filters(
    hentai: Hentai,
    required_tags: list[str],
    required_language: str | None,
    required_artist: str | None,
) -> str | None:
    if required_artist is not None and not hentai.contains_artist(required_artist):
        return f"missing artist: {required_artist}"
    for tag in required_tags:
        if not hentai.contains_tag(tag):
            return f"missing tag: {tag}"
    if required_language is not None and not hentai.contains_language(required_language):
        return f"missing language: {required_language}"
    return None


def _build_search_query(
    search_term: str | None,
    required_tags: list[str],
    required_language: str | None,
    required_artist: str | None,
) -> str:
    parts: list[str] = []

    if search_term is not None and search_term.strip() != "":
        parts.append(search_term.strip())

    for tag in required_tags:
        parts.append(f'tag:"{_quote_filter_value(tag)}"')

    if required_language is not None and required_language.strip() != "":
        parts.append(f'language:"{_quote_filter_value(required_language)}"')

    if required_artist is not None and required_artist.strip() != "":
        parts.append(f'artist:"{_quote_filter_value(required_artist)}"')

    return " ".join(parts)


def _build_page_url(search_query: str) -> str:
    if search_query:
        encoded_query: str = urllib.parse.quote_plus(search_query)
        url_page: str = URL_SEARCH.format(search=encoded_query)
    else:
        url_page = URL_INDEX

    parsed: urllib.parse.ParseResult = urllib.parse.urlparse(url_page)
    query: str = parsed.query
    if query:
        query += "&"
    query += "page={page}"
    return urllib.parse.urlunparse(parsed._replace(query=query))


def _validate_filters(
    required_tags: list[str],
    required_language: str | None,
    required_artist: str | None,
) -> bool:
    if required_artist is not None and not tag_exists("artist", required_artist):
        error(f"Artist doesn't exist: {required_artist}")
        return False
    for tag in required_tags:
        if not tag_exists("tag", tag):
            error(f"Tag doesn't exist: {tag}")
            return False
    if required_language is not None and not tag_exists("language", required_language):
        error(f"Language doesn't exist: {required_language}")
        return False
    return True


def _print_unknown_command(cmds: list[list[str]]) -> None:
    warn("Unknown command")
    hint("List of available commands:")
    for cmd in cmds:
        hint(f"-> {cmd}")
    alert()


def _handle_command(
    c: str,
    hentai: Hentai,
    cmds: list[list[str]],
    cmd_quit: list[str],
    cmd_read: list[str],
    cmd_download: list[str],
) -> str:
    if c in cmd_quit:
        return "quit"
    if c in cmd_read:
        hentai.reading_loop()
        return "show"
    if c in cmd_download:
        hentai.download_in_background()
        return "show"
    return ""


def interactive_hentai_enjoyment(
    search_term: str | None = None,
    required_tags: list[str] | None = None,
    required_language: str | None = None,
    required_artist: str | None = None,
    gallery_id: int | None = None,
) -> None:
    cmds: list[list[str]] = []
    cmds.append(cmd_quit := ["quit", "q", "exit", "e"])
    cmds.append(cmd_next := ["next hentai", "next", "n"])
    cmds.append(cmd_prev := ["previous hentai", "previous", "prev", "p"])
    cmds.append(cmd_read := ["read hentai", "read", "r", "enjoy", "cum", "wank", "sex"])
    cmds.append(cmd_download := ["download hentai", "download", "d"])

    if required_tags is None:
        required_tags = []

    if gallery_id is not None:
        try:
            hentai: Hentai = get_hentai_by_id(gallery_id, silent=True)
        except Exception as exc:
            error(f"Could not load gallery {gallery_id}: {exc}")
            sys.exit(1)

        running: bool = True
        while running:
            hentai.show()

            c: str = input("[bold cyan]>[/] ", cmd_quit[0])
            if c == "":
                c = cmd_read[0]

            action: str = _handle_command(c, hentai, cmds, cmd_quit, cmd_read, cmd_download)
            if action == "quit":
                running = False
            elif not action:
                if c in cmd_next or c in cmd_prev:
                    warn("Direct gallery mode only has one gallery loaded")
                else:
                    _print_unknown_command(cmds)
        return

    if not _validate_filters(required_tags, required_language, required_artist):
        sys.exit(1)

    search_query: str = _build_search_query(
        search_term,
        required_tags,
        required_language,
        required_artist,
    )

    url_page: str = _build_page_url(search_query)

    if search_query:
        required_tags = []
        required_language = None
        required_artist = None

    running = True
    hentais: list[Hentai] = []
    ind: int = 0

    for hentai in scrape_hentais(url_page):
        if hentai is None:
            if len(hentais) == 0:
                warn("No hentais with the specified parameters")
                break
            info("This was the last hentai")
            ind = len(hentais) - 1
        else:
            if _is_duplicate(hentai, hentais):
                print_tmp("Hentai rejected (reason: duplicate), searching for another one...")
                continue

            reason: str | None = _check_missing_filters(hentai, required_tags, required_language, required_artist)
            if reason is not None:
                print_tmp(f"Hentai rejected (reason: {reason}), searching for another one...")
                continue

            hentais.append(hentai)

        while running:
            if ind >= len(hentais):
                break
            hentai = hentais[ind]

            hentai.show()

            c = input("[bold cyan]>[/] ", cmd_quit[0])

            if c == "":
                c = cmd_next[0]

            action = _handle_command(c, hentai, cmds, cmd_quit, cmd_read, cmd_download)
            if action == "quit":
                running = False
            elif action == "show":
                continue
            elif c in cmd_next:
                ind += 1
            elif c in cmd_prev:
                ind -= 1
            else:
                _print_unknown_command(cmds)

        else:
            break
