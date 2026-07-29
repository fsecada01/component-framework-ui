"""DaisyUI component set, django-cotton side (issue #6).

These go through the public ``cotton/cf/<name>.html`` entry points with
``CF_UI_THEME = "daisy"``, so they exercise the dispatch wrapper as well as
the partial. ``render_to_string`` bypasses the django-cotton compiler (props
arrive as plain context), which is why the E2E tier still matters — but the
``{% include %}`` dispatch itself is real Django template machinery and is
fully exercised here.
"""

import pytest


@pytest.fixture
def daisy_render(settings, cotton_render):
    settings.CF_UI_THEME = "daisy"
    return cotton_render


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_daisy_input_classes(daisy_render):
    html = daisy_render("cf/form-field.html", name="email", label="Email Address")
    assert "form-control" in html
    assert "input-bordered" in html
    assert "Email Address" in html


def test_form_field_error_uses_daisy_error_classes(daisy_render):
    html = daisy_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "input-error" in html
    assert "text-error" in html
    assert "Required" in html


def test_form_field_required_flag(daisy_render):
    html = daisy_render("cf/form-field.html", name="email", label="Email", required="true")
    assert "required" in html


def test_form_field_input_class_still_applied(daisy_render):
    html = daisy_render("cf/form-field.html", name="e", label="E", input_class="input-lg")
    assert "input-lg" in html


def test_select_uses_daisy_select_classes(daisy_render):
    html = daisy_render(
        "cf/select.html",
        name="choice",
        label="Choose",
        options=[{"value": "a", "label": "Option A"}],
    )
    assert "select-bordered" in html
    assert "Option A" in html


def test_textarea_uses_daisy_textarea_classes(daisy_render):
    html = daisy_render("cf/textarea.html", name="bio", label="Bio", value="Hello", rows="4")
    assert "textarea-bordered" in html
    assert "Hello" in html


def test_checkbox_group_uses_daisy_checkbox_class(daisy_render):
    html = daisy_render(
        "cf/checkbox-group.html",
        name="fruits",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert 'class="checkbox' in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_control_class_still_applied(daisy_render):
    html = daisy_render(
        "cf/checkbox-group.html",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}],
        selected=[],
        control_class="flex-row",
    )
    assert "flex-row" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(daisy_render):
    html = daisy_render("cf/modal.html", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_daisy_modal_classes(daisy_render):
    html = daisy_render("cf/modal.html", id="m")
    assert "modal-box" in html
    assert "modal-open" in html


def test_notification_maps_danger_to_daisy_error(daisy_render):
    html = daisy_render("cf/notification.html", message="Boom", type="danger")
    assert "alert-error" in html
    assert "alert-danger" not in html


def test_notification_dismissible(daisy_render):
    html = daisy_render(
        "cf/notification.html", message="Saved!", type="success", dismissible="true"
    )
    assert "alert-success" in html
    assert "visible = false" in html


def test_notification_non_dismissible_omits_the_button(daisy_render):
    html = daisy_render("cf/notification.html", message="Hi", type="info", dismissible="false")
    assert "visible = false" not in html


def test_progress_uses_daisy_progress_classes(daisy_render):
    html = daisy_render("cf/progress.html", value="40", max="100", type="primary")
    assert "progress-primary" in html
    assert 'value="40"' in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(daisy_render):
    html = daisy_render("cf/card.html", header="Title", slot="Body", footer="Foot")
    assert "card-body" in html
    assert "card-title" in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_daisy_table_classes(daisy_render):
    html = daisy_render(
        "cf/table.html", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}]
    )
    assert "table-zebra" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_join_group(daisy_render):
    html = daisy_render(
        "cf/pagination.html", page="2", total_pages="3", hx_url="/x", hx_target="#t"
    )
    assert "join-item" in html
    assert "btn-active" in html


def test_panel_keeps_the_alpine_contract(daisy_render):
    html = daisy_render("cf/panel.html", title="Details", slot="Inner")
    assert 'x-data="cfPanel"' in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_navbar_keeps_the_alpine_contract(daisy_render):
    html = daisy_render("cf/navbar.html", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "navbar-start" in html
    assert "navbar-end" in html


def test_breadcrumb_uses_daisy_breadcrumbs_class(daisy_render):
    html = daisy_render("cf/breadcrumb.html", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumbs' in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(daisy_render):
    html = daisy_render("cf/tabs.html", tabs=[{"id": "one", "url": "/one"}], slot="C")
    assert 'x-data="cfTabs"' in html
    assert "setActive('one')" in html
    assert "tab-active" in html
