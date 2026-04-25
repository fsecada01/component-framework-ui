import re

import pytest
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
