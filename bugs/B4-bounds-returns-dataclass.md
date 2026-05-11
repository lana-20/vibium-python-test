# `element.bounds()` returns a `BoundingBox` dataclass, not a dict — dict operations raise `TypeError` (Python Client)

**Package:** `vibium` Python client
**Version:** 26.3.18
**Platform:** macOS x86_64 (Darwin 25.3.0)
**Python:** 3.13
**Repro repo:** https://github.com/lana-20/vibium-python-test

## Summary

`element.bounds()` returns a `BoundingBox` Python dataclass, not a dictionary. Code that treats the return value as a dict raises `TypeError` at runtime. The return type is not documented, and the natural assumption for a bounding-box object is a dict (matching JSON and other browser automation APIs).

## Steps to reproduce

```python
from vibium import browser

bro = browser.start(headless=True)
page = bro.new_page()
page.go("https://example.com")
el = page.find("h1")
bb = el.bounds()

# All of these raise TypeError
"width" in bb    # TypeError: argument of type 'BoundingBox' is not iterable
bb["width"]      # TypeError: 'BoundingBox' object is not subscriptable
```

## Actual errors

```
TypeError: argument of type 'BoundingBox' is not iterable    # for `"width" in bb`
TypeError: 'BoundingBox' object is not subscriptable         # for `bb["width"]`
```

## Expected behaviour

Either:
- `bounds()` returns a plain dict `{"x": …, "y": …, "width": …, "height": …}` consistent with other browser automation libraries, or
- the return type is clearly documented as a dataclass with attribute access

## Working form

Access fields as attributes:

```python
bb = el.bounds()
bb.x       # float
bb.y       # float
bb.width   # float
bb.height  # float
```

Confirm the type:

```python
import dataclasses
dataclasses.is_dataclass(bb)   # True
```

## Verification

Hardened across 5 sites (example.com, books.toscrape.com, httpbin.org, testtrack.org, example.org) with 3 element types each (h1, p, a/varies):
- `"width" in bb` → TypeError on all 14 element/site combinations (BUG)
- `bb["width"]` → TypeError on all 14 combinations (BUG)
- `bb.width` / `bb.height` / `bb.x` / `bb.y` → correct float values on all 14 (OK)
- `dataclasses.is_dataclass(bb)` → `True` on all 5 sites (BUG confirmed)

## Test suite LOC

- [`test_vibium_python.py#L994-L1000`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L994-L1000) — `test_bounds()` asserts `hasattr(bb, "width") and bb.width > 0`
- [`test_vibium_python.py#L1177`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L1177) — `run_test("element.bounds()", …)`
- [`bug_hardening.py`](https://github.com/lana-20/vibium-python-test/blob/main/bug_hardening.py) — B4 section, 47 probes

## Repro

```sh
VIBIUM_BIN_PATH=<path> python3 bug_hardening.py --headless B4
```

Expected: 28 BUG (`in` and subscript both raise TypeError) + 5 BUG (is_dataclass confirms), 14 OK (attribute access works).
