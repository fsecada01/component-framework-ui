"""Fomantic UI component set, django-cotton side (issue #24).

These go through the public ``cotton/cf/<name>.html`` entry points with
``CF_UI_THEME = "fomantic"``, so they exercise the dispatch wrapper as well as
the partial. ``render_to_string`` bypasses the django-cotton compiler (props
arrive as plain context), which is why the E2E tier still matters — but the
``{% include %}`` dispatch itself is real Django template machinery and is
fully exercised here.
"""

import pytest


@pytest.fixture
def fomantic_render(settings, cotton_render):
    settings.CF_UI_THEME = "fomantic"
    return cotton_render


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_fomantic_form_classes(fomantic_render):
    html = fomantic_render("cf/form-field.html", name="email", label="Email Address")
    assert "ui form" in html
    assert 'class="field' in html
    assert "ui fluid input" in html
    assert "Email Address" in html


def test_form_field_error_marks_the_field_and_prompts(fomantic_render):
    html = fomantic_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "field error" in html
    assert "ui basic red pointing prompt label" in html
    assert "Required" in html


def test_form_field_error_does_not_use_a_ui_error_message(fomantic_render):
    html = fomantic_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "ui error message" not in html


def test_form_field_required_flag(fomantic_render):
    html = fomantic_render("cf/form-field.html", name="email", label="Email", required="true")
    assert "required" in html


def test_form_field_input_class_still_applied(fomantic_render):
    html = fomantic_render("cf/form-field.html", name="e", label="E", input_class="mini")
    assert "mini" in html


def test_select_uses_a_plain_styled_select(fomantic_render):
    html = fomantic_render(
        "cf/select.html",
        name="choice",
        label="Choose",
        options=[{"value": "a", "label": "Option A"}],
    )
    assert "<select" in html
    assert "ui fluid selection dropdown" in html
    assert "Option A" in html


def test_textarea_uses_fomantic_field_markup(fomantic_render):
    html = fomantic_render("cf/textarea.html", name="bio", label="Bio", value="Hello", rows="4")
    assert "ui form" in html
    assert "<textarea" in html
    assert "Hello" in html


def test_checkbox_group_uses_fomantic_checkbox_class(fomantic_render):
    html = fomantic_render(
        "cf/checkbox-group.html",
        name="fruits",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert "ui checkbox" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_are_associated_with_their_inputs(fomantic_render):
    html = fomantic_render(
        "cf/checkbox-group.html",
        name="fruits",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=[],
    )
    assert 'id="fruits-1"' in html
    assert 'for="fruits-1"' in html


def test_checkbox_group_control_class_still_applied(fomantic_render):
    html = fomantic_render(
        "cf/checkbox-group.html",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}],
        selected=[],
        control_class="inline",
    )
    assert "inline" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(fomantic_render):
    html = fomantic_render("cf/modal.html", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_renders_its_own_dimmer(fomantic_render):
    html = fomantic_render("cf/modal.html", id="m")
    assert "ui page dimmer" in html
    assert "ui modal" in html


def test_modal_toggles_the_active_class_from_alpine(fomantic_render):
    html = fomantic_render("cf/modal.html", id="m")
    assert html.count("{ 'active': open }") == 2


def test_notification_maps_danger_to_fomantic_negative(fomantic_render):
    html = fomantic_render("cf/notification.html", message="Boom", type="danger")
    assert "ui negative message" in html
    assert "alert-error" not in html


def test_notification_dismissible(fomantic_render):
    html = fomantic_render(
        "cf/notification.html", message="Saved!", type="success", dismissible="true"
    )
    assert "ui positive message" in html
    assert "visible = false" in html


def test_notification_non_dismissible_omits_the_button(fomantic_render):
    html = fomantic_render("cf/notification.html", message="Hi", type="info", dismissible="false")
    assert "visible = false" not in html


def test_progress_uses_fomantic_progress_markup(fomantic_render):
    html = fomantic_render("cf/progress.html", value="40", max="100", type="primary")
    assert "ui blue progress" in html
    assert 'class="bar"' in html
    assert 'data-percent="40"' in html


def test_progress_declares_progressbar_semantics(fomantic_render):
    html = fomantic_render("cf/progress.html", value="40", max="100", type="primary")
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert 'aria-valuemax="100"' in html


def test_progress_maps_danger_to_error(fomantic_render):
    html = fomantic_render("cf/progress.html", value="75", max="100", type="danger")
    assert "ui error progress" in html


def test_progress_clamps_a_value_above_max(fomantic_render):
    """Must match the Jinja side — the two template sets are one contract."""
    html = fomantic_render("cf/progress.html", value="150", max="100", type="primary")
    assert 'data-percent="100"' in html
    assert "width:100%" in html.replace(" ", "")
    assert 'aria-valuenow="100"' in html
    assert "150" not in html


def test_progress_clamps_a_negative_value(fomantic_render):
    html = fomantic_render("cf/progress.html", value="-10", max="100", type="primary")
    assert 'data-percent="0"' in html
    assert "width:0%" in html.replace(" ", "")
    assert 'aria-valuenow="0"' in html
    assert "-10" not in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(fomantic_render):
    html = fomantic_render("cf/card.html", header="Title", slot="Body", footer="Foot")
    assert "ui card" in html
    assert 'class="description"' in html
    assert 'class="extra content"' in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_fomantic_table_classes(fomantic_render):
    html = fomantic_render(
        "cf/table.html", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}]
    )
    assert "ui celled striped table" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_pagination_menu(fomantic_render):
    html = fomantic_render(
        "cf/pagination.html", page="2", total_pages="3", hx_url="/x", hx_target="#t"
    )
    assert "ui pagination menu" in html
    assert "active item" in html


def test_panel_uses_the_accordion_vocabulary(fomantic_render):
    html = fomantic_render("cf/panel.html", title="Details", slot="Inner", open="")
    assert "ui styled fluid accordion" in html
    assert 'x-data="cfPanel"' in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_panel_body_carries_the_active_class_when_open(fomantic_render):
    html = fomantic_render("cf/panel.html", id="p", title="T", slot="Body", open="true")
    assert "content active" in html
    assert "{ 'active': open }" in html


def test_panel_body_omits_the_active_class_when_closed(fomantic_render):
    html = fomantic_render("cf/panel.html", id="p", title="T", slot="Body", open="")
    assert "content active" not in html


def test_navbar_keeps_the_alpine_contract(fomantic_render):
    html = fomantic_render("cf/navbar.html", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "ui stackable menu" in html
    assert "Brand" in html


def test_breadcrumb_uses_fomantic_breadcrumb_markup(fomantic_render):
    html = fomantic_render(
        "cf/breadcrumb.html", items=[{"url": "/a", "label": "A"}, {"url": "/b", "label": "B"}]
    )
    assert "ui breadcrumb" in html
    assert 'class="divider"' in html
    assert "active section" in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(fomantic_render):
    html = fomantic_render("cf/tabs.html", tabs=[{"id": "one", "url": "/one"}], slot="C")
    assert 'x-data="cfTabs"' in html
    # The id reaches Alpine as data, never as expression text (#32).
    assert 'data-cf-tab="one"' in html
    assert "setActive($el.dataset.cfTab)" in html
    assert "ui top attached tabular menu" in html
