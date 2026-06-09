import time

import requests

from .constants import NET_TOO_MANY_REQUESTS_SLEEP
from .errors import ExceptionNetPageNotFound, ExceptionNetUnknown
from .ui import print_tmp


def receive_raw(url: str, silent: bool = False) -> bytes:
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
    }
    while True:
        try:
            page = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException:
            if not silent:
                print_tmp(
                    f"Network error while fetching page, retrying in {NET_TOO_MANY_REQUESTS_SLEEP} seconds",
                )
            time.sleep(NET_TOO_MANY_REQUESTS_SLEEP)
            continue

        if page.ok:
            return page.content

        if page.status_code == 404:
            raise ExceptionNetPageNotFound()

        if page.status_code == 429:
            retry_after = page.headers.get("Retry-After")
            if retry_after is None:
                sleep_for = NET_TOO_MANY_REQUESTS_SLEEP
            else:
                try:
                    sleep_for = float(retry_after)
                except ValueError:
                    sleep_for = NET_TOO_MANY_REQUESTS_SLEEP

            if not silent:
                print_tmp(
                    f"Too many requests, server refused connection, retrying in {sleep_for} seconds",
                )
            time.sleep(sleep_for)
            continue

        raise ExceptionNetUnknown(f"{url} {page.status_code} {page.reason}")


def receive(url: str, silent: bool = False) -> str:
    return receive_raw(url, silent=silent).decode()


def does_page_exist(url: str) -> bool:
    try:
        receive(url)
    except ExceptionNetPageNotFound:
        return False
    return True
