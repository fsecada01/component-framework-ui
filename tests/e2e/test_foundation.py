"""Foundation E2E coverage (issue #23), parameterized over js_on / js_off.

Two things make this suite different from the Bulma and DaisyUI ones, and both
come from the same constraint — the theme loads Foundation's **CSS only**:

1. Reveal has no open-state class, so "is the modal open" cannot be asserted
   with `to_have_class`. Every visibility claim here reads the **computed
   display**, which is the property that actually matters and the only one that
   would catch a binding that changes markup without changing the page.
2. `test_no_page_loads_jquery` is the executable form of the issue's "grep the
   rendered output for jquery" step. Adding jQuery for one theme would make a
   `CF_UI_THEME` edit change a consuming app's dependency graph.
"""

import pytest
from playwright.sync_api import expect

DISPLAY = "el => getComputedStyle(el).display"


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


def _wait_for_modal_shown(page, shown: bool) -> None:
    op = "!==" if shown else "==="
    page.wait_for_function(
        f"() => getComputedStyle(document.getElementById('e2e-modal')).display {op} 'none'",
        timeout=5000,
    )


# --- The CSS-only constraint, executed -------------------------------------


def test_no_page_loads_jquery(foundation_jinja_page, foundation_jinja_server_url):
    """Issue #23's verification step, as a test rather than a one-off grep."""
    page, _ = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    assert "jquery" not in page.content().lower()


def test_no_cotton_page_loads_jquery(foundation_cotton_page, foundation_cotton_server_url):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/modal/")
    assert "jquery" not in page.content().lower()


def test_foundation_js_is_never_initialised(foundation_jinja_page, foundation_jinja_server_url):
    """`window.Foundation` existing would mean the plugins got loaded."""
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("nothing to evaluate without JS")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)
    assert page.evaluate("() => typeof window.jQuery") == "undefined"
    assert page.evaluate("() => typeof window.Foundation") == "undefined"


# --- JinjaX: same Alpine contract, Foundation classes ----------------------


def test_jinja_modal_opens_and_closes(foundation_jinja_page, foundation_jinja_server_url):
    """Reveal ships no state class, so this reads computed display.

    `.reveal-overlay` is `display: none` in Foundation's stylesheet with no
    counterpart rule; the template drives an inline `display` from Alpine
    exactly as the jQuery plugin would have.
    """
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")

    modal = page.locator("#e2e-modal")
    if js_mode == "js_on":
        _wait_for_alpine(page)
        assert modal.evaluate(DISPLAY) == "none"
        page.evaluate("Alpine.store('cf').modal.open('e2e-modal')")
        _wait_for_modal_shown(page, shown=True)
        modal.locator("button[aria-label='close']").click()
        _wait_for_modal_shown(page, shown=False)
    else:
        # Without JS the stylesheet alone keeps it closed — which is the point
        # of not needing a state class to hide it.
        expect(modal).to_be_attached()
        assert modal.evaluate(DISPLAY) == "none"


def test_jinja_notification_dismisses(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    notification = page.locator(".callout")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(notification).to_be_visible()
        notification.locator("button[aria-label='dismiss']").click()
        expect(notification).to_be_hidden()
    else:
        expect(notification).to_be_attached()


def test_jinja_panel_expands(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    panel_body = page.locator("#e2e-panel-body")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        expect(panel_body).to_be_hidden()
        page.locator('button[aria-controls="e2e-panel-body"]').click()
        expect(panel_body).to_be_visible()
    else:
        expect(panel_body).to_be_attached()


def test_jinja_navbar_burger_toggles_menu(foundation_jinja_page, foundation_jinja_server_url):
    """`hide-for-small-only` is breakpoint-scoped on purpose.

    Binding plain `.hide` would have collapsed the desktop menu too. Asserting
    the computed display at a small viewport is what distinguishes the two.
    """
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")

    if js_mode == "js_on":
        _wait_for_alpine(page)
        page.set_viewport_size({"width": 600, "height": 800})
        menu = page.locator(".top-bar-right")
        assert menu.evaluate(DISPLAY) == "none"
        page.locator("button[aria-label='menu']").click()
        assert menu.evaluate(DISPLAY) != "none"
    else:
        expect(page.locator(".top-bar")).to_be_attached()


def test_jinja_navbar_menu_survives_at_desktop_width(
    foundation_jinja_page, foundation_jinja_server_url
):
    """The regression `hide-for-small-only` exists to prevent."""
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("the collapse only happens under Alpine")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)
    page.set_viewport_size({"width": 1280, "height": 800})
    assert page.locator(".top-bar-right").evaluate(DISPLAY) != "none"


def test_jinja_tabs_activate(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("covered without JS by test_jinja_exactly_one_tab_is_active")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    tabs = page.locator("[role='tab']")
    expect(page.locator("li.tabs-title.is-active")).to_have_text("tab1")
    tabs.nth(1).click()
    expect(page.locator("li.tabs-title.is-active")).to_have_text("tab2")
    expect(page.locator("li.tabs-title.is-active")).to_have_count(1)


def test_jinja_exactly_one_tab_is_active(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("li.tabs-title.is-active")).to_have_count(1)
    expect(page.locator("li.tabs-title.is-active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)
    expect(page.locator("[role='tab'][tabindex='0']")).to_have_count(1)


def test_jinja_arrow_keys_rove_focus_across_the_tablist(
    foundation_jinja_page, foundation_jinja_server_url
):
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("roving tabindex requires JS")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("[role='tab']").first.focus()
    page.keyboard.press("ArrowRight")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab2"
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.cfTab") == "tab1"


# --- Dialog semantics and focus management (#21) ---------------------------


def test_jinja_modal_declares_dialog_semantics(foundation_jinja_page, foundation_jinja_server_url):
    page, _ = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    modal = page.locator("#e2e-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "e2e-modal-title")


def test_jinja_modal_manages_focus(foundation_jinja_page, foundation_jinja_server_url):
    """Same Alpine contract as Bulma — the theme changes classes, not behavior."""
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    page.keyboard.press("Escape")
    _wait_for_modal_shown(page, shown=False)
    assert page.evaluate("() => document.activeElement.id") == "open-modal"


def test_jinja_tab_does_not_escape_the_open_modal(
    foundation_jinja_page, foundation_jinja_server_url
):
    page, js_mode = foundation_jinja_page
    if js_mode != "js_on":
        pytest.skip("focus management requires JS")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    _wait_for_alpine(page)

    page.locator("#open-modal").click()
    _wait_for_modal_focus(page)
    inside = "() => document.getElementById('e2e-modal').contains(document.activeElement)"
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(inside), "focus escaped the dialog on Tab"


def test_jinja_open_panel_is_readable_without_js(
    foundation_jinja_page, foundation_jinja_server_url
):
    """The reason the panel is not built from Foundation's accordion.

    `.accordion-content` is `display: none` with no rule that ever un-hides it,
    so this assertion is exactly what that markup would have failed.
    """
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator("#e2e-panel-open-body")).to_be_visible()


def test_jinja_panel_toggle_reports_its_state(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/gallery")
    if js_mode == "js_on":
        _wait_for_alpine(page)
    expect(page.locator('button[aria-controls="e2e-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )
    expect(page.locator('button[aria-controls="e2e-panel-open-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )


def test_jinja_form_field_renders(foundation_jinja_page, foundation_jinja_server_url):
    page, _ = foundation_jinja_page
    page.goto(f"{foundation_jinja_server_url}/form-field")
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator("label[for='email']")).to_have_text("Email")


def test_jinja_page_usable_without_js(foundation_jinja_page, foundation_jinja_server_url):
    page, js_mode = foundation_jinja_page
    if js_mode != "js_off":
        pytest.skip("only runs in js_off mode")
    page.goto(f"{foundation_jinja_server_url}/gallery")
    expect(page.locator("body")).not_to_be_empty()
    expect(page.locator(".top-bar")).to_be_visible()


# --- django-cotton: one setting, no consumer template edits ----------------


def test_cotton_form_field_renders_foundation_markup(
    foundation_cotton_page, foundation_cotton_server_url
):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/form-field/")
    expect(page.locator("input[name='email']")).to_be_attached()
    expect(page.locator("label[for='email']")).to_be_attached()


def test_cotton_form_field_has_no_bulma_markup(
    foundation_cotton_page, foundation_cotton_server_url
):
    """The Bulma partial must not leak through the dispatch."""
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/form-field/")
    expect(page.locator(".field")).to_have_count(0)


def test_cotton_card_renders_foundation_markup(
    foundation_cotton_page, foundation_cotton_server_url
):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/card/")
    expect(page.locator(".card-section")).to_be_attached()
    expect(page.locator(".card-divider").first).to_contain_text("Card Title")


def test_cotton_card_slot_survives_the_dispatch(
    foundation_cotton_page, foundation_cotton_server_url
):
    """`{% include %}` must carry {{ slot }} into the theme partial."""
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/card/")
    expect(page.locator(".card-section")).to_contain_text("Card body content")


def test_cotton_modal_named_slot_survives_the_dispatch(
    foundation_cotton_page, foundation_cotton_server_url
):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/modal/")
    expect(page.locator("#test-modal .reveal")).to_contain_text("Test Modal")
    expect(page.locator("#test-modal .reveal")).to_contain_text("Modal body content")


def test_cotton_modal_is_not_server_rendered_open(
    foundation_cotton_page, foundation_cotton_server_url
):
    """The cotton gallery pages are bare fragments — no stylesheet, no Alpine.

    So computed display proves nothing here (it would be measuring the
    fixture), and Foundation has no `modal-open` class for the DaisyUI version
    of this test to look for. What *is* assertable is the markup the dispatch
    produced: the overlay carries the state binding and no server-rendered
    inline `display`, so it is Alpine — not the server — that ever opens it.
    Whether it is actually invisible when closed is asserted against the
    JinjaX gallery, which does load Foundation's CSS.
    """
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_be_attached()
    expect(modal).to_have_attribute(":style", "open ? 'display: block' : 'display: none'")
    assert modal.get_attribute("style") is None


def test_cotton_modal_declares_dialog_semantics(
    foundation_cotton_page, foundation_cotton_server_url
):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/modal/")
    modal = page.locator("#test-modal")
    expect(modal).to_have_attribute("role", "dialog")
    expect(modal).to_have_attribute("aria-modal", "true")
    expect(modal).to_have_attribute("aria-labelledby", "test-modal-title")


def test_cotton_tabs_render_the_active_tab(foundation_cotton_page, foundation_cotton_server_url):
    """`active` has to survive <c-vars> — unit tests bypass that compiler."""
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/tabs/")
    expect(page.locator("li.tabs-title.is-active")).to_have_count(1)
    expect(page.locator("li.tabs-title.is-active")).to_have_text("tab1")
    expect(page.locator("[role='tab'][aria-selected='true']")).to_have_count(1)


def test_cotton_panel_honors_its_open_prop(foundation_cotton_page, foundation_cotton_server_url):
    page, _ = foundation_cotton_page
    page.goto(f"{foundation_cotton_server_url}/panel/")
    expect(page.locator("#open-panel-body")).not_to_have_attribute("x-cloak", "")
    expect(page.locator('button[aria-controls="open-panel-body"]')).to_have_attribute(
        "aria-expanded", "true"
    )
    expect(page.locator('button[aria-controls="closed-panel-body"]')).to_have_attribute(
        "aria-expanded", "false"
    )


def test_cotton_theme_comments_do_not_leak_into_the_page(
    foundation_cotton_page, foundation_cotton_server_url
):
    """Django's `{# #}` is single-line only — a multi-line one renders verbatim.

    Every explanatory comment in the cotton partials is therefore a
    `{% comment %}` block. This caught a real leak during the phase, so it is
    pinned rather than left to review.
    """
    page, _ = foundation_cotton_page
    for path in ("/form-field/", "/card/", "/modal/", "/panel/", "/tabs/"):
        page.goto(f"{foundation_cotton_server_url}{path}")
        body = page.locator("body").inner_text()
        assert "{#" not in body
        assert "{% comment" not in body
