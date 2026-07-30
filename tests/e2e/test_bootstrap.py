"""Bootstrap 5 E2E coverage (issue #22), parameterized over js_on / js_off.

Two claims this tier exists to execute rather than assert:

* The cotton pages render the *same* consumer templates as the Bulma and
  DaisyUI E2E servers — ``tests/integration/cotton_app/templates/`` is neither
  duplicated nor edited — through the real django-cotton compiler, with nothing
  changed but ``CF_UI_THEME``.
* The behaviour is Alpine's, not Bootstrap's. No ``bootstrap.bundle.js`` is
  loaded anywhere, so every open/close/switch below is proof that
  ``cf_ui_alpine.js`` drives Bootstrap markup unaided.
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


# --- No Bootstrap JavaScript anywhere on the page --------------------------


def test_jinja_page_loads_no_bootstrap_javascript(bootstrap_jinja_page, bootstrap_jinja_server_url):
    """Two state owners for `open` is the failure this theme is shaped around."""
    page, _ = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    srcs = page.eval_on_selector_all("script[src]", "els => els.map(e => e.src)")
    assert not [s for s in srcs if "bootstrap" in s]
    expect(page.locator("[data-bs-toggle]")).to_have_count(0)


def test_cotton_page_loads_no_bootstrap_javascript(
    bootstrap_cotton_page, bootstrap_cotton_server_url
):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/modal/")
    expect(page.locator("[data-bs-toggle]")).to_have_count(0)
    expect(page.locator("[data-bs-dismiss]")).to_have_count(0)


# --- django-cotton: one setting, no consumer template edits ----------------


def test_cotton_form_field_renders_bootstrap_markup(
    bootstrap_cotton_page, bootstrap_cotton_server_url
):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/form-field/")
    expect(page.locator("input[name='email']")).to_be_attached()
    expect(page.locator("input.form-control")).to_be_attached()
    expect(page.locator("label.form-label")).to_have_text("Email")


def test_cotton_form_field_has_no_bulma_markup(bootstrap_cotton_page, bootstrap_cotton_server_url):
    """The Bulma partial must not leak through the dispatch."""
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/form-field/")
    expect(page.locator(".field")).to_have_count(0)


def test_cotton_card_renders_bootstrap_markup(bootstrap_cotton_page, bootstrap_cotton_server_url):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/card/")
    expect(page.locator(".card-header")).to_contain_text("Card Title")
    expect(page.locator(".card-footer")).to_contain_text("Card Footer")


def test_cotton_card_slot_survives_the_dispatch(bootstrap_cotton_page, bootstrap_cotton_server_url):
    """`{% include %}` must carry {{ slot }} into the theme partial."""
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/card/")
    expect(page.locator(".card-body")).to_contain_text("Card body content")


def test_cotton_modal_named_slot_survives_the_dispatch(
    bootstrap_cotton_page, bootstrap_cotton_server_url
):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/modal/")
    expect(page.locator("#test-modal .modal-title")).to_contain_text("Test Modal")
    expect(page.locator("#test-modal .modal-body")).to_contain_text("Modal body content")


def test_cotton_modal_closed_by_default(bootstrap_cotton_page, bootstrap_cotton_server_url):
    """Class-level only: the cotton gallery pages are bare fragments that load
    neither a stylesheet nor Alpine, so `display` proves nothing here. The
    visibility claim is made against the JinjaX gallery, which loads both."""
    page, js_mode = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_be_attached()
    if js_mode == "js_on":
        expect(modal).not_to_have_class(re.compile(r"\bshow\b"))
        expect(modal).not_to_have_class(re.compile(r"\bd-block\b"))


def test_cotton_modal_declares_dialog_semantics(bootstrap_cotton_page, bootstrap_cotton_server_url):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "test-modal-title")


def test_cotton_tabs_render_the_active_tab(bootstrap_cotton_page, bootstrap_cotton_server_url):
    """`active` has to survive <c-vars> — unit tests bypass that compiler."""
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/tabs/")
    expect(page.locator("[role='tab'].active")).to_have_count(1)
    expect(page.locator("[role='tab'].active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_cotton_panel_honors_its_open_prop(bootstrap_cotton_page, bootstrap_cotton_server_url):
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).not_to_have_attribute("x-cloak", "")
    expect(page.locator('button[aria-controls="open-panel-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.locator('button[aria-controls="closed-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )


def test_cotton_open_panel_is_readable_without_js(
    bootstrap_cotton_page, bootstrap_cotton_server_url
):
    """The page ships the `[x-cloak] { display: none }` rule but no Alpine, so
    this is exactly the JS-less case: an open panel must not emit x-cloak."""
    page, _ = bootstrap_cotton_page
    page.goto(f"{bootstrap_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).to_be_visible()
    expect(page.locator("#closed-panel-body")).to_be_hidden()


# --- JinjaX: same Alpine contract, Bootstrap classes -----------------------


def test_jinja_modal_opens_and_closes(bootstrap_jinja_page, bootstrap_jinja_server_url):
    """cfModal is theme-independent; only the toggled classes differ.

    `.modal` is `display:none` and Bootstrap's `.show` only sets opacity — its
    own JS is what writes `display:block`. Asserting visibility rather than the
    class list is what catches a reveal that changes classes and nothing else.
    """
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")

    modal = page.locator("#e2e-modal")
    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(modal).to_be_hidden()
        page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
        expect(modal).to_be_visible()
        expect(modal).to_have_class(re.compile(r"\bshow\b"))
        modal.locator("button[aria-label='close']").click()
        expect(modal).to_be_hidden()
    else:
        expect(modal).to_be_attached()


def test_jinja_modal_backdrop_closes_and_does_not_swallow_the_dialog(
    bootstrap_jinja_page, bootstrap_jinja_server_url
):
    """The backdrop lives *inside* the modal here, which is not where Bootstrap
    puts it — its JS appends one to <body> at z-index 1050, below the modal's
    1055. Inside, that same 1050 would paint over the dialog and eat every
    click. The negative z-index is what prevents it, so both halves are
    asserted: the dialog still takes clicks, and the backdrop still closes."""
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_on":
        pytest.skip("backdrop dismissal requires JS")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    _wait_for_alpine(page)
    modal = page.locator("#e2e-modal")

    page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
    expect(modal).to_be_visible()
    # A control inside the dialog is still reachable, not covered.
    expect(modal.locator("#modal-ok")).to_be_visible()
    modal.locator("#modal-ok").click(timeout=2000)
    expect(modal).to_be_visible()

    modal.locator(".modal-backdrop").click(position={"x": 10, "y": 10})
    expect(modal).to_be_hidden()


def test_jinja_notification_dismisses(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    notification = page.locator(".alert")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(notification).to_be_visible()
        notification.locator("button[aria-label='dismiss']").click()
        expect(notification).to_be_hidden()
    else:
        expect(notification).to_be_attached()


def test_jinja_panel_expands(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    panel_body = page.locator("#e2e-panel-body")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(panel_body).to_be_hidden()
        page.locator('button[aria-controls="e2e-panel-body"]').click()
        expect(panel_body).to_be_visible()
    else:
        expect(panel_body).to_be_attached()


def test_jinja_navbar_toggler_toggles_menu(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        page.set_viewport_size({"width": 600, "height": 800})
        menu = page.locator(".navbar-collapse")
        # Assert the computed display, not the class list: `.collapse:not(.show)`
        # is what hides it, and only the computed value proves the toggle
        # actually reached that rule.
        display = "el => getComputedStyle(el).display"
        assert menu.evaluate(display) == "none"
        page.locator("button[aria-label='menu']").click()
        # Not to_be_visible(): the gallery passes empty start/end slots, so the
        # box has zero height even once it is displayed.
        assert menu.evaluate(display) != "none"
    else:
        expect(page.locator(".navbar")).to_be_attached()


def test_jinja_tabs_activate(bootstrap_jinja_page, bootstrap_jinja_server_url):
    """Clicking a tab moves the marker; the server-rendered one is the start."""
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_on":
        pytest.skip("covered without JS by test_jinja_exactly_one_tab_is_active")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    tabs = page.locator("[role='tab']")
    expect(tabs.nth(0)).to_have_class(re.compile(r"\bactive\b"))
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_class(re.compile(r"\bactive\b"))
    expect(tabs.nth(0)).not_to_have_class(re.compile(r"\bactive\b"))


def test_jinja_exactly_one_tab_is_active(bootstrap_jinja_page, bootstrap_jinja_server_url):
    """#21: `to_be_attached()` passed against markup that was unusable."""
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("[role='tab'].active")).to_have_count(1)
    expect(page.locator("[role='tab'].active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_jinja_arrow_keys_rove_focus_across_the_tablist(
    bootstrap_jinja_page, bootstrap_jinja_server_url
):
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_on":
        pytest.skip("roving tabindex requires JS")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("[role='tab']").first.focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab1"


# --- Dialog semantics and focus management (#21) ---------------------------


def test_jinja_modal_declares_dialog_semantics(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, _ = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    modal = page.locator("#e2e-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "e2e-modal-title")


def test_jinja_modal_manages_focus(bootstrap_jinja_page, bootstrap_jinja_server_url):
    """Same Alpine contract as Bulma — the theme changes classes, not behavior."""
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    page.keyboard.press("Escape")
    expect(page.locator("#e2e-modal")).to_be_hidden()
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_jinja_tab_does_not_escape_the_open_modal(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    inside = "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Tab"


def test_jinja_open_panel_is_readable_without_js(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("#e2e-panel-open-body")).to_be_visible()


def test_jinja_panel_toggle_reports_its_state(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator('button[aria-controls="e2e-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )
    expect(page.locator('button[aria-controls="e2e-panel-open-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )


def test_jinja_form_field_renders(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, _ = bootstrap_jinja_page
    page.goto(f"{bootstrap_jinja_server_url}/form-field")
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator(".form-label")).to_have_text("Email")


def test_jinja_page_usable_without_js(bootstrap_jinja_page, bootstrap_jinja_server_url):
    page, js_mode = bootstrap_jinja_page
    if js_mode != "js_off":
        pytest.skip("only runs in js_off mode")
    page.goto(f"{bootstrap_jinja_server_url}/gallery")
    expect(page.locator("section.section")).to_be_visible()
    expect(page.locator("body")).not_to_be_empty()
