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
        # classList membership, not a regex — "lg:flex" is always present and
        # a word-boundary pattern matches inside it.
        has_flex = "el => el.classList.contains('flex')"
        menu = page.locator(".navbar-end")
        assert menu.evaluate(has_flex) is False
        page.locator("button[aria-label='menu']").click()
        expect(menu).to_have_class(re.compile(r"\bflex\b"))
        assert menu.evaluate(has_flex) is True
    else:
        expect(page.locator(".navbar")).to_be_attached()


def test_jinja_tabs_activate(daisy_jinja_page, daisy_jinja_server_url):
    page, js_mode = daisy_jinja_page
    page.goto(f"{daisy_jinja_server_url}/gallery")
    first_tab = page.locator("[role='tab']").first

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(first_tab).not_to_have_class(re.compile(r"tab-active"))
        first_tab.click()
        expect(first_tab).to_have_class(re.compile(r"tab-active"))
    else:
        expect(first_tab).to_be_attached()


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
