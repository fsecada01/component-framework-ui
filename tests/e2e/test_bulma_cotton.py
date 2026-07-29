import re

from playwright.sync_api import expect


def test_form_field_cotton_renders(cotton_page, cotton_server_url):
    page, js_mode = cotton_page
    page.goto(f"{cotton_server_url}/form-field/")
    expect(page.locator("input[name='email']")).to_be_attached()


def test_modal_cotton_renders(cotton_page, cotton_server_url):
    page, js_mode = cotton_page
    page.goto(f"{cotton_server_url}/modal/")
    expect(page.locator(".modal")).to_be_attached()
    if js_mode == "js_on":
        expect(page.locator(".modal")).not_to_have_class(re.compile(r"is-active"))


def test_card_cotton_renders(cotton_page, cotton_server_url):
    page, js_mode = cotton_page
    page.goto(f"{cotton_server_url}/card/")
    expect(page.locator(".card")).to_be_visible()
    expect(page.locator(".card-header-title")).to_have_text("Card Title")
    expect(page.locator(".card-footer-item")).to_have_text("Card Footer")


# --- Accessibility through the real cotton compiler (#21) ------------------
#
# These pages carry no Alpine: the E2E Django server is a bare WSGIHandler and
# serves no static files. That is fine for what this half is for — proving the
# new props survive <c-vars>, which the unit tier cannot do because
# render_to_string bypasses the compiler entirely. Focus behavior is asserted
# on the JinjaX galleries, where cf_ui_alpine.js actually loads.


def test_modal_cotton_declares_dialog_semantics(cotton_page, cotton_server_url):
    page, _ = cotton_page
    page.goto(f"{cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "test-modal-title")
    expect(page.locator("#test-modal-title")).to_have_text("Test Modal")


def test_tabs_cotton_render_the_active_tab(cotton_page, cotton_server_url):
    page, _ = cotton_page
    page.goto(f"{cotton_server_url}/tabs/")
    expect(page.locator("li.is-active")).to_have_count(1)
    expect(page.locator("li.is-active [role='tab']")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_panel_cotton_honors_its_open_prop(cotton_page, cotton_server_url):
    page, _ = cotton_page
    page.goto(f"{cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).not_to_have_attribute("x-cloak", "")
    expect(page.locator('button[aria-controls="open-panel-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.locator('button[aria-controls="closed-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )
