"""Bootstrap 5 component set, django-cotton side (issue #22).

These go through the public ``cotton/cf/<name>.html`` entry points with
``CF_UI_THEME = "bootstrap"``, so they exercise the dispatch wrapper as well as
the partial. ``render_to_string`` bypasses the django-cotton compiler (props
arrive as plain context), which is why the E2E tier still matters — but the
``{% include %}`` dispatch itself is real Django template machinery and is
fully exercised here.
"""

from pathlib import Path

import pytest

PARTIALS_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "cf_ui"
    / "templates"
    / "cotton"
    / "_themes"
    / "bootstrap"
)

STEMS = [
    "breadcrumb",
    "card",
    "checkbox-group",
    "form-field",
    "modal",
    "navbar",
    "notification",
    "pagination",
    "panel",
    "progress",
    "select",
    "table",
    "tabs",
    "textarea",
]


@pytest.fixture
def bootstrap_render(settings, cotton_render):
    settings.CF_UI_THEME = "bootstrap"
    return cotton_render


# --- The set is complete, and carries no Bootstrap JS ----------------------


def test_the_legacy_planned_stub_directory_is_gone():
    """`cotton/bootstrap/` predates the `_themes/` dispatch introduced in #6."""
    legacy = PARTIALS_DIR.parent.parent / "bootstrap"
    assert not legacy.exists()


@pytest.mark.parametrize("stem", STEMS)
def test_partial_uses_no_bootstrap_javascript_api(stem):
    """Alpine owns modal/tab/panel state in every theme — see issue #22."""
    source = (PARTIALS_DIR / f"{stem}.html").read_text(encoding="utf-8")
    assert "data-bs-" not in source
    assert "bootstrap.bundle" not in source


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_bootstrap_input_classes(bootstrap_render):
    html = bootstrap_render("cf/form-field.html", name="email", label="Email Address")
    assert "form-label" in html
    assert "form-control" in html
    assert "Email Address" in html


def test_form_field_error_uses_bootstrap_validation_classes(bootstrap_render):
    html = bootstrap_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "is-invalid" in html
    assert "invalid-feedback d-block" in html
    assert "Required" in html


def test_form_field_required_flag(bootstrap_render):
    """`required>` rather than `required` — the uncompiled <c-vars> line the
    wrapper emits under ``render_to_string`` contains ``required="false"``,
    so a bare substring check passes either way."""
    html = bootstrap_render("cf/form-field.html", name="email", label="Email", required="true")
    assert "required>" in html


def test_form_field_not_required_by_default(bootstrap_render):
    """<c-vars required="false"> arrives as the *string* "false"."""
    html = bootstrap_render("cf/form-field.html", name="email", label="Email", required="false")
    assert "required>" not in html


def test_form_field_input_class_still_applied(bootstrap_render):
    html = bootstrap_render(
        "cf/form-field.html", name="e", label="E", input_class="form-control-lg"
    )
    assert "form-control-lg" in html


def test_select_uses_the_bootstrap_select_class(bootstrap_render):
    html = bootstrap_render(
        "cf/select.html",
        name="choice",
        label="Choose",
        options=[{"value": "a", "label": "Option A"}],
    )
    assert "form-select" in html
    assert "Option A" in html


def test_select_marks_the_current_value(bootstrap_render):
    html = bootstrap_render(
        "cf/select.html",
        name="choice",
        label="Choose",
        value="a",
        options=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
    )
    assert "selected" in html


def test_textarea_uses_the_form_control_class(bootstrap_render):
    html = bootstrap_render("cf/textarea.html", name="bio", label="Bio", value="Hello", rows="4")
    assert "form-control" in html
    assert "Hello" in html


def test_checkbox_group_uses_the_form_check_classes(bootstrap_render):
    html = bootstrap_render(
        "cf/checkbox-group.html",
        name="fruits",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert "form-check-input" in html
    assert "form-check-label" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_point_at_their_input(bootstrap_render):
    html = bootstrap_render(
        "cf/checkbox-group.html",
        name="fruit",
        label="Fruit",
        choices=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
        selected=[],
    )
    assert 'id="fruit-a"' in html
    assert 'for="fruit-b"' in html


def test_checkbox_group_control_class_still_applied(bootstrap_render):
    html = bootstrap_render(
        "cf/checkbox-group.html",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}],
        selected=[],
        control_class="d-flex",
    )
    assert "d-flex" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(bootstrap_render):
    html = bootstrap_render("cf/modal.html", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_bootstrap_modal_classes(bootstrap_render):
    html = bootstrap_render("cf/modal.html", id="m")
    assert "modal-dialog" in html
    assert "modal-content" in html
    assert "modal-body" in html
    assert "btn-close" in html


def test_modal_reveal_toggles_display_not_just_show(bootstrap_render):
    html = bootstrap_render("cf/modal.html", id="m")
    assert "d-block" in html
    assert "'show'" in html


def test_notification_maps_danger_to_a_bootstrap_alert(bootstrap_render):
    html = bootstrap_render("cf/notification.html", message="Boom", type="danger")
    assert "alert-danger" in html
    assert "alert-error" not in html


def test_notification_maps_error_onto_danger(bootstrap_render):
    html = bootstrap_render("cf/notification.html", message="Boom", type="error")
    assert "alert-danger" in html


def test_notification_dismissible(bootstrap_render):
    html = bootstrap_render(
        "cf/notification.html", message="Saved!", type="success", dismissible="true"
    )
    assert "alert-success" in html
    assert "alert-dismissible" in html
    assert "visible = false" in html


def test_notification_non_dismissible_omits_the_button(bootstrap_render):
    html = bootstrap_render("cf/notification.html", message="Hi", type="info", dismissible="false")
    assert "visible = false" not in html


def test_progress_uses_the_bootstrap_progress_bar_markup(bootstrap_render):
    html = bootstrap_render("cf/progress.html", value="40", max="100", type="primary")
    assert "progress-bar" in html
    assert "bg-primary" in html
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert "width: 40%" in html


def test_progress_scales_the_bar_to_a_non_percentage_max(bootstrap_render):
    html = bootstrap_render("cf/progress.html", value="1", max="4", type="info")
    assert "width: 25%" in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(bootstrap_render):
    html = bootstrap_render("cf/card.html", header="Title", slot="Body", footer="Foot")
    assert "card-header" in html
    assert "card-body" in html
    assert "card-footer" in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_bootstrap_table_classes(bootstrap_render):
    html = bootstrap_render(
        "cf/table.html", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}]
    )
    assert "table-striped" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_page_item_list(bootstrap_render):
    html = bootstrap_render(
        "cf/pagination.html", page="2", total_pages="3", hx_url="/x", hx_target="#t"
    )
    assert "page-item" in html
    assert "page-link" in html
    assert 'aria-current="page"' in html


def test_panel_uses_the_accordion_markup(bootstrap_render):
    html = bootstrap_render("cf/panel.html", title="Details", slot="Inner")
    assert "accordion-button" in html
    assert "accordion-body" in html
    assert 'x-data="cfPanel"' in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_panel_body_is_not_a_bootstrap_collapse(bootstrap_render):
    html = bootstrap_render("cf/panel.html", id="p", title="T", slot="Inner", open="true")
    assert 'class="collapse' not in html
    assert " collapse " not in html


def test_navbar_keeps_the_alpine_contract(bootstrap_render):
    html = bootstrap_render("cf/navbar.html", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "navbar-toggler" in html
    assert "navbar-collapse" in html


def test_breadcrumb_uses_the_bootstrap_breadcrumb_classes(bootstrap_render):
    html = bootstrap_render("cf/breadcrumb.html", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumb"' in html
    assert "breadcrumb-item" in html
    assert 'aria-current="page"' in html


def test_tabs_keep_the_alpine_contract(bootstrap_render):
    html = bootstrap_render("cf/tabs.html", tabs=[{"id": "one", "url": "/one"}], slot="C")
    assert 'x-data="cfTabs"' in html
    assert "setActive('one')" in html
    assert "nav-tabs" in html
