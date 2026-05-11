# `page.wait_until()` requires full function expression — bare JS expressions always time out (Python Client)

**Package:** `vibium` Python client
**Version:** 26.3.18
**Platform:** macOS x86_64 (Darwin 25.3.0)
**Python:** 3.13
**Repro repo:** https://github.com/lana-20/vibium-python-test
**Related:** #123 (same symptom in JS client — JS workaround is `page.wait(ms)`; Python has a working form)

## Summary

`page.wait_until(expression)` always times out when passed a bare JS boolean expression. A full arrow-function expression `"() => ..."` resolves correctly. The distinction is not documented anywhere in the Python API.

## Steps to reproduce

```python
from vibium import browser

bro = browser.start(headless=True)
page = bro.new_page()
page.go("https://example.com")

# All of these time out — page is fully loaded, expression is unconditionally true
page.wait_until("true", timeout=3000)
page.wait_until("1 === 1", timeout=3000)
page.wait_until("document.readyState === 'complete'", timeout=3000)
page.wait_until("document.body !== null", timeout=3000)
```

## Actual error

```
vibium.errors.TimeoutError: timeout: timeout waiting for function to return truthy
```

## Expected behaviour

A bare boolean expression like `"document.readyState === 'complete'"` should be evaluated in the page context and resolve when truthy, just as `"() => document.readyState === 'complete'"` does.

## Working workaround

Wrap the expression in an arrow function:

```python
# These all resolve correctly
page.wait_until("() => true")
page.wait_until("() => 1 === 1")
page.wait_until("() => document.readyState === 'complete'")
page.wait_until("() => document.body !== null")
```

## Verification

Hardened across 3 sites (example.com, books.toscrape.com, httpbin.org):
- 6 bare expressions × 3 sites = 18 probes → all time out (BUG)
- 4 function expressions × 3 sites = 12 probes → all resolve (OK)

## Test suite LOC

- [`test_vibium_python.py#L550-L556`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L550-L556) — `test_wait_until_fn()` uses `"() => document.readyState === 'complete'"` (the working form)
- [`test_vibium_python.py#L560`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L560) — `run_test("page.wait_until(fn_string)", …)`
- [`test_vibium_python.py#L1573`](https://github.com/lana-20/vibium-python-test/blob/main/test_vibium_python.py#L1573) — `p.wait_until("false", timeout=500)` used to confirm `TimeoutError` is raised
- [`bug_hardening.py`](https://github.com/lana-20/vibium-python-test/blob/main/bug_hardening.py) — B2 section, 30 probes

## Repro

```sh
VIBIUM_BIN_PATH=<path> python3 bug_hardening.py --headless B2
```

Expected: 18 BUG (bare expressions time out), 12 OK (function expressions resolve).
