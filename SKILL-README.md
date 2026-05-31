# vibium-python-test

A Claude Code skill that runs the [Vibium](https://github.com/VibiumDev/vibium) Python API regression suite against `vibium==26.3.18`.

**Test repo:** [github.com/lana-20/vibium-python-test](https://github.com/lana-20/vibium-python-test)

## What it does

Runs a single-file Python test suite — no pytest, no fixtures, just `python3`. Labels each test `PASS`, `FAIL`, `BUG`, or `SKIP`, then prints a summary table.

## Coverage

141 tests across 22 sections covering the full sync API:
Browser · Page (navigation, finding, eval, screenshots, viewport, a11y, waiting, events, network, capture, scroll, frames) · Element · Keyboard · Mouse · Touch · Clock · BrowserContext · Recording · Errors · Multi-page

## Usage

```
/vibium-python-test
/vibium-python-test --headed
/vibium-python-test element
/vibium-python-test capture
```

## Baseline

140 pass / 0 fail / 1 bug / 0 skip  (141 total)
