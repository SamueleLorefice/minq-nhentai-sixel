import json
import urllib.parse

from .constants import API_BASE
from .errors import ExceptionNetUnknown
from .net import receive

_CDN_SERVERS = None


def api_get(path, params=None, silent=False):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return json.loads(receive(url, silent=silent))


def get_cdn_servers(refresh=False, silent=True):
    global _CDN_SERVERS

    if _CDN_SERVERS is None or refresh:
        data = api_get("/cdn", silent=silent)
        image_servers = [server.rstrip("/") for server in data.get("image_servers", []) if isinstance(server, str)]
        thumb_servers = [server.rstrip("/") for server in data.get("thumb_servers", []) if isinstance(server, str)]

        if not image_servers or not thumb_servers:
            raise ExceptionNetUnknown("Malformed CDN server response")

        _CDN_SERVERS = {
            "image": image_servers,
            "thumb": thumb_servers,
        }

    return _CDN_SERVERS


def get_gallery_detail(hentai_id, silent=True):
    return api_get(f"/galleries/{hentai_id}", silent=silent)


def _ordered_servers(kind, path, refresh=False):
    servers = list(get_cdn_servers(refresh=refresh).get(kind, []))
    if not servers:
        return []

    normalized_path = path.lstrip("/")
    start = sum(normalized_path.encode("utf-8")) % len(servers)
    return servers[start:] + servers[:start]


def iter_cdn_urls(path, kind, refresh=False):
    normalized_path = path.lstrip("/")
    for server in _ordered_servers(kind, normalized_path, refresh=refresh):
        yield f"{server}/{normalized_path}"


def build_cdn_url(path, kind, refresh=False):
    for url in iter_cdn_urls(path, kind, refresh=refresh):
        return url
    return None

