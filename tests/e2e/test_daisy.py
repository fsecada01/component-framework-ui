"""DaisyUI E2E coverage (issue #6), parameterized over js_on / js_off.

The cotton half matters most: these pages render the *same* consumer templates
as the Bulma E2E server — ``tests/integration/cotton_app/templates/`` is not
duplicated or edited — through the real django-cotton compiler, with nothing
changed but ``CF_UI_THEME``. That is the acceptance criterion, executed rather
than asserted.
"""

import re

import pytest
from playwright.sync_api import expect


def _wait_for_alpine(page) -> None:
    page.wait_for_function(
        "() => window.Alpine !== undefined && document.querySelectorAll('[x-cloak]').length === 0",
        timeout=8000,
    )


# --- django-cotton: one setting, no consumer template edits ----------------


def test_cotton_form_field_renders_daisy_markup(daisy_cotton_page, daisy_cotton_server_url):
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/form-field/")
    expect(page.locator("input[name='email']")).to_be_attached()
    expect(page.locator(".form-control")).to_be_attached()
    expect(page.locator("input.input-bordered")).to_be_attached()


def test_cotton_form_field_has_no_bulma_markup(daisy_cotton_page, daisy_cotton_server_url):
    """The Bulma partial must not leak through the dispatch."""
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/form-field/")
    expect(page.locator(".field")).to_have_count(0)


def test_cotton_card_renders_daisy_markup(daisy_cotton_page, daisy_cotton_server_url):
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/card/")
    expect(page.locator(".card-body")).to_be_attached()
    expect(page.locator(".card-title")).to_have_text("Card Title")
    expect(page.locator(".card-actions")).to_contain_text("Card Footer")


def test_cotton_card_slot_survives_the_dispatch(daisy_cotton_page, daisy_cotton_server_url):
    """`{% include %}` must carry {{ slot }} into the theme partial."""
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/card/")
    expect(page.locator(".card-body")).to_contain_text("Card body content")


def test_cotton_modal_named_slot_survives_the_dispatch(daisy_cotton_page, daisy_cotton_server_url):
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/modal/")
    expect(page.locator("#test-modal .modal-box")).to_contain_text("Test Modal")
    expect(page.locator("#test-modal .modal-box")).to_contain_text("Modal body content")


def test_cotton_modal_closed_by_default(daisy_cotton_page, daisy_cotton_server_url):
    page, js_mode = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_be_attached()
    if js_mode == "js_on":
        expect(modal).not_to_have_class(re.compile(r"modal-open"))


# --- JinjaX: same Alpine contract, DaisyUI classes -------------------------


def test_jinja_modal_opens_and_closes(daisy_jinja_page, daisy_jinja_server_url):
    """cfModal is theme-independent; only the toggled class differs."""
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")

    modal = page.locator("#e2e-modal")
    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(modal).not_to_have_class(re.compile(r"modal-open"))
        page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
        expect(modal).to_have_class(re.compile(r"modal-open"))
        modal.locator("button[aria-label='close']").click()
        expect(modal).not_to_have_class(re.compile(r"modal-open"))
    else:
        expect(modal).to_be_attached()


def test_jinja_notification_dismisses(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    notification = page.locator(".alert")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(notification).to_be_visible()
        notification.locator("button[aria-label='dismiss']").click()
        expect(notification).to_be_hidden()
    else:
        expect(notification).to_be_attached()


def test_jinja_panel_expands(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    panel_body = page.locator(".card-body").first

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(panel_body).to_be_hidden()
        # Scoped to the panel's own header — the navbar burger also carries
        # aria-expanded, and it comes first in the document.
        page.locator("div.card > button").first.click()
        expect(panel_body).to_be_visible()
    else:
        expect(panel_body).to_be_attached()


def test_jinja_navbar_burger_toggles_menu(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        page.set_viewport_size({"width": 600, "height": 800})
        menu = page.locator(".navbar-end")
        # Assert the computed display, not the class list. An earlier version
        # toggled `flex` onto an element that kept `hidden`; the class list
        # changed and the menu still never appeared, because Tailwind emits
        # `hidden` after `flex`. Only computed style catches that.
        display = "el => getComputedStyle(el).display"
        assert menu.evaluate(display) == "none"
        page.locator("button[aria-label='menu']").click()
        # Not to_be_visible(): the gallery passes an empty `end` slot, so the
        # box has zero height even once it is displayed.
        assert menu.evaluate(display) != "none"
    else:
        expect(page.locator(".navbar")).to_be_attached()


def test_jinja_tabs_activate(daisy_jinja_page, daisy_jinja_server_url):
    """Clicking a tab moves the marker; the server-rendered one is the start.

    Was: assert the first tab is *not* active, click it, assert it is. That
    only held because no tab was ever active to begin with — the js_off half
    of the same test could do no better than `to_be_attached()`. The gallery
    now ships `active="tab1"`, so this asserts a move rather than a first
    appearance, and js_off has something real to check (see below).
    """
    page, js_mode = daisy_jinja_page
    if js_mode != "js_on":
        pytest.skip("covered without JS by test_jinja_exactly_one_tab_is_active")
    page.goto(f"{daisy_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    tabs = page.locator("[role='tab']")
    expect(tabs.nth(0)).to_have_class(re.compile(r"tab-active"))
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_class(re.compile(r"tab-active"))
    expect(tabs.nth(0)).not_to_have_class(re.compile(r"tab-active"))


def test_jinja_exactly_one_tab_is_active(daisy_jinja_page, daisy_jinja_server_url):
    """#21: `to_be_attached()` passed against markup that was unusable."""
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("[role='tab'].tab-active")).to_have_count(1)
    expect(page.locator("[role='tab'].tab-active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_jinja_arrow_keys_rove_focus_across_the_tablist(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    if js_mode != "js_on":
        pytest.skip("roving tabindex requires JS")
    page.goto(f"{daisy_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("[role='tab']").first.focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab1"


# --- Dialog semantics and focus management (#21) ---------------------------


def test_jinja_modal_declares_dialog_semantics(daisy_jinja_page, daisy_jinja_server_url):
    page, _ = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    modal = page.locator("#e2e-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "e2e-modal-title")


def test_jinja_modal_manages_focus(daisy_jinja_page, daisy_jinja_server_url):
    """Same Alpine contract as Bulma — the theme changes classes, not behavior."""
    page, js_mode = daisy_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{daisy_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    assert page.evaluate(
        "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    ), "focus stayed behind the dialog"
    page.keyboard.press("Escape")
    expect(page.locator("#e2e-modal")).not_to_have_class(re.compile(r"modal-open"))
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_jinja_tab_does_not_escape_the_open_modal(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{daisy_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    inside = "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Tab"


def test_jinja_open_panel_is_readable_without_js(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("#e2e-panel-open-body")).to_be_visible()


def test_jinja_panel_toggle_reports_its_state(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator('button[aria-controls="e2e-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )
    expect(page.locator('button[aria-controls="e2e-panel-open-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )


# --- django-cotton: the same contract through the real compiler ------------


def test_cotton_modal_declares_dialog_semantics(daisy_cotton_page, daisy_cotton_server_url):
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "test-modal-title")


def test_cotton_tabs_render_the_active_tab(daisy_cotton_page, daisy_cotton_server_url):
    """`active` has to survive <c-vars> — unit tests bypass that compiler."""
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/tabs/")
    expect(page.locator("[role='tab'].tab-active")).to_have_count(1)
    expect(page.locator("[role='tab'].tab-active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)


def test_cotton_panel_honors_its_open_prop(daisy_cotton_page, daisy_cotton_server_url):
    page, _ = daisy_cotton_page
    page.goto(f"{daisy_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).not_to_have_attribute("x-cloak", "")
    expect(page.locator('button[aria-controls="open-panel-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.locator('button[aria-controls="closed-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )


def test_jinja_form_field_renders(daisy_jinja_page, daisy_jinja_server_url):
    page, _ = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/form-field")
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator(".label-text")).to_have_text("Email")


def test_jinja_page_usable_without_js(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    if js_mode != "js_off":
        pytest.skip("only runs in js_off mode")
    page.goto(f"{daisy_jinja_server_url}/gallery")
    expect(page.locator("section.section")).to_be_visible()
    expect(page.locator("body")).not_to_be_empty()
