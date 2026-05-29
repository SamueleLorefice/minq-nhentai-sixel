import time

import requests

from .constants import NET_TOO_MANY_REQUESTS_SLEEP
from .errors import Exception_net_page_not_found, Exception_net_unknown
from .ui import print_tmp


def receive_raw(url, silent=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
    }
    while True:
        try:
            page = requests.get(url, headers=headers)
        except requests.RequestException as exc:
            if not silent:
                print_tmp(
                    "Network error while fetching page, "
                    f"retrying in {NET_TOO_MANY_REQUESTS_SLEEP} seconds"
                )
            time.sleep(NET_TOO_MANY_REQUESTS_SLEEP)
            continue

        if page.ok:
            return page.content

        if page.status_code == 404:
            raise Exception_net_page_not_found()

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
                    "Too many requests, server refused connection, "
                    f"retrying in {sleep_for} seconds"
                )
            time.sleep(sleep_for)
            continue

        raise Exception_net_unknown(f"{url} {page.status_code} {page.reason}")


def receive(url, silent=False):
    return receive_raw(url, silent=silent).decode()


def does_page_exist(url):
    try:
        receive(url)
    except Exception_net_page_not_found:
        return False
    return True

