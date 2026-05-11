# vibium-python-test

Vibium Python API regression suite for [`vibium==26.3.18`](https://github.com/VibiumDev/vibium). Single-file runner, no test framework required — just Python 3.9+.

## File

| File | Description |
|---|---|
| `test_vibium_python.py` | Full API regression suite — 140 tests across 22 sections |

## Requirements

- Python 3.9+
- `vibium` package: `pip install vibium`

## Run

```sh
VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium \
  python3 test_vibium_python.py --headless
```

Omit `--headless` to run headed (visible browser).

`VIBIUM_BIN_PATH` is optional if the vibium binary is on `PATH` or installed via pip platform package.

## Coverage

140 tests across 22 sections:

| Section | Tests | Key methods |
|---|---|---|
| Browser | 8 | `start`, `stop`, `new_page`, `page`, `pages`, `new_context`, `on_page` |
| Page: Navigation | 7 | `go`, `title`, `url`, `content`, `back`, `forward`, `reload`, `set_content` |
| Page: Finding | 10 | `find` (CSS / role / text / role+text / xpath / placeholder / label / testid), `find_all` |
| Page: Evaluation & Scripts | 6 | `evaluate`, `add_script`, `add_style` |
| Page: Screenshots & PDF | 4 | `screenshot`, `screenshot(full_page)`, `pdf` |
| Page: Viewport & Emulation | 6 | `set_viewport`, `viewport`, `emulate_media`, `set_geolocation`, `window` |
| Page: Accessibility | 2 | `a11y_tree`, `a11y_tree(everything=True)` |
| Page: Waiting | 4 | `wait`, `wait_until.loaded`, `wait_until.url`, `wait_until(fn)` |
| Page: Events | 8 | `on_console`, `on_error`, `on_dialog`, `on_request`, `on_response`, `remove_all_listeners` |
| Page: Network / Route | 6 | `route` (abort / fulfill / callable / continue), `unroute`, `set_headers` |
| Page: capture.* | 8 | `capture.response`, `capture.request`, `capture.navigation`, `capture.dialog` (fn + context manager) |
| Page: Scroll & Lifecycle | 6 | `scroll`, `bring_to_front`, `close`, `id` |
| Page: Frames | 2 | `main_frame`, `frames` |
| Element API | 32 | `text`, `inner_text`, `html`, `value`, `attr`, `bounds`, `bounding_box`, `fill`, `clear`, `type`, `press`, `click`, `dblclick`, `check`, `uncheck`, `select_option`, `hover`, `focus`, `scroll_into_view`, `dispatch_event`, `screenshot`, `find`, `find_all`, `wait_until`, `role`, `label`, `is_*` |
| Keyboard API | 3 | `type`, `press`, `down` / `up` |
| Mouse API | 4 | `move`, `click`, `down` / `up`, `wheel` |
| Touch API | 1 | `tap` |
| Clock API | 7 | `install`, `fast_forward`, `set_fixed_time`, `set_system_time`, `pause_at` / `resume`, `run_for`, `set_timezone` |
| BrowserContext API | 8 | `new_page`, `id`, `cookies`, `set_cookies`, `clear_cookies`, `storage`, `add_init_script`, isolation |
| Recording API | 2 | `start` / `stop`, `stop(path=file)` |
| Error Types | 3 | `ElementNotFoundError`, `TimeoutError`, all error classes importable |
| Multi-page & Popups | 3 | multiple pages, `on_popup`, `page.context` |

## Baseline

```
Results: 140 pass  0 fail  0 bug  0 skip  (140 total)
```

## Bugs found

| # | Method(s) | Detail |
|---|---|---|
| B1 | `page.evaluate()` alias | `test_basic.py` in the vibium repo calls `vibe.eval()` — method does not exist; correct name is `evaluate()` |
| B2 | `page.wait_until(fn)` | Requires a full JS function expression `"() => ..."` — a bare boolean expression always times out |
| B3 | `capture.dialog(fn)` deadlock | `fn` calling `page.evaluate("alert(...)")` deadlocks: `alert()` blocks the browser until the dialog is handled, but the dialog capture future isn't awaited yet when `fn()` is called synchronously. Fix: fire `evaluate` in a daemon thread inside `fn` |
| B4 | `element.bounds()` | Returns a `BoundingBox` dataclass, not a dict — `"width" in bb` raises `TypeError`; use `bb.width`, `bb.x` etc. |
