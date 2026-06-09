# Improvement Plan — minq-nhentai v0.2.0

Comprehensive analysis of issues, organized by priority.

---

## 🔴 Critical (must fix)

### 1. Infinite retry loop — `net.py:14`
`while True` with no maximum retry count. Persistent server errors (sustained 429, 5xx) cause an infinite hang.

### 2. `assert` for control flow — `cache.py:58`, `image_backend.py:145`, `ui.py:52`
Using `assert` for runtime validation. Stripped by `python -O`, silently breaking these checks in optimized mode.

### 3. TOCTOU race condition — `models.py:253-256`
```python
if self.downloading_pages_in_background:
    print("Already downloading")
    return
self.downloading_pages_in_background = True
```
Two threads can both pass the check and start background downloads. Needs a `threading.Lock`.

---

## 🟠 High Priority

### 4. Race conditions in `HentaiCache`
`image_set_cached`, `image_cache`, and related methods operate on `.done` marker files without locking. Called from multiple threads (background download + UI thread).

### 5. Dead dependency: `beautifulsoup4` (and likely `lxml`)
Listed in `pyproject.toml` and `requirements.txt` but never imported anywhere. Leftover from the pre-API-migration era.

### 6. `interactive_hentai_enjoyment` too long — `app.py:37-192`
155 lines, up to 12 levels of nesting. Mixes URL building, search, input handling, rendering, and navigation.

### 7. No `requests.Session` — `net.py:16`
Every HTTP request opens a new TCP connection. Prevents connection reuse and keeps-alive.

### 8. `list[Any]` instead of concrete types — throughout
- `api.py:16`: `api_get` returns `Any`, forcing callers to `cast` or use `Any`
- `app.py:126`: `hentais: list[Any]` — should be `list[Hentai]`
- `cli.py:101`: `call_args: list[Any]` defeats type safety

### 9. `contains_tag` returns True for empty tags — `models.py:208-211`
Empty tag list treated as "contains everything," which is semantically wrong.

---

## 🟡 Medium Priority

### 10. Test coverage gaps
- `app.py`, `cli.py`, `ui.py`, `models.py` have 0% coverage
- `test_cache.py` writes to real cache dir instead of `tmp_path` (tests leave artifacts)
- `test_net.py` uses `try/except/raise AssertionError` instead of `pytest.raises`
- No integration tests

### 11. CI improvements — `.github/workflows/ci.yml`
- No pip caching (every run installs from scratch)
- No coverage reporting (no `pytest-cov`, no threshold)
- Unused `hatch` install (`pipx install hatch` then never used)
- Python 3.14 is pre-release; consider 3.13 instead

### 12. `does_page_exist` downloads full response — `net.py:55-60`
Downloads and decodes the entire response body just to check HTTP status. Should use `requests.head()`.

### 13. Mutable global state — `api.py:9`, `image_backend.py:20-22`
Module-level mutable variables (`_CDN_SERVERS`, `_image_backend_resolved`, etc.) make testing harder and aren't thread-safe.

### 14. `build_cdn_url` fetches all servers — `api.py:65-68`
Fetches and sorts all CDN servers just to return the first URL. Should short-circuit.

### 15. Poor hashing — `api.py:53`
`sum(bytes) % n` for server selection. "ab" and "ba" collide, causing uneven CDN load distribution.

### 16. Broad exception catches — `scrape.py:28`, `scrape.py:173-176`
`tag_exists` and `scrape_hentais` catch ALL exceptions, silently masking network errors, rate limits, auth failures.

---

## 🟢 Low Priority

### 17. Missing `[project.scripts]` entry point
Noted in `AUR_PLAN.md` but not yet applied. Users must run `python -m minq_nhentai`.

### 18. Stale User-Agent — `net.py:12`
`Firefox/95.0` (from 2021). May trigger bot detection.

### 19. Typo — `models.py:269`
`"prevoius page"` should be `"previous page"`.

### 20. No config file support
Users cannot set defaults (language, backend, etc.) persistently.

### 21. No ANSI color support
Terminal UI is entirely monochrome.

### 22. Duplicate command dispatch — `app.py:73-83` and `app.py:174-189`
Same `if/elif` pattern duplicated in gallery branch and search branch.

### 23. Mutating global state during render — `image_backend.py:139-161`
`render_image()` can permanently change `_image_backend_resolved` as a side effect.

### 24. `models.py` delegation boilerplate — `models.py:131-156`
10 methods that do nothing but delegate to `self.cache`. Could use `__getattr__` or direct access.

### 25. Lazy import — `app.py:56`
`from .models import Hentai` inside function body instead of module top level.

### 26. URL construction inconsistency
Mix of string concatenation (`app.py:117-122`) and `urllib.parse` (`scrape.py:55`). Fragile.

### 27. `_resolve_image_backend` dead code — `image_backend.py:101-106`
Auto-detection logic contains a second SIXEL check (line 105) that is unreachable or contradictory.

### 28. No rate limiting — `scrape.py:169-207`
No proactive rate limiting between API calls. Relies on reactive 429 handling in `net.py`.

---

## Quick Wins
- [ ] Remove dead `beautifulsoup4` / `lxml` deps
- [ ] Fix `"prevoius"` typo
- [ ] Add `max_retries` to `net.py`
- [ ] Replace `assert` with proper `if`/`raise`
- [ ] Use `requests.Session`
- [ ] Use `requests.head()` for `does_page_exist`
- [ ] Remove unused `hatch` step from CI
