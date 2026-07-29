"""Fomantic UI E2E coverage (issue #24), parameterized over js_on / js_off.

Two claims this tier exists to execute rather than assert:

* The **same consumer templates** as the Bulma and DaisyUI E2E servers —
  ``tests/integration/cotton_app/templates/`` is not duplicated or edited —
  render under ``CF_UI_THEME="fomantic"``.
* **No jQuery reaches the browser.** Fomantic's Modal, Tab, Accordion and
  Dropdown are jQuery plugins, and this theme deliberately loads none of them:
  Alpine drives every one of those behaviours, exactly as it does for the other
  themes. ``test_no_jquery_reaches_the_browser`` checks the delivered page and
  the live ``window`` object, not the templates — the templates are checked in
  ``tests/unit/jinja/test_fomantic.py``.
"""

import re

import pytest
from playwright.sync_api import expect


def _wait_for_alpine(page) -> None:
    page.wait_for_function(
        "() => window.Alpine !== undefined && document.querySelectorAll('[x-cloak]').length === 0",
        timeout=8000,
    )


def _wait_for_modal_focus(page) -> None:
    """Wait for the dialog to actually hold focus — see the Bulma suite.

    `_focusFirst` retries across animation frames, so a one-shot read of
    `document.activeElement` right after the reveal is a race that only a slow
    machine loses.
    """
    page.wait_for_function(
        "() => document.getElementById('e2e-modal').contains(document.activeElement)",
        timeout=5000,
    )


# --- The architectural constraint, executed --------------------------------


def test_no_jquery_reaches_the_browser(fomantic_jinja_page, fomantic_jinja_server_url):
    """A theme choice must not change a consuming app's dependency graph."""
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")

    html = page.content().lower()
    assert "jquery" not in html
    assert "semantic.min.js" not in html
    assert "semantic.js" not in html

    if js_mode == "js_on":
        _wait_for_alpine(page)
        assert page.evaluate("() => typeof window.jQuery") == "undefined"
        assert page.evaluate("() => typeof window.$") == "undefined"


def test_cotton_pages_ship_no_jquery_either(fomantic_cotton_page, fomantic_cotton_server_url):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/modal/")
    assert "jquery" not in page.content().lower()


# --- django-cotton: one setting, no consumer template edits ----------------


def test_cotton_form_field_renders_fomantic_markup(
    fomantic_cotton_page, fomantic_cotton_server_url
):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/form-field/")
    expect(page.locator("input[name='email']")).to_be_attached()
    expect(page.locator(".ui.form")).to_be_attached()
    expect(page.locator(".ui.fluid.input")).to_be_attached()


def test_cotton_form_field_has_no_bulma_or_daisy_markup(
    fomantic_cotton_page, fomantic_cotton_server_url
):
    """Neither shipped partial may leak through the dispatch."""
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/form-field/")
    expect(page.locator(".control")).to_have_count(0)
    expect(page.locator(".form-control")).to_have_count(0)


def test_cotton_card_renders_fomantic_markup(fomantic_cotton_page, fomantic_cotton_server_url):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/card/")
    expect(page.locator(".ui.card")).to_be_attached()
    expect(page.locator(".ui.card .header")).to_have_text("Card Title")
    expect(page.locator(".ui.card .extra.content")).to_contain_text("Card Footer")


def test_cotton_card_slot_survives_the_dispatch(fomantic_cotton_page, fomantic_cotton_server_url):
    """`{% include %}` must carry {{ slot }} into the theme partial."""
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/card/")
    expect(page.locator(".ui.card .description")).to_contain_text("Card body content")


def test_cotton_modal_named_slot_survives_the_dispatch(
    fomantic_cotton_page, fomantic_cotton_server_url
):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/modal/")
    expect(page.locator("#test-modal .ui.modal")).to_contain_text("Test Modal")
    expect(page.locator("#test-modal .ui.modal")).to_contain_text("Modal body content")


def test_cotton_modal_closed_by_default(fomantic_cotton_page, fomantic_cotton_server_url):
    page, js_mode = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_be_attached()
    if js_mode == "js_on":
        expect(modal).not_to_have_class(re.compile(r"\bactive\b"))


def test_cotton_modal_declares_dialog_semantics(fomantic_cotton_page, fomantic_cotton_server_url):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "test-modal-title")


def test_cotton_tabs_render_the_active_tab(fomantic_cotton_page, fomantic_cotton_server_url):
    """`active` has to survive <c-vars> — unit tests bypass that compiler."""
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/tabs/")
    expect(page.locator("[role='tab'].active")).to_have_count(1)
    expect(page.locator("[role='tab'].active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)


def test_cotton_panel_honors_its_open_prop(fomantic_cotton_page, fomantic_cotton_server_url):
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).not_to_have_attribute("x-cloak", "")
    expect(page.locator('button[aria-controls="open-panel-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.locator('button[aria-controls="closed-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )


def test_cotton_open_panel_is_readable_without_js(fomantic_cotton_page, fomantic_cotton_server_url):
    """`.ui.accordion .title~.content:not(.active)` would hide it permanently.

    The cotton gallery pages load no Alpine at all, so this is the pure-CSS
    path in both js modes: `active` from the server reveals the open panel,
    `x-cloak` plus the same `:not(.active)` rule keeps the closed one hidden.
    """
    page, _ = fomantic_cotton_page
    page.goto(f"{fomantic_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).to_be_visible()
    expect(page.locator("#closed-panel-body")).to_be_hidden()


# --- JinjaX: same Alpine contract, Fomantic classes ------------------------


def test_jinja_modal_opens_and_closes(fomantic_jinja_page, fomantic_jinja_server_url):
    """cfModal is theme-independent; only the toggled class differs.

    Fomantic normally gets `.active` from `$('.ui.modal').modal('show')`. Here
    the dimmer and the modal both take it from the same Alpine `open`.
    """
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")

    modal = page.locator("#e2e-modal")
    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(modal).not_to_have_class(re.compile(r"\bactive\b"))
        page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
        expect(modal).to_have_class(re.compile(r"\bactive\b"))
        expect(page.locator("#e2e-modal .ui.modal")).to_have_class(re.compile(r"\bactive\b"))
        modal.locator("button[aria-label='close']").click()
        expect(modal).not_to_have_class(re.compile(r"\bactive\b"))
    else:
        expect(modal).to_be_attached()


def test_jinja_modal_is_actually_visible_when_open(fomantic_jinja_page, fomantic_jinja_server_url):
    """Both `.ui.dimmer` and `.ui.modal` are display:none until `.active`.

    Asserting the class alone would pass against markup that never appears —
    which is the failure the accessibility phase called out.
    """
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("reveal requires JS")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    box = page.locator("#e2e-modal .ui.modal")
    expect(box).to_be_hidden()
    page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
    expect(box).to_be_visible()


def test_jinja_modal_declares_dialog_semantics(fomantic_jinja_page, fomantic_jinja_server_url):
    page, _ = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    modal = page.locator("#e2e-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "e2e-modal-title")


def test_jinja_modal_manages_focus(fomantic_jinja_page, fomantic_jinja_server_url):
    """Same Alpine contract as Bulma — the theme changes classes, not behavior."""
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    page.keyboard.press("Escape")
    expect(page.locator("#e2e-modal")).not_to_have_class(re.compile(r"\bactive\b"))
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_jinja_tab_does_not_escape_the_open_modal(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    inside = "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Tab"


def test_jinja_notification_dismisses(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    notification = page.locator(".ui.message")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(notification).to_be_visible()
        notification.locator("button[aria-label='dismiss']").click()
        expect(notification).to_be_hidden()
    else:
        expect(notification).to_be_attached()


def test_jinja_panel_expands(fomantic_jinja_page, fomantic_jinja_server_url):
    """Fomantic's accordion is a jQuery module; Alpine drives this one."""
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    panel_body = page.locator("#e2e-panel-body")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(panel_body).to_be_hidden()
        page.locator('button[aria-controls="e2e-panel-body"]').click()
        expect(panel_body).to_be_visible()
    else:
        expect(panel_body).to_be_attached()


def test_jinja_open_panel_is_readable_without_js(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("#e2e-panel-open-body")).to_be_visible()


def test_jinja_panel_toggle_reports_its_state(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator('button[aria-controls="e2e-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )
    expect(page.locator('button[aria-controls="e2e-panel-open-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )


def test_jinja_navbar_toggle_reports_its_state(fomantic_jinja_page, fomantic_jinja_server_url):
    """`ui stackable menu` does the responsive layout in CSS; the toggle owns
    the state and reports it, because Fomantic's collapse is a JS module."""
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("state toggle requires JS")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    burger = page.locator("button[aria-label='menu']")
    expect(burger).to_have_attribute("aria-expanded", "false")
    burger.click()
    expect(burger).to_have_attribute("aria-expanded", "true")
    expect(burger).to_have_class(re.compile(r"\bactive\b"))


def test_jinja_tabs_activate(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("covered without JS by test_jinja_exactly_one_tab_is_active")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    tabs = page.locator("[role='tab']")
    expect(tabs.nth(0)).to_have_class(re.compile(r"\bactive\b"))
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_class(re.compile(r"\bactive\b"))
    expect(tabs.nth(0)).not_to_have_class(re.compile(r"\bactive\b"))


def test_jinja_exactly_one_tab_is_active(fomantic_jinja_page, fomantic_jinja_server_url):
    """#21: `to_be_attached()` passed against markup that was unusable."""
    page, js_mode = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("[role='tab'].active")).to_have_count(1)
    expect(page.locator("[role='tab'].active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_jinja_arrow_keys_rove_focus_across_the_tablist(
    fomantic_jinja_page, fomantic_jinja_server_url
):
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_on":
        pytest.skip("roving tabindex requires JS")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("[role='tab']").first.focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab1"


def test_jinja_form_field_renders(fomantic_jinja_page, fomantic_jinja_server_url):
    page, _ = fomantic_jinja_page
    page.goto(f"{fomantic_jinja_server_url}/form-field")
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator(".ui.form label")).to_have_text("Email")


def test_jinja_page_usable_without_js(fomantic_jinja_page, fomantic_jinja_server_url):
    page, js_mode = fomantic_jinja_page
    if js_mode != "js_off":
        pytest.skip("only runs in js_off mode")
    page.goto(f"{fomantic_jinja_server_url}/gallery")
    expect(page.locator("section.section")).to_be_visible()
    expect(page.locator("body")).not_to_be_empty()
