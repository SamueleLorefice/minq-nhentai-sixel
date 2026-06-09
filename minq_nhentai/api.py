import json
import urllib.parse
from typing import Any

from .constants import API_BASE
from .errors import ExceptionNetUnknown
from .net import receive

_CDN_SERVERS: dict[str, list[str]] | None = None


def api_get(path: str, params: dict[str, Any] | None = None, silent: bool = False) -> Any:
    url: str = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    result: Any = json.loads(receive(url, silent=silent))
    return result


def get_cdn_servers(refresh: bool = False, silent: bool = True) -> dict[str, list[str]]:
    global _CDN_SERVERS

    if _CDN_SERVERS is None or refresh:
        data = api_get("/cdn", silent=silent)
        image_servers: list[str] = [
            server.rstrip("/") for server in data.get("image_servers", []) if isinstance(server, str)
        ]
        thumb_servers: list[str] = [
            server.rstrip("/") for server in data.get("thumb_servers", []) if isinstance(server, str)
        ]

        if not image_servers or not thumb_servers:
            raise ExceptionNetUnknown("Malformed CDN server response")

        _CDN_SERVERS = {
            "image": image_servers,
            "thumb": thumb_servers,
        }

    return _CDN_SERVERS


def get_gallery_detail(hentai_id: int, silent: bool = True) -> Any:
    return api_get(f"/galleries/{hentai_id}", silent=silent)


def _ordered_servers(kind: str, path: str, refresh: bool = False) -> list[str]:
    servers: list[str] = list(get_cdn_servers(refresh=refresh).get(kind, []))
    if not servers:
        return []

    normalized_path: str = path.lstrip("/")
    start: int = sum(normalized_path.encode("utf-8")) % len(servers)
    return servers[start:] + servers[:start]


def iter_cdn_urls(path: str, kind: str, refresh: bool = False) -> list[str]:
    normalized_path: str = path.lstrip("/")
    urls: list[str] = []
    for server in _ordered_servers(kind, normalized_path, refresh=refresh):
        urls.append(f"{server}/{normalized_path}")
    return urls


def build_cdn_url(path: str, kind: str, refresh: bool = False) -> str | None:
    for url in iter_cdn_urls(path, kind, refresh=refresh):
        return url
    return None
