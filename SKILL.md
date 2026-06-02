---
name: vibium-python-test
description: Run the Vibium Python API regression suite. Tests all public methods across Browser, Page, Element, BrowserContext, Keyboard, Mouse, Touch, Clock, Dialog, Route, Recording, capture.*, wait_until.*, and error types using a single-file Python runner. Labels each test PASS/FAIL/BUG/SKIP.
---

# Vibium Python API Test Suite

Tests all public methods in the vibium Python language bindings (`vibium==26.5.31`, sync API).
141 tests across 22 sections in a single self-contained runner.

## Project directory

All commands run from:
```sh
cd ~/vibium-python-test
```

## File

| File | Purpose |
|---|---|
| `test_vibium_python.py` | Regression suite — 141 tests across 22 sections |
| `bug_hardening.py` | Bug hardening suite — B1–B4 across 5 sites, 107 probes |

## Environment

The vibium binary is resolved via `VIBIUM_BIN_PATH`. Set it before running:
```sh
export VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium
```

## Running

**Full suite (headless):**
```sh
VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium python3 test_vibium_python.py --headless
```

**Full suite (headed, for visual debugging):**
```sh
VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium python3 test_vibium_python.py
```

**Bug hardening suite:**
```sh
VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium python3 bug_hardening.py --headless
```

## Sections covered

| Section | Tests | Methods |
|---|---|---|
| Browser | 8 | start, stop, repr, new_page, page, pages, new_context, on_page, start(headless) |
| Page: Navigation | 7 | go, title, url, content, back, forward, reload, set_content |
| Page: Finding | 10 | find (CSS/role/text/role+text/xpath/placeholder/label/testid), find_all (CSS/role) |
| Page: Evaluation & Scripts | 6 | evaluate (number/string/object), add_script, add_style, eval() alias (v26.5.31) |
| Page: Screenshots & PDF | 5 | screenshot, screenshot(full_page), screenshot→file, screenshot large payload (B5), pdf |
| Page: Viewport & Emulation | 6 | set_viewport, viewport, emulate_media (color_scheme/reduced_motion), set_geolocation, window |
| Page: Accessibility | 2 | a11y_tree, a11y_tree(everything=True) |
| Page: Waiting | 4 | wait, wait_until.loaded, wait_until.url, wait_until(fn_string) |
| Page: Events | 8 | on_console/console_messages, on_error/errors, on_dialog (accept/dismiss/callable), on_request, on_response, remove_all_listeners |
| Page: Network / Route | 6 | route (abort/fulfill/callable/continue), unroute, set_headers |
| Page: capture.* | 8 | capture.response (fn/cm), capture.request (fn/cm), capture.navigation (fn/cm), capture.dialog (fn/cm) |
| Page: Scroll & Lifecycle | 6 | scroll (down/up), bring_to_front, close, repr, id |
| Page: Frames | 2 | main_frame, frames |
| Element API | 32 | text, inner_text, html, value, attr, get_attribute, is_visible, is_hidden, is_enabled, is_checked, is_editable, bounds, bounding_box, fill, clear, type, press, check/uncheck, select_option, hover, focus, click, dblclick, scroll_into_view, dispatch_event, screenshot, repr, find (scoped), find_all (scoped), wait_until, role, label |
| Keyboard API | 3 | type, press, down/up |
| Mouse API | 4 | move, click, down/up, wheel |
| Touch API | 1 | tap |
| Clock API | 7 | install, fast_forward, set_fixed_time, set_system_time, pause_at/resume, run_for, set_timezone |
| BrowserContext API | 8 | new_page, id, cookies, set_cookies, clear_cookies, storage, add_init_script, isolation |
| Recording API | 2 | start/stop, stop(path=file) |
| Error Types | 3 | ElementNotFoundError, TimeoutError, all error classes importable |
| Multi-page & Popups | 3 | multiple pages, on_popup, page.context |

## Reporting

Parse the runner output. Produce a result line per test:

- `PASS [test name]` — test passed
- `FAIL [test name]` — unexpected failure; include the error message
- `BUG [test name] — <bug_id>` — known bug; include the note
- `SKIP [test name]` — skipped with reason

After all sections, print a summary:
```
Section                      Tests  Pass  Fail  Bug  Skip
Browser                      8      8     0     0    0
Page: Navigation             7      7     0     0    0
...
──────────────────────────────────────────────────────
TOTAL                        141    140   1     0    0
```

## Baseline

| Version | Pass | Fail | Bug | Skip | Total |
|---|---|---|---|---|---|
| v26.3.18 | 140 | 0 | 1 | 0 | 141 |
| v26.5.31 | 141 | 0 | 0 | 0 | 141 |

**Bug hardening baseline:**

| Confirmed | Total probes | Unexpected |
|---|---|---|
| 68 | 107 | 0 |

Note: two daemon-thread `TimeoutError` lines print to stderr during `capture.dialog` tests. These are expected — the background `evaluate("alert(...)")` threads are cancelled when the browser stops. They do not affect test results.

**v26.5.31 clock guard:** `clock.*` methods now error with `clock not installed` if called before `clock.install()`. Tests that call `set_fixed_time`, `pause_at`, or `set_system_time` must call `clock.install()` first.

## Bugs found during workout

| Bug | Method(s) | v26.5.31 status | Detail |
|---|---|---|---|
| B1 | `page.eval()` alias | **FIXED** (#144/#166) | Added as alias for `evaluate()` in v26.5.31; test flipped from BUG to PASS |
| B2 | `page.wait_until(fn)` | **FIXED** (#123/#163) | Bare expressions now accepted; `"() => ..."` form still works |
| B3 | `capture.dialog(fn)` deadlock | Still present | `fn` must fire `evaluate("alert(...)")` in a daemon thread; direct call deadlocks |
| B4 | `element.bounds()` returns dataclass | **FIXED** (#147/#166) | `BoundingBox` now supports dict-style access (`bb["width"]`, `"width" in bb`) alongside attribute access |
| B5 | `page.screenshot(full_page=True)` buffer overflow | **FIXED** (#110/#166) | Large pipe messages no longer crash with `LimitOverrunError` |

## Input

If the user passes a section name (e.g. `element`, `clock`, `capture`), run the suite and highlight that section's output.
If the user passes `--headed`, omit `--headless` from the run command.
If no argument, run the full suite headless and produce the complete summary.
