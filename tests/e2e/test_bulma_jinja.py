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
