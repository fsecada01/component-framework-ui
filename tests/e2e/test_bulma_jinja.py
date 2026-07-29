import re

import pytest
from playwright.sync_api import expect


def _wait_for_alpine(page) -> None:
    """Wait for Alpine.js to initialize and remove x-cloak attributes."""
    page.wait_for_function(
        "() => window.Alpine !== undefined && document.querySelectorAll('[x-cloak]').length === 0",
        timeout=8000,
    )


def test_modal_opens_and_closes(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")

    modal = page.locator("#e2e-modal")
    if js_mode == "js_on":
        _wait_for_alpine(page)
        # Modal is closed by default — no is-active class
        expect(modal).not_to_have_class(re.compile(r"is-active"))
        # Open via the Alpine.store cf.modal API
        page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
        expect(modal).to_have_class(re.compile(r"is-active"))
        # Close via the delete button inside the modal
        modal.locator(".delete").click()
        expect(modal).not_to_have_class(re.compile(r"is-active"))
    else:
        # Without JS the element still exists in the DOM
        expect(modal).to_be_attached()


# --- Dialog semantics and focus management (#21) ---------------------------
#
# Everything below asserts where focus *is*, not which attributes are present.
# Attribute presence is covered by tests/unit/test_accessibility.py; a modal
# can carry role="dialog" and still strand the keyboard user behind it.


def test_modal_declares_dialog_semantics(jinja_page, jinja_server_url):
    """Runs in both modes — the semantics are server-rendered, not scripted."""
    page, _ = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    modal = page.locator("#e2e-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "e2e-modal-title")
    expect(page.locator("#e2e-modal-title")).to_have_text("E2E Dialog")


def test_modal_moves_focus_into_the_dialog(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    expect(page.locator("#e2e-modal")).to_have_class(re.compile(r"is-active"))
    assert page.evaluate(
        "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    ), "focus stayed behind the dialog"


def test_modal_takes_focus_even_when_the_reveal_is_late(jinja_page, jinja_server_url):
    """Regression: CI failed here while every local run passed.

    `focus()` on an element that is not rendered yet is a silent no-op — on the
    first tabbable child *and* on the `$el` fallback — so if the class that
    reveals the dialog has not been committed when focus is attempted, focus
    stays on `<body>` and the dialog is unusable. Nothing orders Alpine's
    `:class` effect against a `$watch`'s `$nextTick`, so this is a race, and a
    theme revealing behind a transition would hit it deterministically.

    Rather than reproduce the timing, this pins the dialog hidden with a rule
    that outranks `is-active`, opens it, and lifts the rule a couple of frames
    later. It runs entirely in the page so the reveal lands inside the retry
    window instead of racing the test harness's round trips.
    """
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    result = page.evaluate("""
        async () => {
            const frame = () => new Promise((r) => requestAnimationFrame(r));
            const inside = () =>
                document.getElementById('e2e-modal').contains(document.activeElement);

            const style = document.createElement('style');
            style.textContent = '#e2e-modal { display: none !important; }';
            document.head.appendChild(style);

            document.getElementById('open-modal').click();
            await frame();
            await frame();
            const whilePinned = inside();

            style.remove();
            for (let i = 0; i < 30; i++) {
                await frame();
                if (inside()) return { whilePinned, recovered: true };
            }
            return { whilePinned, recovered: false };
        }
    """)

    assert not result["whilePinned"], (
        "the dialog took focus while pinned hidden — the reveal was never "
        "actually blocked, so this test proves nothing"
    )
    assert result["recovered"], "focus never reached the revealed dialog"


def test_modal_restores_focus_to_its_trigger(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    page.locator("#e2e-modal .delete").click()
    expect(page.locator("#e2e-modal")).not_to_have_class(re.compile(r"is-active"))
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_escape_closes_the_modal(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    expect(page.locator("#e2e-modal")).to_have_class(re.compile(r"is-active"))
    page.keyboard.press("Escape")
    expect(page.locator("#e2e-modal")).not_to_have_class(re.compile(r"is-active"))
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_tab_does_not_escape_the_open_modal(jinja_page, jinja_server_url):
    """Tab past the last focusable element must wrap, not leave the dialog.

    The gallery modal has two stops (close, OK), so the loop below crosses the
    wrap point several times rather than merely staying put.
    """
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    inside = "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    seen = set()
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Tab"
        seen.add(page.evaluate("() => document.activeElement.className"))
    assert len(seen) > 1, "focus never moved — the trap is pinning, not cycling"

    for _ in range(6):
        page.keyboard.press("Shift+Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Shift+Tab"


def test_notification_dismisses(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    notification = page.locator(".notification")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(notification).to_be_visible()
        notification.locator(".delete").click()
        expect(notification).to_be_hidden()
    else:
        # Without Alpine x-show is not processed — element is present
        expect(notification).to_be_attached()


def test_panel_expands(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        # Panel card-content is hidden by default (x-cloak + x-show="open", open=false)
        panel_content = page.locator(".card-content").first
        expect(panel_content).to_be_hidden()
        # Click card-header to expand
        page.locator(".card-header").first.click()
        expect(panel_content).to_be_visible()
    else:
        # x-cloak keeps it hidden without JS — check it's in the DOM
        expect(page.locator(".card-content").first).to_be_attached()


def test_navbar_burger_toggles_menu(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        page.set_viewport_size({"width": 600, "height": 800})
        burger = page.locator(".navbar-burger")
        menu = page.locator(".navbar-menu")
        expect(menu).not_to_have_class(re.compile(r"is-active"))
        burger.click()
        expect(menu).to_have_class(re.compile(r"is-active"))
    else:
        expect(page.locator(".navbar")).to_be_visible()


def test_open_panel_is_readable_without_js(jinja_page, jinja_server_url):
    """`open` is server-rendered, so x-cloak must not hide an open panel.

    Runs in both modes: with JS, initPanel() has to keep it open rather than
    resetting to closed; without JS, the absence of x-cloak is what shows it.
    """
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("#e2e-panel-open-body")).to_be_visible()
    expect(page.locator("#e2e-panel-open-body")).to_contain_text("Visible content")


def test_panel_toggle_reports_its_state(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    closed = page.locator('button[aria-controls="e2e-panel-body"]')
    opened = page.locator('button[aria-controls="e2e-panel-open-body"]')
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(closed).to_have_attribute("aria-expanded", "false")
    expect(opened).to_have_attribute("aria-expanded", "true")


# --- Tabs: server-rendered active state (#21) ------------------------------


def test_exactly_one_tab_is_marked_active(jinja_page, jinja_server_url):
    """The js_off half is the point: without JS every tab used to look alike."""
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("li.is-active")).to_have_count(1)
    expect(page.locator("li.is-active [role='tab']")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)


def test_tabs_switch_the_active_marker_on_click(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("client-side switching requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("[role='tab']").nth(1).click()
    expect(page.locator("li.is-active")).to_have_count(1)
    expect(page.locator("li.is-active [role='tab']")).to_have_text("tab2")


def test_arrow_keys_rove_focus_across_the_tablist(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_on":
        pytest.skip("roving tabindex requires JS")
    page.goto(f"{jinja_server_url}/gallery")
    _wait_for_alpine(page)

    tabs = page.locator("[role='tab']")
    tabs.first.focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"
    # Wraps rather than dead-ending at the edge.
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab1"
    page.keyboard.press("End")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"


def test_only_the_active_tab_is_in_the_tab_order(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_form_field_renders(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    page.goto(f"{jinja_server_url}/form-field")
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator(".label")).to_have_text("Email")


def test_page_accessible_without_js(jinja_page, jinja_server_url):
    page, js_mode = jinja_page
    if js_mode != "js_off":
        pytest.skip("only runs in js_off mode")
    page.goto(f"{jinja_server_url}/gallery")
    expect(page.locator("section.section")).to_be_visible()
    expect(page.locator("body")).not_to_be_empty()
