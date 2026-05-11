#!/usr/bin/env python3
"""Vibium Python Bug Hardening Suite — B1–B4

Hardens each bug found by the regression suite across multiple sites,
page contexts, element types, and dialog variants.

Run:
    VIBIUM_BIN_PATH=<path> python3 bug_hardening.py [--headless] [B1|B2|B3|B4]
"""

import os
import sys
import time
import threading
import traceback
import multiprocessing as mp

HEADLESS = "--headless" in sys.argv
FILTER = next((a for a in sys.argv[1:] if a.startswith("B")), None)
VIBIUM_BIN_PATH = os.environ.get("VIBIUM_BIN_PATH", "")

GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

confirmed = 0
unexpected = 0
total = 0
surprises: list[str] = []


def bug(tag: str, title: str) -> None:
    width = 74
    line = f"╔══ {tag}: {title} "
    print(f"\n{line}{'═' * max(0, width - len(line))}╗\n")


def probe(idx: str, site: str, scenario: str, is_bug: bool, note: str = "") -> None:
    global confirmed, unexpected, total
    total += 1
    if is_bug:
        confirmed += 1
        status = f"{RED}BUG{RESET}"
    else:
        status = f"{GREEN}OK{RESET} "
    suffix = f"  # {note}" if note else ""
    print(f"  Probe {idx:<6} {site:<22} {scenario:<42} {status}{suffix}")


def unexpected_probe(idx: str, site: str, scenario: str, note: str = "") -> None:
    global unexpected, total
    total += 1
    unexpected += 1
    surprises.append(f"{site} / {scenario}: {note}")
    print(f"  Probe {idx:<6} {site:<22} {scenario:<42} {YELLOW}UNEXPECTED{RESET}  # {note}")


def make_browser():
    from vibium import browser
    return browser.start(headless=HEADLESS)


# ══════════════════════════════════════════════════════════════════════════════
# B1: page.eval() alias — method does not exist on Page
#
# test_basic.py in the vibium repo calls vibe.eval() which raises AttributeError.
# The correct method name is evaluate(). Hardened across multiple sites and
# page creation paths to confirm the absence is consistent.
# ══════════════════════════════════════════════════════════════════════════════

B1_SITES = [
    ("example.com",    "https://example.com"),
    ("books.toscrape", "https://books.toscrape.com"),
    ("httpbin.org",    "https://httpbin.org/html"),
    ("example.org",    "https://example.org"),
]

def harden_b1() -> None:
    bug("B1", "page.eval() alias — method does not exist on Page")

    bro = make_browser()
    try:
        n = len(B1_SITES)
        # Check 1: eval() absent via hasattr
        for i, (short, url) in enumerate(B1_SITES, 1):
            p = bro.new_page()
            try:
                p.go(url)
                absent = not hasattr(p, "eval")
                probe(f"{i}/{n*3}", short, "hasattr(page, 'eval') → False",
                      is_bug=absent,
                      note="eval() absent — test_basic.py would fail with AttributeError")
            finally:
                p.close()

        # Check 2: calling eval() raises AttributeError
        for i, (short, url) in enumerate(B1_SITES, 1):
            p = bro.new_page()
            try:
                p.go(url)
                raised = False
                try:
                    getattr(p, "eval")("1+1")
                except AttributeError:
                    raised = True
                probe(f"{n+i}/{n*3}", short, "page.eval('1+1') → AttributeError",
                      is_bug=raised,
                      note="AttributeError raised — confirms test_basic.py fails")
            finally:
                p.close()

        # Check 3: evaluate() works correctly (not a bug — context for contrast)
        for i, (short, url) in enumerate(B1_SITES, 1):
            p = bro.new_page()
            try:
                p.go(url)
                result = p.evaluate("1 + 1")
                probe(f"{n*2+i}/{n*3}", short, "page.evaluate('1+1') == 2",
                      is_bug=(result != 2),
                      note=f"evaluate() works correctly: {result}")
            finally:
                p.close()
    finally:
        bro.stop()


# ══════════════════════════════════════════════════════════════════════════════
# B2: page.wait_until(fn) — bare boolean expressions always time out
#
# wait_until() passes the string directly to vibium:page.waitForFunction.
# That command expects a JS function expression ("() => ..."), not a bare
# expression. Bare expressions like "document.readyState === 'complete'" time
# out even when already true at the point of the call.
# ══════════════════════════════════════════════════════════════════════════════

BARE_EXPRESSIONS = [
    "true",
    "1 === 1",
    "2 + 2 === 4",
    "document.readyState === 'complete'",
    "document.body !== null",
    "window.location.href.length > 0",
]

FN_EXPRESSIONS = [
    "() => true",
    "() => 1 === 1",
    "() => document.readyState === 'complete'",
    "() => document.body !== null",
]

B2_SITES = [
    ("example.com",    "https://example.com"),
    ("books.toscrape", "https://books.toscrape.com"),
    ("httpbin.org",    "https://httpbin.org/html"),
]

def harden_b2() -> None:
    bug("B2", "page.wait_until(fn) — bare expressions time out, fn expressions resolve")
    from vibium.errors import TimeoutError as VibiumTimeout

    n_bare = len(BARE_EXPRESSIONS) * len(B2_SITES)
    n_fn   = len(FN_EXPRESSIONS) * len(B2_SITES)
    n_total = n_bare + n_fn
    idx = 0

    bro = make_browser()
    try:
        print("  ── Bare expressions — expected to time out (BUG confirmed when they do) ──\n")
        for expr in BARE_EXPRESSIONS:
            for short, url in B2_SITES:
                idx += 1
                p = bro.new_page()
                try:
                    p.go(url)
                    timed_out = False
                    try:
                        p.wait_until(expr, timeout=2000)
                    except (VibiumTimeout, Exception):
                        timed_out = True
                    probe(f"{idx}/{n_total}", short, repr(expr)[:38],
                          is_bug=timed_out,
                          note="timed out — bare expression rejected (BUG)")
                finally:
                    p.close()

        print("\n  ── Function expressions — expected to resolve (BUG if they time out) ──\n")
        for expr in FN_EXPRESSIONS:
            for short, url in B2_SITES:
                idx += 1
                p = bro.new_page()
                try:
                    p.go(url)
                    resolved = False
                    try:
                        p.wait_until(expr, timeout=5000)
                        resolved = True
                    except Exception:
                        resolved = False
                    probe(f"{idx}/{n_total}", short, repr(expr)[:38],
                          is_bug=not resolved,
                          note="resolved correctly" if resolved else "timed out (unexpected)")
                finally:
                    p.close()
    finally:
        bro.stop()


# ══════════════════════════════════════════════════════════════════════════════
# B3: capture.dialog(fn) deadlock — fn calling evaluate() blocks forever
#
# capture.dialog(fn) calls fn() synchronously between setting up the dialog
# future and awaiting it. If fn() calls page.evaluate("alert(...)"), the
# browser blocks waiting for the dialog, evaluate() blocks waiting for the
# browser, and the dialog future is never submitted — deadlock.
#
# Workaround: fire evaluate() in a daemon thread so fn() returns immediately
# and the event loop can proceed to await the dialog future.
#
# Deadlock probes run in isolated subprocesses (killed after timeout) to avoid
# hanging the harness.
# ══════════════════════════════════════════════════════════════════════════════

DIALOG_VARIANTS = [
    ("alert",   "alert('deadlock test')"),
    ("confirm", "confirm('proceed?')"),
    ("prompt",  "prompt('enter value:')"),
]

B3_SITES = [
    ("example.com",    "https://example.com"),
    ("books.toscrape", "https://books.toscrape.com"),
    ("httpbin.org",    "https://httpbin.org/html"),
]

def _deadlock_worker(js: str, headless: bool, binpath: str, q: "mp.Queue") -> None:
    """Subprocess: confirm deadlock by attempting synchronous capture.dialog."""
    if binpath:
        os.environ["VIBIUM_BIN_PATH"] = binpath
    from vibium import browser
    bro = browser.start(headless=headless)
    try:
        p = bro.new_page()
        p.set_content("<html><body></body></html>")
        p.capture.dialog(lambda: p.evaluate(js))
        q.put("ok")
    except Exception as e:
        q.put(f"err:{e}")
    finally:
        try:
            bro.stop()
        except Exception:
            pass


def check_deadlock(js: str, timeout_s: float = 9.0) -> bool:
    """Returns True if capture.dialog(fn) deadlocks for the given JS."""
    q: mp.Queue = mp.Queue()
    proc = mp.Process(
        target=_deadlock_worker,
        args=(js, HEADLESS, VIBIUM_BIN_PATH, q),
        daemon=True,
    )
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.kill()
        proc.join()
        return True
    try:
        q.get_nowait()
        return False
    except Exception:
        return True


def _thread_workaround(p, js: str) -> dict | None:
    """Run capture.dialog with the fire-and-forget thread fix."""
    return p.capture.dialog(
        lambda: threading.Thread(
            target=lambda: p.evaluate(js), daemon=True
        ).start()
    )


def harden_b3() -> None:
    bug("B3", "capture.dialog(fn) deadlock — sync evaluate inside fn blocks forever")

    n_dl = len(DIALOG_VARIANTS) * len(B3_SITES)
    n_wk = len(DIALOG_VARIANTS) * len(B3_SITES)
    n_total = n_dl + n_wk
    idx = 0

    print("  ── Synchronous fn — expected to deadlock (isolated subprocess per probe) ──\n")
    for dtype, js in DIALOG_VARIANTS:
        for short, url in B3_SITES:
            idx += 1
            deadlocked = check_deadlock(js, timeout_s=9.0)
            js_short = repr(js)[:20]
            probe(f"{idx}/{n_total}", short, f"{dtype}: evaluate({js_short}…)",
                  is_bug=deadlocked,
                  note="deadlocked — dialog future never awaited (BUG)")

    print("\n  ── Thread workaround — expected to resolve ──\n")
    bro = make_browser()
    try:
        for dtype, js in DIALOG_VARIANTS:
            for short, url in B3_SITES:
                idx += 1
                p = bro.new_page()
                try:
                    p.go(url)
                    p.set_content("<html><body></body></html>")
                    # Suppress stderr: daemon thread gets "Browsing context is gone" when
                    # the page closes while evaluate() is still pending — expected noise.
                    import io
                    old_stderr, sys.stderr = sys.stderr, io.StringIO()
                    try:
                        result = _thread_workaround(p, js)
                    finally:
                        sys.stderr = old_stderr
                    ok = (
                        result is not None
                        and isinstance(result, dict)
                        and result.get("type") == dtype
                    )
                    probe(f"{idx}/{n_total}", short, f"{dtype} via daemon thread",
                          is_bug=not ok,
                          note=f"resolved: type={result.get('type')!r}, msg={result.get('message')!r}" if ok else f"failed: {result}")
                except Exception as e:
                    unexpected_probe(f"{idx}/{n_total}", short, f"{dtype} via thread", str(e))
                finally:
                    p.close()
    finally:
        bro.stop()


# ══════════════════════════════════════════════════════════════════════════════
# B4: element.bounds() returns BoundingBox dataclass, not a dict
#
# BoundingBox is a Python dataclass with fields x, y, width, height.
# Code that treats it as a dict (e.g. "width" in bb, bb["width"]) raises
# TypeError. Correct usage is bb.width, bb.x, etc.
# ══════════════════════════════════════════════════════════════════════════════

B4_SITES = [
    ("example.com",    "https://example.com",          ["h1", "p", "a"]),
    ("books.toscrape", "https://books.toscrape.com",   ["h1", "a", "p"]),
    ("httpbin.org",    "https://httpbin.org/html",     ["h1", "p"]),            # only h1 and p exist on httpbin/html
    ("testtrack.org",  "https://testtrack.org",        ["h1", "a", "p"]),
    ("example.org",    "https://example.org",          ["h1", "p", "a"]),
]

def harden_b4() -> None:
    bug("B4", "element.bounds() — BoundingBox is a dataclass, not a dict")

    from vibium._types import BoundingBox
    import dataclasses

    n_in   = sum(len(sels) for _, _, sels in B4_SITES)   # 'width' in bb probes
    n_sub  = sum(len(sels) for _, _, sels in B4_SITES)   # bb["width"] probes
    n_attr = sum(len(sels) for _, _, sels in B4_SITES)   # bb.width attr probes
    n_dc   = len(B4_SITES)                                # is dataclass probes
    n_total = n_in + n_sub + n_attr + n_dc
    idx = 0

    bro = make_browser()
    try:
        print("  ── 'width' in bb raises TypeError (BUG confirmed when True) ──\n")
        for short, url, sels in B4_SITES:
            p = bro.new_page()
            try:
                p.go(url)
                for sel in sels:
                    idx += 1
                    try:
                        el = p.find(sel, timeout=5000)
                        bb = el.bounds()
                        type_err = False
                        try:
                            _ = "width" in bb
                        except TypeError:
                            type_err = True
                        probe(f"{idx}/{n_total}", short, f"{sel}: 'width' in bb",
                              is_bug=type_err,
                              note="TypeError raised — dataclass is not iterable (BUG)")
                    except Exception as e:
                        unexpected_probe(f"{idx}/{n_total}", short,
                                         f"{sel}: 'width' in bb", str(e))
            finally:
                p.close()

        print("\n  ── bb['width'] raises TypeError (BUG confirmed when True) ──\n")
        for short, url, sels in B4_SITES:
            p = bro.new_page()
            try:
                p.go(url)
                for sel in sels:
                    idx += 1
                    try:
                        el = p.find(sel, timeout=5000)
                        bb = el.bounds()
                        type_err = False
                        try:
                            _ = bb["width"]
                        except TypeError:
                            type_err = True
                        probe(f"{idx}/{n_total}", short, f"{sel}: bb['width']",
                              is_bug=type_err,
                              note="TypeError — not subscriptable (BUG)")
                    except Exception as e:
                        unexpected_probe(f"{idx}/{n_total}", short,
                                         f"{sel}: bb['width']", str(e))
            finally:
                p.close()

        print("\n  ── bb.width / bb.height / bb.x / bb.y work correctly ──\n")
        for short, url, sels in B4_SITES:
            p = bro.new_page()
            try:
                p.go(url)
                for sel in sels:
                    idx += 1
                    try:
                        el = p.find(sel, timeout=5000)
                        bb = el.bounds()
                        ok = (
                            hasattr(bb, "width") and isinstance(bb.width, (int, float)) and
                            hasattr(bb, "height") and isinstance(bb.height, (int, float)) and
                            hasattr(bb, "x") and isinstance(bb.x, (int, float)) and
                            hasattr(bb, "y") and isinstance(bb.y, (int, float))
                        )
                        probe(f"{idx}/{n_total}", short, f"{sel}: bb.width/height/x/y",
                              is_bug=not ok,
                              note=f"w={bb.width:.0f} h={bb.height:.0f} x={bb.x:.0f} y={bb.y:.0f}" if ok else "attr missing")
                    except Exception as e:
                        unexpected_probe(f"{idx}/{n_total}", short,
                                         f"{sel}: bb attrs", str(e))
            finally:
                p.close()

        print("\n  ── isinstance(bb, BoundingBox) and dataclasses.is_dataclass(bb) ──\n")
        for short, url, sels in B4_SITES:
            idx += 1
            p = bro.new_page()
            try:
                p.go(url)
                el = p.find(sels[0], timeout=5000)
                bb = el.bounds()
                is_dc = dataclasses.is_dataclass(bb) and isinstance(bb, BoundingBox)
                probe(f"{idx}/{n_total}", short, f"is_dataclass(bb) → True",
                      is_bug=is_dc,
                      note="BoundingBox is a dataclass — dict operations fail on it (BUG)")
            except Exception as e:
                unexpected_probe(f"{idx}/{n_total}", short, "is_dataclass check", str(e))
            finally:
                p.close()

    finally:
        bro.stop()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def summary() -> None:
    print(f"\n{'═' * 76}")
    if surprises:
        print(f"  UNEXPECTED ({unexpected}):")
        for s in surprises:
            print(f"    - {s}")
    print(f"  Total confirmed: {confirmed} / {total}  unexpected: {unexpected}")
    print("═" * 76)


def main() -> None:
    print("═" * 76)
    print("  Vibium Python Bug Hardening Suite — B1–B4")
    print(f"  headless={HEADLESS}  filter={FILTER or 'all'}")
    print("═" * 76)

    t0 = time.time()
    runners = {"B1": harden_b1, "B2": harden_b2, "B3": harden_b3, "B4": harden_b4}

    for bug_id, fn in runners.items():
        if FILTER and FILTER != bug_id:
            continue
        try:
            fn()
        except Exception as e:
            print(f"\n  ERROR in {bug_id}: {e}")
            traceback.print_exc()

    elapsed = time.time() - t0
    print(f"\n  ({elapsed:.1f}s elapsed)")
    summary()


if __name__ == "__main__":
    main()
