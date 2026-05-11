# `page.eval()` alias does not exist on `Page` (Python Client)

**Package:** `vibium` Python client
**Version:** 26.3.18
**Platform:** macOS x86_64 (Darwin 25.3.0)
**Python:** 3.13
**Repro repo:** https://github.com/lana-20/vibium-python-test

## Summary

`page.eval()` does not exist on the Python `Page` object. The method is named `evaluate()`. The official `test_basic.py` in the vibium repository calls `vibe.eval(...)`, which raises `AttributeError` immediately.

## Steps to reproduce

```python
from vibium import browser

bro = browser.start(headless=True)
page = bro.new_page()
page.go("https://example.com")

result = page.eval("1 + 1")   # crashes
```

## Actual error

```
AttributeError: 'Page' object has no attribute 'eval'
```

## Expected behaviour

Either `page.eval()` works as an alias for `page.evaluate()`, or `test_basic.py` is corrected to call `page.evaluate()`.

## Verification

```python
hasattr(page, "eval")       # False — every page, every site
hasattr(page, "evaluate")   # True
page.evaluate("1 + 1")      # 2 — works correctly
```

Hardened across 4 sites (example.com, books.toscrape.com, httpbin.org, example.org): `eval()` absent on every page instance; `evaluate()` works on all.

## Test suite LOC

- [`test_vibium_python.py#L370-L375`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L370-L375) — `test_eval_alias_bug()` asserts `eval` absent, `evaluate` present
- [`test_vibium_python.py#L383-L384`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L383-L384) — `run_test("page.eval() alias absent …", known_bug=…)`
- [`bug_hardening.py`](https://github.com/lana-20/vibium-python-test/blob/main/bug_hardening.py) — B1 section, 12 probes

## Repro

```sh
VIBIUM_BIN_PATH=<path> python3 bug_hardening.py --headless B1
```

Expected: 8 BUG (eval absent / AttributeError), 4 OK (evaluate works).
