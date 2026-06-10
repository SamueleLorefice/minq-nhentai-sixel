# Improvement Plan — minq-nhentai v0.2.0

## ✅ Done (25 items across 3 commits)

| Commit | Items | Area |
|--------|-------|------|
| `55bfceb` | 1–3 | Critical: retry limit, `assert`→`if/raise`, TOCTOU lock |
| `901f957` | 4–9 | High: dead deps, `contains_*` bug, `requests.Session`, `RLock`, app.py refactor, concrete types |
| `c0aa35d` | 10–16 | Medium: test infra, CI, HEAD request, `_BackendState`, short-circuit, hash, narrowed catches |
| `a5e9a00` | 18–19, 22–28 | Low: User-Agent, typo, delegation, URL, dead code, rate limit, lazy import |
| `abd1998` | 21 | ANSI color support via Rich library |

## 📋 Remaining

### 🔸 `[project.scripts]` entry point
Noted in `AUR_PLAN.md` but deferred — excluded from this session per instruction. Users run via `python -m minq_nhentai`.

### 🔸 Config file support
Feature: users cannot set defaults (language, backend, etc.) persistently. Out of scope for this bug-fix pass.

### 🔸 Test coverage for interactive paths
`app.py`, `cli.py`, `ui.py` still at ~0%. Test infrastructure is solid (hermetic, 33 tests) but the core interactive paths are uncovered.
