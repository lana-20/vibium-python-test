#!/usr/bin/env python3
"""Vibium Python API regression test suite.

Covers: Browser, Page, Element, BrowserContext, Keyboard, Mouse, Touch, Clock,
        Dialog, Route, Recording, capture.*, wait_until.*

Run:
    VIBIUM_BIN_PATH=<path> python3 test_vibium_python.py [--headless]
"""

import os
import sys
import time
import tempfile
import traceback
import threading
from typing import Callable, Optional

HEADLESS = "--headless" in sys.argv

# ── result tracking ────────────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
BUG  = "BUG"

results: list[dict] = []


def record(label: str, status: str, note: str = "") -> None:
    results.append({"label": label, "status": status, "note": note})
    color = {"PASS": "\033[32m", "FAIL": "\033[31m", "SKIP": "\033[33m", "BUG": "\033[35m"}.get(status, "")
    reset = "\033[0m"
    suffix = f"  # {note}" if note else ""
    print(f"  [{color}{status}{reset}] {label}{suffix}")


def run_test(label: str, fn: Callable, known_bug: str = "", skip_reason: str = "") -> None:
    if skip_reason:
        record(label, SKIP, skip_reason)
        return
    try:
        fn()
        record(label, PASS)
    except AssertionError as e:
        if known_bug:
            record(label, BUG, f"{known_bug} — {e}")
        else:
            record(label, FAIL, str(e))
    except Exception as e:
        if known_bug:
            record(label, BUG, f"{known_bug} — {type(e).__name__}: {e}")
        else:
            record(label, FAIL, f"{type(e).__name__}: {e}")
            traceback.print_exc()


# ── helpers ────────────────────────────────────────────────────────────────────

def make_browser():
    from vibium import browser
    return browser.start(headless=HEADLESS)


def with_page(fn: Callable) -> None:
    """Start a browser, call fn(page), stop browser."""
    bro = make_browser()
    try:
        page = bro.new_page()
        fn(page)
    finally:
        bro.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Browser API
# ══════════════════════════════════════════════════════════════════════════════

def section_browser() -> None:
    print("\n── Browser ───────────────────────────────────────────────────────────")

    def test_start_stop():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        assert bro is not None
        bro.stop()

    def test_repr():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            assert "Browser" in repr(bro)
        finally:
            bro.stop()

    def test_new_page():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            p = bro.new_page()
            from vibium import Page
            assert isinstance(p, Page)
        finally:
            bro.stop()

    def test_page_default():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            p = bro.page()
            from vibium import Page
            assert isinstance(p, Page)
        finally:
            bro.stop()

    def test_pages_list():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            bro.new_page()
            bro.new_page()
            pages = bro.pages()
            assert len(pages) >= 2
        finally:
            bro.stop()

    def test_new_context():
        from vibium import browser, BrowserContext
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            assert isinstance(ctx, BrowserContext)
            ctx.close()
        finally:
            bro.stop()

    def test_on_page_callback():
        from vibium import browser
        created = []
        bro = browser.start(headless=HEADLESS)
        try:
            bro.on_page(lambda p: created.append(p))
            bro.new_page()
            time.sleep(0.3)
            assert len(created) >= 1
        finally:
            bro.stop()

    def test_headless_start():
        from vibium import browser
        bro = browser.start(headless=True)
        try:
            p = bro.new_page()
            p.go("https://example.com")
            assert "example" in p.url()
        finally:
            bro.stop()

    run_test("browser.start() / stop()", test_start_stop)
    run_test("browser repr", test_repr)
    run_test("browser.new_page()", test_new_page)
    run_test("browser.page() — default page", test_page_default)
    run_test("browser.pages() — list", test_pages_list)
    run_test("browser.new_context()", test_new_context)
    run_test("browser.on_page() callback", test_on_page_callback)
    run_test("browser.start(headless=True)", test_headless_start)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Page: Navigation
# ══════════════════════════════════════════════════════════════════════════════

def section_page_navigation() -> None:
    print("\n── Page: Navigation ──────────────────────────────────────────────────")

    def test_go():
        def fn(p):
            p.go("https://example.com")
            assert "example.com" in p.url()
        with_page(fn)

    def test_title():
        def fn(p):
            p.go("https://example.com")
            assert p.title() == "Example Domain"
        with_page(fn)

    def test_url():
        def fn(p):
            p.go("https://example.com")
            url = p.url()
            assert url.startswith("https://")
        with_page(fn)

    def test_content():
        def fn(p):
            p.go("https://example.com")
            html = p.content()
            assert "<html" in html.lower()
        with_page(fn)

    def test_back_forward():
        def fn(p):
            p.go("https://example.com")
            p.go("https://example.org")
            p.back()
            assert "example.com" in p.url()
            p.forward()
            assert "example.org" in p.url()
        with_page(fn)

    def test_reload():
        def fn(p):
            p.go("https://example.com")
            title_before = p.title()
            p.reload()
            assert p.title() == title_before
        with_page(fn)

    def test_set_content():
        def fn(p):
            p.set_content("<html><body><h1>Hello</h1></body></html>")
            h1 = p.find("h1")
            assert h1.text() == "Hello"
        with_page(fn)

    run_test("page.go(url)", test_go)
    run_test("page.title()", test_title)
    run_test("page.url()", test_url)
    run_test("page.content()", test_content)
    run_test("page.back() / forward()", test_back_forward)
    run_test("page.reload()", test_reload)
    run_test("page.set_content(html)", test_set_content)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Page: Finding
# ══════════════════════════════════════════════════════════════════════════════

def section_page_finding() -> None:
    print("\n── Page: Finding ─────────────────────────────────────────────────────")

    def test_find_css():
        def fn(p):
            p.go("https://example.com")
            h1 = p.find("h1")
            assert "Example Domain" in h1.text()
        with_page(fn)

    def test_find_role():
        def fn(p):
            p.go("https://example.com")
            el = p.find(role="heading")
            assert el is not None
        with_page(fn)

    def test_find_text():
        def fn(p):
            p.go("https://example.com")
            el = p.find(text="Example Domain")
            assert el is not None
        with_page(fn)

    def test_find_link_role_text():
        def fn(p):
            p.go("https://example.com")
            link = p.find(role="link", text="Learn more")
            assert link is not None
        with_page(fn)

    def test_find_all():
        def fn(p):
            p.go("https://example.com")
            els = p.find_all("p")
            assert len(els) >= 1
        with_page(fn)

    def test_find_all_role():
        def fn(p):
            p.go("https://example.com")
            headings = p.find_all(role="heading")
            assert len(headings) >= 1
        with_page(fn)

    def test_find_xpath():
        def fn(p):
            p.go("https://example.com")
            el = p.find(xpath="//h1")
            assert el is not None
        with_page(fn)

    def test_find_placeholder():
        def fn(p):
            p.set_content('<html><body><input placeholder="Search here"></body></html>')
            el = p.find(placeholder="Search here")
            assert el is not None
        with_page(fn)

    def test_find_label():
        def fn(p):
            p.set_content('<html><body><label for="x">Name</label><input id="x"></body></html>')
            el = p.find(label="Name")
            assert el is not None
        with_page(fn)

    def test_find_testid():
        def fn(p):
            p.set_content('<html><body><button data-testid="submit-btn">Go</button></body></html>')
            el = p.find(testid="submit-btn")
            assert el is not None
        with_page(fn)

    run_test("page.find(css selector)", test_find_css)
    run_test("page.find(role=)", test_find_role)
    run_test("page.find(text=)", test_find_text)
    run_test("page.find(role=, text=) — interactive element", test_find_link_role_text)
    run_test("page.find_all(css)", test_find_all)
    run_test("page.find_all(role=)", test_find_all_role)
    run_test("page.find(xpath=)", test_find_xpath)
    run_test("page.find(placeholder=)", test_find_placeholder)
    run_test("page.find(label=)", test_find_label)
    run_test("page.find(testid=)", test_find_testid)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Page: Evaluation & Scripts
# ══════════════════════════════════════════════════════════════════════════════

def section_page_eval() -> None:
    print("\n── Page: Evaluation & Scripts ────────────────────────────────────────")

    def test_evaluate_number():
        def fn(p):
            p.go("https://example.com")
            result = p.evaluate("2 + 2")
            assert result == 4, f"expected 4, got {result}"
        with_page(fn)

    def test_evaluate_string():
        def fn(p):
            p.go("https://example.com")
            title = p.evaluate("document.title")
            assert title == "Example Domain", f"got: {title}"
        with_page(fn)

    def test_evaluate_object():
        def fn(p):
            p.go("https://example.com")
            result = p.evaluate("({a: 1, b: 2})")
            assert result == {"a": 1, "b": 2}, f"got: {result}"
        with_page(fn)

    def test_add_script():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.add_script("window._testVar = 42;")
            result = p.evaluate("window._testVar")
            assert result == 42, f"expected 42, got {result}"
        with_page(fn)

    def test_add_style():
        def fn(p):
            p.set_content("<html><body><p>text</p></body></html>")
            p.add_style("p { color: red; }")
            # No assertion needed — just must not throw
        with_page(fn)

    # eval() is not in the API — evaluate() is the correct name
    def test_eval_alias_bug():
        def fn(p):
            p.go("https://example.com")
            # The existing test_basic.py uses vibe.eval() which does not exist
            assert hasattr(p, "evaluate"), "evaluate() must exist"
            assert not hasattr(p, "eval"), "eval() does NOT exist — existing test_basic.py has a bug"
        with_page(fn)

    run_test("page.evaluate() — number", test_evaluate_number)
    run_test("page.evaluate() — string", test_evaluate_string)
    run_test("page.evaluate() — object", test_evaluate_object)
    run_test("page.add_script()", test_add_script)
    run_test("page.add_style()", test_add_style)
    run_test("page.eval() alias absent (test_basic.py bug)", test_eval_alias_bug,
             known_bug="test_basic.py uses vibe.eval() which does not exist on Page")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Page: Screenshots & PDF
# ══════════════════════════════════════════════════════════════════════════════

def section_page_media() -> None:
    print("\n── Page: Screenshots & PDF ───────────────────────────────────────────")

    def test_screenshot_bytes():
        def fn(p):
            p.go("https://example.com")
            png = p.screenshot()
            assert isinstance(png, bytes)
            assert len(png) > 1000
            assert png[:4] == b"\x89PNG"
        with_page(fn)

    def test_screenshot_full_page():
        def fn(p):
            p.go("https://example.com")
            png = p.screenshot(full_page=True)
            assert isinstance(png, bytes) and len(png) > 1000
        with_page(fn)

    def test_screenshot_save():
        def fn(p):
            p.go("https://example.com")
            png = p.screenshot()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(png)
                path = f.name
            assert os.path.getsize(path) > 0
            os.unlink(path)
        with_page(fn)

    def test_pdf():
        def fn(p):
            p.go("https://example.com")
            pdf = p.pdf()
            assert isinstance(pdf, bytes)
            assert pdf[:4] == b"%PDF"
        with_page(fn)

    run_test("page.screenshot() — bytes", test_screenshot_bytes)
    run_test("page.screenshot(full_page=True)", test_screenshot_full_page)
    run_test("page.screenshot() — save to file", test_screenshot_save)
    run_test("page.pdf()", test_pdf)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Page: Viewport & Emulation
# ══════════════════════════════════════════════════════════════════════════════

def section_page_viewport() -> None:
    print("\n── Page: Viewport & Emulation ────────────────────────────────────────")

    def test_set_viewport():
        def fn(p):
            p.go("https://example.com")
            p.set_viewport({"width": 800, "height": 600})
            vp = p.viewport()
            assert vp["width"] == 800
            assert vp["height"] == 600
        with_page(fn)

    def test_viewport_get():
        def fn(p):
            p.go("https://example.com")
            vp = p.viewport()
            assert "width" in vp
            assert "height" in vp
        with_page(fn)

    def test_emulate_media():
        def fn(p):
            p.go("https://example.com")
            p.emulate_media(color_scheme="dark")
            result = p.evaluate("window.matchMedia('(prefers-color-scheme: dark)').matches")
            assert result is True
        with_page(fn)

    def test_emulate_reduced_motion():
        def fn(p):
            p.go("https://example.com")
            p.emulate_media(reduced_motion="reduce")
            result = p.evaluate("window.matchMedia('(prefers-reduced-motion: reduce)').matches")
            assert result is True
        with_page(fn)

    def test_set_geolocation():
        def fn(p):
            p.go("https://example.com")
            p.set_geolocation({"latitude": 37.7749, "longitude": -122.4194})
            # No assertion — just must not throw
        with_page(fn)

    def test_window_get():
        def fn(p):
            p.go("https://example.com")
            win = p.window()
            assert isinstance(win, dict)
        with_page(fn)

    run_test("page.set_viewport()", test_set_viewport)
    run_test("page.viewport()", test_viewport_get)
    run_test("page.emulate_media(color_scheme='dark')", test_emulate_media)
    run_test("page.emulate_media(reduced_motion='reduce')", test_emulate_reduced_motion)
    run_test("page.set_geolocation()", test_set_geolocation)
    run_test("page.window()", test_window_get)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Page: Accessibility
# ══════════════════════════════════════════════════════════════════════════════

def section_page_a11y() -> None:
    print("\n── Page: Accessibility ───────────────────────────────────────────────")

    def test_a11y_tree():
        def fn(p):
            p.go("https://example.com")
            tree = p.a11y_tree()
            assert tree is not None
        with_page(fn)

    def test_a11y_tree_everything():
        def fn(p):
            p.go("https://example.com")
            tree = p.a11y_tree(everything=True)
            assert tree is not None
        with_page(fn)

    run_test("page.a11y_tree()", test_a11y_tree)
    run_test("page.a11y_tree(everything=True)", test_a11y_tree_everything)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Page: Waiting
# ══════════════════════════════════════════════════════════════════════════════

def section_page_waiting() -> None:
    print("\n── Page: Waiting ─────────────────────────────────────────────────────")

    def test_wait():
        def fn(p):
            p.go("https://example.com")
            t0 = time.time()
            p.wait(500)
            elapsed = time.time() - t0
            assert elapsed >= 0.4, f"expected >=0.4s, got {elapsed:.2f}s"
        with_page(fn)

    def test_wait_until_loaded():
        def fn(p):
            p.go("https://example.com")
            p.wait_until.loaded()
        with_page(fn)

    def test_wait_until_url():
        def fn(p):
            p.go("https://example.com")
            p.wait_until.url("*example.com*")
        with_page(fn)

    def test_wait_until_fn():
        def fn(p):
            p.go("https://example.com")
            result = p.wait_until("() => document.readyState === 'complete'")
            assert result is not None
        with_page(fn)

    run_test("page.wait(ms)", test_wait)
    run_test("page.wait_until.loaded()", test_wait_until_loaded)
    run_test("page.wait_until.url(pattern)", test_wait_until_url)
    run_test("page.wait_until(fn_string)", test_wait_until_fn)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Page: Events
# ══════════════════════════════════════════════════════════════════════════════

def section_page_events() -> None:
    print("\n── Page: Events ──────────────────────────────────────────────────────")

    def test_on_console_collect():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.on_console()
            p.evaluate("console.log('hello from test')")
            time.sleep(0.3)
            msgs = p.console_messages()
            assert any("hello from test" in m["text"] for m in msgs), f"messages: {msgs}"
        with_page(fn)

    def test_on_error_collect():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.on_error()
            p.evaluate("throw new Error('test error')")
            time.sleep(0.3)
            errs = p.errors()
            # Errors may or may not surface depending on context
            assert isinstance(errs, list)
        with_page(fn)

    def test_on_dialog_accept():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.on_dialog("accept")
            p.evaluate("alert('hello')")
            time.sleep(0.5)
        with_page(fn)

    def test_on_dialog_dismiss():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.on_dialog("dismiss")
            p.evaluate("confirm('really?')")
            time.sleep(0.5)
        with_page(fn)

    def test_on_dialog_callable():
        captured = []
        def fn(p):
            def handler(dialog):
                captured.append(dialog.message())
                dialog.accept()
            p.set_content("<html><body></body></html>")
            p.on_dialog(handler)
            p.evaluate("alert('custom handler')")
            time.sleep(0.5)
            assert "custom handler" in captured, f"captured: {captured}"
        with_page(fn)

    def test_on_request():
        seen = []
        def fn(p):
            p.on_request(lambda req: seen.append(req.url()))
            p.go("https://example.com")
            time.sleep(0.3)
            assert any("example.com" in u for u in seen), f"seen: {seen}"
        with_page(fn)

    def test_on_response():
        seen = []
        def fn(p):
            p.on_response(lambda resp: seen.append(resp.url()))
            p.go("https://example.com")
            time.sleep(0.3)
            assert any("example.com" in u for u in seen), f"seen: {seen}"
        with_page(fn)

    def test_remove_all_listeners():
        def fn(p):
            p.set_content("<html><body></body></html>")
            p.on_console()
            p.remove_all_listeners()
            msgs = p.console_messages()
            assert msgs == []
        with_page(fn)

    run_test("page.on_console() / console_messages()", test_on_console_collect)
    run_test("page.on_error() / errors()", test_on_error_collect)
    run_test("page.on_dialog('accept')", test_on_dialog_accept)
    run_test("page.on_dialog('dismiss')", test_on_dialog_dismiss)
    run_test("page.on_dialog(callable)", test_on_dialog_callable)
    run_test("page.on_request()", test_on_request)
    run_test("page.on_response()", test_on_response)
    run_test("page.remove_all_listeners()", test_remove_all_listeners)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — Page: Network / Route
# ══════════════════════════════════════════════════════════════════════════════

def section_page_network() -> None:
    print("\n── Page: Network / Route ─────────────────────────────────────────────")

    def test_route_abort():
        def fn(p):
            p.route("**/favicon.ico", "abort")
            p.go("https://example.com")
        with_page(fn)

    def test_route_fulfill():
        def fn(p):
            p.route("https://example.com/*", {
                "status": 200,
                "content_type": "text/html",
                "body": "<html><body><h1>Mocked</h1></body></html>",
            })
            p.go("https://example.com/")
            h1 = p.find("h1")
            assert h1.text() == "Mocked", f"got: {h1.text()}"
        with_page(fn)

    def test_route_callable():
        def fn(p):
            def handler(route):
                route.fulfill(status=200, body="<html><body><h1>Handler</h1></body></html>",
                              content_type="text/html")
            p.route("https://example.com/*", handler)
            p.go("https://example.com/")
            h1 = p.find("h1")
            assert h1.text() == "Handler", f"got: {h1.text()}"
        with_page(fn)

    def test_route_continue():
        def fn(p):
            p.route("**/*", "continue")
            p.go("https://example.com")
            assert "example.com" in p.url()
        with_page(fn)

    def test_unroute():
        def fn(p):
            p.route("**/*", "abort")
            p.unroute("**/*")
            p.go("https://example.com")
            assert "example.com" in p.url()
        with_page(fn)

    def test_set_headers():
        def fn(p):
            p.set_headers({"X-Test-Header": "vibium"})
            p.go("https://example.com")
            # Header set — just must not throw
        with_page(fn)

    run_test("page.route(pattern, 'abort')", test_route_abort)
    run_test("page.route(pattern, dict fulfill)", test_route_fulfill)
    run_test("page.route(pattern, callable)", test_route_callable)
    run_test("page.route(pattern, 'continue')", test_route_continue)
    run_test("page.unroute()", test_unroute)
    run_test("page.set_headers()", test_set_headers)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — Page: capture.*
# ══════════════════════════════════════════════════════════════════════════════

def section_page_capture() -> None:
    print("\n── Page: capture.* ───────────────────────────────────────────────────")

    def test_capture_response_fn():
        def fn(p):
            result = p.capture.response("*example.com*", lambda: p.go("https://example.com"))
            assert result is not None
            assert result["status"] == 200
        with_page(fn)

    def test_capture_response_cm():
        def fn(p):
            with p.capture.response("*example.com*") as cap:
                p.go("https://example.com")
            assert cap.value is not None
            assert cap.value["status"] == 200
        with_page(fn)

    def test_capture_request_fn():
        def fn(p):
            result = p.capture.request("*example.com*", lambda: p.go("https://example.com"))
            assert result is not None
            assert "example.com" in result["url"]
        with_page(fn)

    def test_capture_request_cm():
        def fn(p):
            with p.capture.request("*example.com*") as cap:
                p.go("https://example.com")
            assert cap.value is not None
            assert "example.com" in cap.value["url"]
        with_page(fn)

    def test_capture_navigation_fn():
        def fn(p):
            p.go("https://example.com")
            url = p.capture.navigation(lambda: p.go("https://example.org"))
            assert "example.org" in url
        with_page(fn)

    def test_capture_navigation_cm():
        def fn(p):
            p.go("https://example.com")
            with p.capture.navigation() as cap:
                p.go("https://example.org")
            assert "example.org" in cap.value
        with_page(fn)

    def test_capture_dialog_fn():
        def fn(p):
            p.set_content("<html><body></body></html>")
            # Fire evaluate in a thread: alert() blocks the browser until dialog is
            # handled; if called synchronously inside capture.dialog(fn), the fn blocks
            # waiting for evaluate, but the dialog capture future hasn't been awaited yet.
            result = p.capture.dialog(
                lambda: threading.Thread(target=lambda: p.evaluate("alert('captured dialog')"), daemon=True).start()
            )
            assert result is not None
            assert result["message"] == "captured dialog"
            assert result["type"] == "alert"
        with_page(fn)

    def test_capture_dialog_cm():
        def fn(p):
            p.set_content("<html><body></body></html>")
            with p.capture.dialog() as cap:
                # Same deadlock risk: alert blocks evaluate; fire in background thread.
                threading.Thread(target=lambda: p.evaluate("alert('cm dialog')"), daemon=True).start()
                time.sleep(0.2)
            assert cap.value is not None
            assert cap.value["message"] == "cm dialog"
        with_page(fn)

    run_test("capture.response(pattern, fn)", test_capture_response_fn)
    run_test("capture.response() — context manager", test_capture_response_cm)
    run_test("capture.request(pattern, fn)", test_capture_request_fn)
    run_test("capture.request() — context manager", test_capture_request_cm)
    run_test("capture.navigation(fn)", test_capture_navigation_fn)
    run_test("capture.navigation() — context manager", test_capture_navigation_cm)
    run_test("capture.dialog(fn)", test_capture_dialog_fn)
    run_test("capture.dialog() — context manager", test_capture_dialog_cm)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — Page: Scroll & Lifecycle
# ══════════════════════════════════════════════════════════════════════════════

def section_page_misc() -> None:
    print("\n── Page: Scroll & Lifecycle ──────────────────────────────────────────")

    def test_scroll_down():
        def fn(p):
            p.go("https://example.com")
            p.scroll("down", 3)
        with_page(fn)

    def test_scroll_up():
        def fn(p):
            p.go("https://example.com")
            p.scroll("down", 5)
            p.scroll("up", 2)
        with_page(fn)

    def test_bring_to_front():
        def fn(p):
            p.go("https://example.com")
            p.bring_to_front()
        with_page(fn)

    def test_page_close():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            p1 = bro.new_page()
            p2 = bro.new_page()
            p1.go("https://example.com")
            p1.close()
            pages = bro.pages()
            assert len(pages) >= 1
        finally:
            bro.stop()

    def test_page_repr():
        def fn(p):
            p.go("https://example.com")
            r = repr(p)
            assert "Page" in r
        with_page(fn)

    def test_page_id():
        def fn(p):
            assert p.id is not None and len(p.id) > 0
        with_page(fn)

    run_test("page.scroll('down')", test_scroll_down)
    run_test("page.scroll('up')", test_scroll_up)
    run_test("page.bring_to_front()", test_bring_to_front)
    run_test("page.close()", test_page_close)
    run_test("page repr", test_page_repr)
    run_test("page.id", test_page_id)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — Page: Frames
# ══════════════════════════════════════════════════════════════════════════════

def section_page_frames() -> None:
    print("\n── Page: Frames ──────────────────────────────────────────────────────")

    IFRAME_HTML = """<html><body>
    <iframe id="f1" src="https://example.com" name="testframe"></iframe>
    </body></html>"""

    def test_main_frame():
        def fn(p):
            p.go("https://example.com")
            mf = p.main_frame()
            assert mf is not None
        with_page(fn)

    def test_frames_list():
        def fn(p):
            p.set_content(IFRAME_HTML)
            time.sleep(0.5)
            frames = p.frames()
            assert isinstance(frames, list)
        with_page(fn)

    run_test("page.main_frame()", test_main_frame)
    run_test("page.frames()", test_frames_list)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — Element API
# ══════════════════════════════════════════════════════════════════════════════

def section_element() -> None:
    print("\n── Element API ───────────────────────────────────────────────────────")

    FORM_HTML = """<html><body>
    <input id="inp" type="text" value="hello">
    <input id="chk" type="checkbox">
    <select id="sel"><option value="a">Alpha</option><option value="b">Beta</option></select>
    <button id="btn">Click me</button>
    <a href="https://example.org" id="lnk">Go there</a>
    <textarea id="ta">initial</textarea>
    <label for="inp">Name</label>
    </body></html>"""

    def test_text():
        def fn(p):
            p.set_content("<html><body><p>Hello world</p></body></html>")
            el = p.find("p")
            assert el.text() == "Hello world"
        with_page(fn)

    def test_inner_text():
        def fn(p):
            p.set_content("<html><body><div><span>inner</span></div></body></html>")
            el = p.find("div")
            assert "inner" in el.inner_text()
        with_page(fn)

    def test_html():
        def fn(p):
            p.set_content("<html><body><div><span>content</span></div></body></html>")
            el = p.find("div")
            assert "<span>" in el.html()
        with_page(fn)

    def test_value():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            assert el.value() == "hello"
        with_page(fn)

    def test_attr():
        def fn(p):
            p.set_content("<html><body><a href='https://example.com'>link</a></body></html>")
            el = p.find("a")
            href = el.attr("href")
            assert href == "https://example.com", f"got: {href}"
        with_page(fn)

    def test_get_attribute():
        def fn(p):
            p.set_content("<html><body><a href='https://example.com'>link</a></body></html>")
            el = p.find("a")
            assert el.get_attribute("href") == "https://example.com"
        with_page(fn)

    def test_is_visible():
        def fn(p):
            p.set_content("<html><body><p>visible</p></body></html>")
            el = p.find("p")
            assert el.is_visible() is True
        with_page(fn)

    def test_is_hidden():
        def fn(p):
            p.set_content('<html><body><p style="display:none">hidden</p></body></html>')
            el = p.find("p")
            assert el.is_hidden() is True
        with_page(fn)

    def test_is_enabled():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#btn")
            assert el.is_enabled() is True
        with_page(fn)

    def test_is_checked():
        def fn(p):
            p.set_content('<html><body><input type="checkbox" checked></body></html>')
            el = p.find("input[type=checkbox]")
            assert el.is_checked() is True
        with_page(fn)

    def test_is_editable():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            assert el.is_editable() is True
        with_page(fn)

    def test_bounds():
        def fn(p):
            p.go("https://example.com")
            el = p.find("h1")
            bb = el.bounds()
            assert hasattr(bb, "width") and bb.width > 0
        with_page(fn)

    def test_bounding_box():
        def fn(p):
            p.go("https://example.com")
            el = p.find("h1")
            bb = el.bounding_box()
            assert bb is not None
        with_page(fn)

    def test_fill():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            el.fill("new value")
            assert el.value() == "new value"
        with_page(fn)

    def test_clear():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            el.clear()
            assert el.value() == ""
        with_page(fn)

    def test_type():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            el.clear()
            el.type("typed")
            assert el.value() == "typed"
        with_page(fn)

    def test_press():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            el.fill("abc")
            el.press("End")
            el.press("Backspace")
            # 'ab' remains
            assert el.value() == "ab", f"got: {el.value()}"
        with_page(fn)

    def test_check_uncheck():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#chk")
            el.check()
            assert el.is_checked() is True
            el.uncheck()
            assert el.is_checked() is False
        with_page(fn)

    def test_select_option():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#sel")
            el.select_option("b")
            assert el.value() == "b"
        with_page(fn)

    def test_hover():
        def fn(p):
            p.go("https://example.com")
            el = p.find("h1")
            el.hover()
        with_page(fn)

    def test_focus():
        def fn(p):
            p.set_content(FORM_HTML)
            el = p.find("#inp")
            el.focus()
            focused = p.evaluate("document.activeElement.id")
            assert focused == "inp", f"focused: {focused}"
        with_page(fn)

    def test_click():
        clicked = []
        def fn(p):
            p.set_content('<html><body><button id="b" onclick="this.textContent=\'clicked\'">go</button></body></html>')
            el = p.find("#b")
            el.click()
            assert el.text() == "clicked", f"got: {el.text()}"
        with_page(fn)

    def test_dblclick():
        def fn(p):
            p.set_content('<html><body><div id="d" ondblclick="this.textContent=\'dbl\'">text</div></body></html>')
            el = p.find("#d")
            el.dblclick()
            assert el.text() == "dbl", f"got: {el.text()}"
        with_page(fn)

    def test_scroll_into_view():
        def fn(p):
            p.set_content("<html><body>" + "<br>" * 50 + "<p id='target'>bottom</p></body></html>")
            el = p.find("#target")
            el.scroll_into_view()
        with_page(fn)

    def test_dispatch_event():
        def fn(p):
            p.set_content('<html><body><input id="inp"></body></html>')
            el = p.find("#inp")
            el.dispatch_event("focus")
        with_page(fn)

    def test_element_screenshot():
        def fn(p):
            p.go("https://example.com")
            el = p.find("h1")
            png = el.screenshot()
            assert isinstance(png, bytes) and len(png) > 100
        with_page(fn)

    def test_element_repr():
        def fn(p):
            p.go("https://example.com")
            el = p.find("h1")
            r = repr(el)
            assert "Element" in r
        with_page(fn)

    def test_element_find_scoped():
        def fn(p):
            p.set_content("<html><body><div><span>inner</span></div></body></html>")
            div = p.find("div")
            span = div.find("span")
            assert span.text() == "inner"
        with_page(fn)

    def test_element_find_all_scoped():
        def fn(p):
            p.set_content("<html><body><ul><li>a</li><li>b</li></ul></body></html>")
            ul = p.find("ul")
            items = ul.find_all("li")
            assert len(items) == 2
        with_page(fn)

    def test_element_wait_until():
        def fn(p):
            p.set_content('<html><body><p id="el">text</p></body></html>')
            el = p.find("#el")
            el.wait_until("visible")
        with_page(fn)

    def test_element_role():
        def fn(p):
            p.set_content("<html><body><button>Go</button></body></html>")
            el = p.find("button")
            r = el.role()
            assert isinstance(r, str) and len(r) > 0
        with_page(fn)

    def test_element_label():
        def fn(p):
            p.set_content('<html><body><label for="i">Name</label><input id="i"></body></html>')
            el = p.find("#i")
            lbl = el.label()
            assert isinstance(lbl, str)
        with_page(fn)

    run_test("element.text()", test_text)
    run_test("element.inner_text()", test_inner_text)
    run_test("element.html()", test_html)
    run_test("element.value()", test_value)
    run_test("element.attr(name)", test_attr)
    run_test("element.get_attribute(name)", test_get_attribute)
    run_test("element.is_visible()", test_is_visible)
    run_test("element.is_hidden()", test_is_hidden)
    run_test("element.is_enabled()", test_is_enabled)
    run_test("element.is_checked()", test_is_checked)
    run_test("element.is_editable()", test_is_editable)
    run_test("element.bounds()", test_bounds)
    run_test("element.bounding_box()", test_bounding_box)
    run_test("element.fill()", test_fill)
    run_test("element.clear()", test_clear)
    run_test("element.type()", test_type)
    run_test("element.press()", test_press)
    run_test("element.check() / uncheck()", test_check_uncheck)
    run_test("element.select_option()", test_select_option)
    run_test("element.hover()", test_hover)
    run_test("element.focus()", test_focus)
    run_test("element.click()", test_click)
    run_test("element.dblclick()", test_dblclick)
    run_test("element.scroll_into_view()", test_scroll_into_view)
    run_test("element.dispatch_event()", test_dispatch_event)
    run_test("element.screenshot()", test_element_screenshot)
    run_test("element repr", test_element_repr)
    run_test("element.find() — scoped", test_element_find_scoped)
    run_test("element.find_all() — scoped", test_element_find_all_scoped)
    run_test("element.wait_until('visible')", test_element_wait_until)
    run_test("element.role()", test_element_role)
    run_test("element.label()", test_element_label)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 15 — Keyboard API
# ══════════════════════════════════════════════════════════════════════════════

def section_keyboard() -> None:
    print("\n── Keyboard API ──────────────────────────────────────────────────────")

    def test_keyboard_type():
        def fn(p):
            p.set_content('<html><body><input id="i" autofocus></body></html>')
            el = p.find("#i")
            el.focus()
            p.keyboard.type("hello")
            assert el.value() == "hello", f"got: {el.value()}"
        with_page(fn)

    def test_keyboard_press():
        def fn(p):
            p.set_content('<html><body><input id="i" value="abc" autofocus></body></html>')
            el = p.find("#i")
            el.focus()
            p.keyboard.press("End")
            p.keyboard.press("Backspace")
            assert el.value() == "ab", f"got: {el.value()}"
        with_page(fn)

    def test_keyboard_down_up():
        def fn(p):
            p.set_content('<html><body><input id="i" autofocus></body></html>')
            el = p.find("#i")
            el.focus()
            p.keyboard.down("Shift")
            p.keyboard.type("a")
            p.keyboard.up("Shift")
            # Shift+a gives uppercase 'A'
            assert el.value() == "A", f"got: {el.value()}"
        with_page(fn)

    run_test("keyboard.type()", test_keyboard_type)
    run_test("keyboard.press()", test_keyboard_press)
    run_test("keyboard.down() / up() — shift+key", test_keyboard_down_up)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 16 — Mouse API
# ══════════════════════════════════════════════════════════════════════════════

def section_mouse() -> None:
    print("\n── Mouse API ─────────────────────────────────────────────────────────")

    def test_mouse_move():
        def fn(p):
            p.go("https://example.com")
            p.mouse.move(100, 100)
        with_page(fn)

    def test_mouse_click_coords():
        def fn(p):
            p.set_content('<html><body><button id="b" onclick="this.textContent=\'clicked\'" style="position:absolute;top:50px;left:50px;width:100px;height:40px">go</button></body></html>')
            p.mouse.click(100, 70)
            time.sleep(0.3)
            el = p.find("#b")
            assert el.text() == "clicked", f"got: {el.text()}"
        with_page(fn)

    def test_mouse_down_up():
        def fn(p):
            p.go("https://example.com")
            p.mouse.move(200, 200)
            p.mouse.down()
            p.mouse.up()
        with_page(fn)

    def test_mouse_wheel():
        def fn(p):
            p.go("https://example.com")
            p.mouse.wheel(0, 300)
        with_page(fn)

    run_test("mouse.move(x, y)", test_mouse_move)
    run_test("mouse.click(x, y)", test_mouse_click_coords)
    run_test("mouse.down() / up()", test_mouse_down_up)
    run_test("mouse.wheel(dx, dy)", test_mouse_wheel)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 17 — Touch API
# ══════════════════════════════════════════════════════════════════════════════

def section_touch() -> None:
    print("\n── Touch API ─────────────────────────────────────────────────────────")

    def test_touch_tap():
        def fn(p):
            p.set_content('<html><body><button id="b" onclick="this.textContent=\'tapped\'" style="position:absolute;top:50px;left:50px;width:100px;height:40px">go</button></body></html>')
            p.touch.tap(100, 70)
            time.sleep(0.3)
            el = p.find("#b")
            assert el.text() == "tapped", f"got: {el.text()}"
        with_page(fn)

    run_test("touch.tap(x, y)", test_touch_tap)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 18 — Clock API
# ══════════════════════════════════════════════════════════════════════════════

def section_clock() -> None:
    print("\n── Clock API ─────────────────────────────────────────────────────────")

    def test_clock_install():
        def fn(p):
            p.go("https://example.com")
            p.clock.install(time=0)
            ts = p.evaluate("Date.now()")
            assert isinstance(ts, (int, float))
        with_page(fn)

    def test_clock_fast_forward():
        def fn(p):
            p.go("https://example.com")
            p.clock.install(time=0)
            p.clock.fast_forward(5000)
            ts = p.evaluate("Date.now()")
            assert ts >= 5000, f"got: {ts}"
        with_page(fn)

    def test_clock_set_fixed_time():
        def fn(p):
            p.go("https://example.com")
            p.clock.set_fixed_time("2025-01-01T00:00:00Z")
            ts = p.evaluate("Date.now()")
            assert ts > 0
        with_page(fn)

    def test_clock_set_system_time():
        def fn(p):
            p.go("https://example.com")
            p.clock.install(time=0)
            p.clock.set_system_time("2025-06-01T12:00:00Z")
        with_page(fn)

    def test_clock_pause_resume():
        def fn(p):
            p.go("https://example.com")
            p.clock.install(time=0)
            p.clock.pause_at(1000)
            t1 = p.evaluate("Date.now()")
            p.clock.resume()
        with_page(fn)

    def test_clock_run_for():
        def fn(p):
            p.go("https://example.com")
            p.clock.install(time=0)
            p.clock.run_for(2000)
            ts = p.evaluate("Date.now()")
            assert ts >= 2000, f"got: {ts}"
        with_page(fn)

    def test_clock_set_timezone():
        def fn(p):
            p.go("https://example.com")
            p.clock.install()
            p.clock.set_timezone("America/New_York")
        with_page(fn)

    run_test("clock.install()", test_clock_install)
    run_test("clock.fast_forward()", test_clock_fast_forward)
    run_test("clock.set_fixed_time()", test_clock_set_fixed_time)
    run_test("clock.set_system_time()", test_clock_set_system_time)
    run_test("clock.pause_at() / resume()", test_clock_pause_resume)
    run_test("clock.run_for()", test_clock_run_for)
    run_test("clock.set_timezone()", test_clock_set_timezone)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 19 — BrowserContext API
# ══════════════════════════════════════════════════════════════════════════════

def section_context() -> None:
    print("\n── BrowserContext API ────────────────────────────────────────────────")

    def test_context_new_page():
        from vibium import browser, Page
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            assert isinstance(p, Page)
            ctx.close()
        finally:
            bro.stop()

    def test_context_id():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            assert ctx.id is not None and len(ctx.id) > 0
            ctx.close()
        finally:
            bro.stop()

    def test_context_cookies():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            p.go("https://example.com")
            cookies = ctx.cookies()
            assert isinstance(cookies, list)
            ctx.close()
        finally:
            bro.stop()

    def test_context_set_cookies():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            p.go("https://example.com")
            ctx.set_cookies([{
                "name": "test_cookie",
                "value": "vibium_test",
                "domain": "example.com",
                "path": "/",
            }])
            cookies = ctx.cookies()
            names = [c.get("name") for c in cookies]
            assert "test_cookie" in names, f"cookies: {cookies}"
            ctx.close()
        finally:
            bro.stop()

    def test_context_clear_cookies():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            p.go("https://example.com")
            ctx.set_cookies([{"name": "x", "value": "y", "domain": "example.com", "path": "/"}])
            ctx.clear_cookies()
            cookies = ctx.cookies()
            assert all(c.get("name") != "x" for c in cookies)
            ctx.close()
        finally:
            bro.stop()

    def test_context_storage():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            state = ctx.storage()
            assert isinstance(state, dict)
            ctx.close()
        finally:
            bro.stop()

    def test_context_add_init_script():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            ctx.add_init_script("window.__vibium_init__ = true;")
            p = ctx.new_page()
            p.go("https://example.com")
            result = p.evaluate("window.__vibium_init__")
            assert result is True, f"got: {result}"
            ctx.close()
        finally:
            bro.stop()

    def test_context_isolation():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx1 = bro.new_context()
            ctx2 = bro.new_context()
            p1 = ctx1.new_page()
            p2 = ctx2.new_page()
            p1.go("https://example.com")
            ctx1.set_cookies([{"name": "iso", "value": "ctx1", "domain": "example.com", "path": "/"}])
            p2.go("https://example.com")
            c2 = ctx2.cookies()
            assert all(c.get("name") != "iso" for c in c2), "contexts should be isolated"
            ctx1.close()
            ctx2.close()
        finally:
            bro.stop()

    run_test("context.new_page()", test_context_new_page)
    run_test("context.id", test_context_id)
    run_test("context.cookies()", test_context_cookies)
    run_test("context.set_cookies()", test_context_set_cookies)
    run_test("context.clear_cookies()", test_context_clear_cookies)
    run_test("context.storage()", test_context_storage)
    run_test("context.add_init_script()", test_context_add_init_script)
    run_test("context isolation — two contexts", test_context_isolation)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 20 — Recording API
# ══════════════════════════════════════════════════════════════════════════════

def section_recording() -> None:
    print("\n── Recording API ─────────────────────────────────────────────────────")

    def test_recording_start_stop():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            p.go("https://example.com")
            ctx.recording.start()
            p.find("h1").scroll_into_view()
            data = ctx.recording.stop()
            assert isinstance(data, bytes) and len(data) > 0
            ctx.close()
        finally:
            bro.stop()

    def test_recording_to_file():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            ctx = bro.new_context()
            p = ctx.new_page()
            p.go("https://example.com")
            ctx.recording.start()
            p.reload()
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
                path = f.name
            ctx.recording.stop(path=path)
            assert os.path.getsize(path) > 0
            os.unlink(path)
            ctx.close()
        finally:
            bro.stop()

    run_test("recording.start() / stop()", test_recording_start_stop)
    run_test("recording.stop(path=file)", test_recording_to_file)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 21 — Error types
# ══════════════════════════════════════════════════════════════════════════════

def section_errors() -> None:
    print("\n── Error Types ───────────────────────────────────────────────────────")

    def test_element_not_found():
        from vibium.errors import ElementNotFoundError
        def fn(p):
            p.go("https://example.com")
            try:
                p.find("#does-not-exist-xyz", timeout=1000)
                assert False, "should have raised"
            except ElementNotFoundError:
                pass
        with_page(fn)

    def test_timeout_error():
        from vibium.errors import TimeoutError as VibiumTimeout
        def fn(p):
            p.go("https://example.com")
            try:
                p.wait_until("false", timeout=500)
                assert False, "should have raised"
            except VibiumTimeout:
                pass
        with_page(fn)

    def test_error_imports():
        from vibium.errors import (
            VibiumError, BiDiError, VibiumNotFoundError,
            TimeoutError, ConnectionError, ElementNotFoundError, BrowserCrashedError,
        )

    run_test("ElementNotFoundError raised on missing element", test_element_not_found)
    run_test("TimeoutError raised on wait_until timeout", test_timeout_error)
    run_test("all error classes importable", test_error_imports)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 22 — Multi-page / popup
# ══════════════════════════════════════════════════════════════════════════════

def section_multi_page() -> None:
    print("\n── Multi-page & Popups ───────────────────────────────────────────────")

    def test_multiple_pages():
        from vibium import browser
        bro = browser.start(headless=HEADLESS)
        try:
            p1 = bro.new_page()
            p2 = bro.new_page()
            p1.go("https://example.com")
            p2.go("https://example.org")
            assert "example.com" in p1.url()
            assert "example.org" in p2.url()
        finally:
            bro.stop()

    def test_on_popup():
        from vibium import browser
        popups = []
        bro = browser.start(headless=HEADLESS)
        try:
            bro.on_popup(lambda p: popups.append(p))
            main = bro.new_page()
            main.set_content('<html><body><a href="https://example.org" target="_blank" id="lnk">open</a></body></html>')
            main.find("#lnk").click()
            time.sleep(1.0)
            assert len(popups) >= 1, f"expected popup, got {len(popups)}"
        finally:
            bro.stop()

    def test_page_context_property():
        from vibium import browser, BrowserContext
        bro = browser.start(headless=HEADLESS)
        try:
            p = bro.new_page()
            ctx = p.context
            assert isinstance(ctx, BrowserContext)
        finally:
            bro.stop()

    run_test("multiple pages — independent navigation", test_multiple_pages)
    run_test("browser.on_popup() callback", test_on_popup)
    run_test("page.context — parent BrowserContext", test_page_context_property)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 70)
    print("  Vibium Python API Test Suite")
    print(f"  headless={HEADLESS}")
    print("=" * 70)

    t0 = time.time()

    section_browser()
    section_page_navigation()
    section_page_finding()
    section_page_eval()
    section_page_media()
    section_page_viewport()
    section_page_a11y()
    section_page_waiting()
    section_page_events()
    section_page_network()
    section_page_capture()
    section_page_misc()
    section_page_frames()
    section_element()
    section_keyboard()
    section_mouse()
    section_touch()
    section_clock()
    section_context()
    section_recording()
    section_errors()
    section_multi_page()

    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    total = len(results)
    counts = {s: sum(1 for r in results if r["status"] == s) for s in (PASS, FAIL, BUG, SKIP)}
    print(f"  Results: {counts[PASS]} pass  {counts[FAIL]} fail  {counts[BUG]} bug  {counts[SKIP]} skip  ({total} total, {elapsed:.1f}s)")

    if counts[FAIL]:
        print("\n  FAILURES:")
        for r in results:
            if r["status"] == FAIL:
                print(f"    - {r['label']}: {r['note']}")

    if counts[BUG]:
        print("\n  KNOWN BUGS:")
        for r in results:
            if r["status"] == BUG:
                print(f"    - {r['label']}: {r['note']}")

    print("=" * 70)
    sys.exit(0 if counts[FAIL] == 0 else 1)


if __name__ == "__main__":
    main()
