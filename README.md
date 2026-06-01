# vibium-python-test

Vibium Python API regression suite for [`vibium==26.3.18`](https://github.com/VibiumDev/vibium). Single-file runner, no test framework required — just Python 3.9+.

## File

| File | Description |
|---|---|
| `test_vibium_python.py` | Full API regression suite — 141 tests across 22 sections |

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

141 tests across 22 sections:

| Section | Tests | Key methods |
|---|---|---|
| Browser | 8 | `start`, `stop`, `new_page`, `page`, `pages`, `new_context`, `on_page` |
| Page: Navigation | 7 | `go`, `title`, `url`, `content`, `back`, `forward`, `reload`, `set_content` |
| Page: Finding | 10 | `find` (CSS / role / text / role+text / xpath / placeholder / label / testid), `find_all` |
| Page: Evaluation & Scripts | 6 | `evaluate`, `add_script`, `add_style` |
| Page: Screenshots & PDF | 5 | `screenshot`, `screenshot(full_page)`, `screenshot→file`, `screenshot large payload (B5)`, `pdf` |
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
Results: 140 pass  0 fail  1 bug  0 skip  (141 total)
```

## Files

```
~/vibium-python-test/
├── test_vibium_python.py   # full regression suite
├── bug_hardening.py        # bug hardening suite — B1–B4 across 5 sites (68/107 confirmed)
├── SKILL.md                # Claude Code skill definition
├── SKILL-README.md         # skill description
└── README.md               # this file
```

## Bug hardening

```sh
VIBIUM_BIN_PATH=/usr/local/lib/node_modules/vibium/node_modules/@vibium/darwin-x64/bin/vibium \
  python3 bug_hardening.py --headless
```

Hardens B1–B4 across 5 sites with multiple element types and dialog variants:

```
Total confirmed: 68 / 107  unexpected: 0
```

## Installation (skill)

```sh
git clone https://github.com/lana-20/vibium-python-test ~/vibium-python-test
mkdir -p ~/.claude/skills/vibium-python-test
cp ~/vibium-python-test/SKILL.md ~/.claude/skills/vibium-python-test/
```

Then add to `~/.claude/CLAUDE.md`:
```
- `/vibium-python-test` — Vibium Python API regression suite (141 tests)
```

## Usage

```
/vibium-python-test              # run full suite headless
/vibium-python-test --headed     # run with visible browser
/vibium-python-test element      # highlight Element section
/vibium-python-test capture      # highlight capture.* section
```

## Bugs found

| # | Method(s) | Detail |
|---|---|---|
| B1 | `page.evaluate()` alias | `test_basic.py` in the vibium repo calls `vibe.eval()` — method does not exist; correct name is `evaluate()` |
| B2 | `page.wait_until(fn)` | Requires a full JS function expression `"() => ..."` — a bare boolean expression always times out |
| B3 | `capture.dialog(fn)` deadlock | `fn` calling `page.evaluate("alert(...)")` deadlocks: `alert()` blocks the browser until the dialog is handled, but the dialog capture future isn't awaited yet when `fn()` is called synchronously. Fix: fire `evaluate` in a daemon thread inside `fn` |
| B4 | `element.bounds()` | Returns a `BoundingBox` dataclass, not a dict — `"width" in bb` raises `TypeError`; use `bb.width`, `bb.x` etc. |
| B5 | `page.screenshot(full_page=True)` | PNG payload exceeds asyncio's 64KB `readline()` buffer → `ConnectionError: Connection closed`; `bro.stop()` then raises `ValueError`. Requires large viewport + full-page + content-heavy page. Duplicate of [#110](https://github.com/VibiumDev/vibium/issues/110); fix in v26.5.31. [#168](https://github.com/VibiumDev/vibium/issues/168) (closed) |
