# `capture.dialog(fn)` deadlocks when `fn` calls `page.evaluate("alert(...)")` (Python Client)

**Package:** `vibium` Python client
**Version:** 26.3.18
**Platform:** macOS x86_64 (Darwin 25.3.0)
**Python:** 3.13
**Repro repo:** https://github.com/lana-20/vibium-python-test

## Summary

`page.capture.dialog(fn)` deadlocks permanently when `fn` calls `page.evaluate("alert(...)")` synchronously. `alert()` blocks the browser until the dialog is dismissed, but the dialog capture future is not yet awaiting at the point `fn()` is called — so the dialog is never handled, the browser never unblocks, and the process hangs forever.

The same deadlock occurs with `confirm()` and `prompt()`, and with the context-manager form `with page.capture.dialog() as cap:`.

## Steps to reproduce

```python
from vibium import browser

bro = browser.start(headless=True)
page = bro.new_page()
page.set_content("<html><body></body></html>")

# Hangs forever — never returns
result = page.capture.dialog(lambda: page.evaluate("alert('test')"))
```

## Root cause

`capture.dialog(fn)` calls `fn()` synchronously before awaiting the dialog future. `alert()` blocks the browser's event loop until the dialog is dismissed. Since the dialog capture future is not yet awaiting, the dialog is never handled — the browser waits for dismissal, `evaluate` waits for the browser, and `capture.dialog` waits for `fn` to return. Classic deadlock.

## Workaround

Fire the `evaluate` call in a daemon thread so it executes concurrently with the future being awaited:

```python
import threading

result = page.capture.dialog(
    lambda: threading.Thread(
        target=lambda: page.evaluate("alert('test')"),
        daemon=True
    ).start()
)
```

## Verification

Deadlock confirmed across 3 sites × 3 dialog types (alert / confirm / prompt) = 9 probes using isolated subprocesses with a 9-second timeout. Thread workaround resolves correctly on all 9 equivalent probes.

## Test suite LOC

- [`test_vibium_python.py#L775-L787`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L775-L787) — `test_capture_dialog_fn()` — working form (daemon thread)
- [`test_vibium_python.py#L789-L798`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L789-L798) — `test_capture_dialog_cm()` — context-manager form (daemon thread)
- [`test_vibium_python.py#L806-L807`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L806-L807) — `run_test("capture.dialog(fn)", …)` / `run_test("capture.dialog() — context manager", …)`
- [`bug_hardening.py`](https://github.com/lana-20/vibium-python-test/blob/main/bug_hardening.py) — B3 section, 18 probes (9 deadlock + 9 workaround)

## Repro

```sh
VIBIUM_BIN_PATH=<path> python3 bug_hardening.py --headless B3
```

Expected: 9 BUG (deadlocked — subprocess killed after timeout), 9 OK (daemon-thread workaround resolves).
