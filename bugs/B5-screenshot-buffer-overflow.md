# page.screenshot(full_page=True) overflows asyncio 64KB readline buffer, crashing connection on large PNG payloads (Python Client)

> **Status:** CLOSED — duplicate of [VibiumDev/vibium#110](https://github.com/VibiumDev/vibium/issues/110).
> Fix merged in PR #166, ships in **v26.5.31**. Reproduced on v26.3.18 (pre-fix).
> Filed as [VibiumDev/vibium#168](https://github.com/VibiumDev/vibium/issues/168).

**Package:** `vibium` Python client
**Version:** 26.3.18
**Platform:** macOS x86_64 (Darwin 25.5.0)
**Python:** 3.13
**Repro repo:** https://github.com/lana-20/vibium-python-test

## Summary

`page.screenshot(full_page=True)` raises `ConnectionError: Connection closed` when the resulting PNG payload exceeds asyncio's 64 KB `readline()` buffer. The connection is permanently corrupted — every subsequent command on any page in the same browser instance then times out. Calling `bro.stop()` afterwards raises a second error: `ValueError: Separator is not found, and chunk exceed the limit`.

Simple pages (e.g. `example.com`, basic TodoMVC at default viewport) produce PNGs under 64 KB and will NOT trigger the bug. A large viewport + `full_page=True` + a content-heavy page is needed to push the payload over the limit.

## Steps to reproduce

```python
from vibium import browser as vibium_browser

bro = vibium_browser.start(headless=True)
page = bro.new_page()
page.set_viewport({"width": 1920, "height": 1080})
page.go("https://demo.playwright.dev/todomvc")

for i in range(20):
    el = page.find(".new-todo")
    el.type(f"Todo item number {i+1} with some extra text to inflate the page")
    page.keyboard.press("Enter")

page.screenshot(full_page=True)  # ConnectionError: Connection closed
bro.stop()                        # ValueError: Separator is not found, and chunk exceed the limit
```

## Actual errors

```
ConnectionError: Connection closed              ← raised by page.screenshot()
ValueError: Separator is not found, and chunk exceed the limit  ← raised by bro.stop()
```

## Expected behaviour

`page.screenshot(full_page=True)` returns `bytes` containing a valid PNG, regardless of the payload size.

## Root cause

`vibium/client.py` → `_receive_loop` reads server responses with `await self._stdout.readline()`, which uses asyncio's default `StreamReader` buffer (64 KB hard limit). When the PNG payload exceeds 64 KB, the buffer overflows and the connection is dropped. Possible fixes:

- Switch to a length-prefixed framing protocol (`readexactly(n)`) instead of newline-delimited `readline()`
- Base64-encode the PNG and split into chunks ≤ 64 KB
- Increase the `StreamReader` limit: `asyncio.StreamReader(limit=10 * 1024 * 1024)` as a quick patch

## Impact on parallel sessions

When multiple pages share one browser instance (the correct Vibium parallel model), a single screenshot call corrupts the shared connection and kills all pages — not just the one that called screenshot.

## Workaround

Short-circuit `screenshot` in the tool dispatch layer to return a soft error without calling vibium:

```python
if name == "screenshot":
    return "FAIL: screenshot unavailable (vibium buffer limitation — skip and continue)"
```

## Test suite LOC

- [`test_vibium_python.py` — `test_screenshot_large_payload()`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py) — marked `BUG` with `known_bug="PNG payload exceeds asyncio 64KB readline limit"`

## Repro

```sh
VIBIUM_BIN_PATH=<path> python3 test_vibium_python.py --headless
```

Expected: `[BUG] page.screenshot() — large payload (>64KB buffer overflow)`
