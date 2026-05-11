---
name: vibium-python-test
description: Run the Vibium Python API regression suite. Tests all public methods across Browser, Page, Element, BrowserContext, Keyboard, Mouse, Touch, Clock, Dialog, Route, Recording, capture.*, wait_until.*, and error types using a single-file Python runner. Labels each test PASS/FAIL/BUG/SKIP.
---

# Vibium Python API Test Suite

Tests all public methods in the vibium Python language bindings (`vibium==26.3.18`, sync API).
140 tests across 22 sections in a single self-contained runner.

## Project directory

All commands run from:
```sh
cd ~/vibium-python-test
```

## File

| File | Purpose |
|---|---|
| `test_vibium_python.py` | Regression suite — 140 tests across 22 sections |
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
| Page: Evaluation & Scripts | 6 | evaluate (number/string/object), add_script, add_style, eval() alias absent |
| Page: Screenshots & PDF | 4 | screenshot, screenshot(full_page), screenshot→file, pdf |
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
TOTAL                        140    140   0     0    0
```

## Baseline

Confirmed across multiple runs:

| Pass | Fail | Bug | Skip | Total |
|---|---|---|---|---|
| 140 | 0 | 0 | 0 | 140 |

**Bug hardening baseline:**

| Confirmed | Total probes | Unexpected |
|---|---|---|
| 68 | 107 | 0 |

Note: two daemon-thread `TimeoutError` lines print to stderr during `capture.dialog` tests. These are expected — the background `evaluate("alert(...)")` threads are cancelled when the browser stops. They do not affect test results.

## Bugs found during workout

| Bug | Method(s) | Detail |
|---|---|---|
| B1 | `page.evaluate()` alias | `test_basic.py` in the repo calls `vibe.eval()` which does not exist on Page; correct name is `evaluate()` |
| B2 | `page.wait_until(fn)` | Requires a full function expression `"() => ..."` — bare boolean expression like `"document.readyState === 'complete'"` always times out |
| B3 | `capture.dialog(fn)` deadlock | `fn` that calls `page.evaluate("alert(...)")` deadlocks: alert blocks browser until dialog is handled, but the dialog capture future hasn't been awaited yet when `fn()` is called synchronously. Fix: fire `evaluate` in a daemon thread inside `fn` |
| B4 | `element.bounds()` returns dataclass | `BoundingBox` is a Python dataclass, not a dict — `"width" in bb` raises `TypeError`; use `bb.width`, `bb.x` etc. |

## Input

If the user passes a section name (e.g. `element`, `clock`, `capture`), run the suite and highlight that section's output.
If the user passes `--headed`, omit `--headless` from the run command.
If no argument, run the full suite headless and produce the complete summary.
