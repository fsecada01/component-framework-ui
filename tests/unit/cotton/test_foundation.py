"""Foundation 6 component set, django-cotton side (issue #23).

These go through the public ``cotton/cf/<name>.html`` entry points with
``CF_UI_THEME = "foundation"``, so they exercise the dispatch wrapper as well
as the partial. ``render_to_string`` bypasses the django-cotton compiler (props
arrive as plain context), which is why the E2E tier still matters — but the
``{% include %}`` dispatch itself is real Django template machinery and is
fully exercised here.
"""

import pytest


@pytest.fixture
def foundation_render(settings, cotton_render):
    settings.CF_UI_THEME = "foundation"
    return cotton_render


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_foundation_error_classes(foundation_render):
    html = foundation_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "is-invalid-input" in html
    assert "is-invalid-label" in html
    assert "Required" in html


def test_form_field_error_text_is_visible(foundation_render):
    """`.form-error` is `display: none` without `.is-visible`."""
    html = foundation_render("cf/form-field.html", name="email", label="Email", error="Required")
    assert "form-error is-visible" in html


def test_form_field_without_an_error_stays_clean(foundation_render):
    html = foundation_render("cf/form-field.html", name="email", label="Email Address")
    assert "is-invalid-input" not in html
    assert "form-error" not in html
    assert "Email Address" in html


def test_form_field_required_flag(foundation_render):
    html = foundation_render("cf/form-field.html", name="email", label="Email", required="true")
    assert "required" in html


def test_form_field_input_class_still_applied(foundation_render):
    html = foundation_render("cf/form-field.html", name="e", label="E", input_class="my-input")
    assert "my-input" in html


def test_select_error_uses_the_invalid_input_class(foundation_render):
    html = foundation_render(
        "cf/select.html",
        name="choice",
        label="Choose",
        error="Pick one",
        options=[{"value": "a", "label": "Option A"}],
    )
    assert "is-invalid-input" in html
    assert "Option A" in html


def test_textarea_error_uses_the_invalid_input_class(foundation_render):
    html = foundation_render(
        "cf/textarea.html", name="bio", label="Bio", value="Hello", rows="4", error="Too short"
    )
    assert "is-invalid-input" in html
    assert "Hello" in html


def test_checkbox_group_uses_a_fieldset(foundation_render):
    html = foundation_render(
        "cf/checkbox-group.html",
        name="fruits",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert 'class="fieldset' in html
    assert "<legend" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_point_at_their_own_input(foundation_render):
    html = foundation_render(
        "cf/checkbox-group.html",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
        selected=[],
    )
    assert 'id="f-1"' in html
    assert 'for="f-1"' in html
    assert 'id="f-2"' in html
    assert 'for="f-2"' in html


def test_checkbox_group_control_class_still_applied(foundation_render):
    html = foundation_render(
        "cf/checkbox-group.html",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}],
        selected=[],
        control_class="my-control",
    )
    assert "my-control" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(foundation_render):
    html = foundation_render("cf/modal.html", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_foundation_reveal_classes(foundation_render):
    html = foundation_render("cf/modal.html", id="m")
    assert "reveal-overlay" in html
    assert 'class="reveal' in html


def test_modal_toggles_an_inline_display_not_a_class(foundation_render):
    """Foundation ships no open-state class for `.reveal` — see the Jinja twin."""
    html = foundation_render("cf/modal.html", id="m")
    assert ":style=" in html
    assert "display: block" in html
    assert "x-show" not in html


def test_notification_maps_danger_to_the_alert_callout(foundation_render):
    html = foundation_render("cf/notification.html", message="Boom", type="danger")
    assert "callout alert" in html
    assert "is-danger" not in html


def test_notification_maps_info_to_primary(foundation_render):
    html = foundation_render("cf/notification.html", message="Hi", type="info")
    assert "callout primary" in html


def test_notification_dismissible(foundation_render):
    html = foundation_render(
        "cf/notification.html", message="Saved!", type="success", dismissible="true"
    )
    assert "callout success" in html
    assert "visible = false" in html
    assert "close-button" in html


def test_notification_non_dismissible_omits_the_button(foundation_render):
    html = foundation_render("cf/notification.html", message="Hi", type="info", dismissible="false")
    assert "visible = false" not in html


def test_progress_uses_a_meter_child(foundation_render):
    """Foundation styles `.progress .progress-meter`, never a native control."""
    html = foundation_render("cf/progress.html", value="40", max="100", type="primary")
    assert "progress-meter" in html
    assert "width: 40%" in html
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html


def test_progress_maps_danger_to_alert(foundation_render):
    html = foundation_render("cf/progress.html", value="75", max="100", type="danger")
    assert "progress alert" in html


def test_progress_survives_a_zero_max(foundation_render):
    html = foundation_render("cf/progress.html", value="0", max="0", type="primary")
    assert "width: 0%" in html


# --- Content + navigation --------------------------------------------------


def test_card_uses_foundation_card_sections(foundation_render):
    html = foundation_render("cf/card.html", header="Title", slot="Body", footer="Foot")
    assert "card-section" in html
    assert "card-divider" in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_the_scroll_wrapper(foundation_render):
    html = foundation_render(
        "cf/table.html", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}]
    )
    assert "table-scroll" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_foundation_list_classes(foundation_render):
    html = foundation_render(
        "cf/pagination.html", page="2", total_pages="3", hx_url="/x", hx_target="#t"
    )
    assert "pagination-previous" in html
    assert "pagination-next" in html
    assert 'class="current"' in html


def test_pagination_disables_the_edges(foundation_render):
    html = foundation_render(
        "cf/pagination.html", page="1", total_pages="1", hx_url="/x", hx_target="#t"
    )
    assert "pagination-previous disabled" in html
    assert "pagination-next disabled" in html


def test_panel_keeps_the_alpine_contract(foundation_render):
    html = foundation_render("cf/panel.html", title="Details", slot="Inner")
    assert 'x-data="cfPanel"' in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_panel_avoids_the_accordion(foundation_render):
    """`.accordion-content` has no rule that ever un-hides it — see the twin."""
    html = foundation_render("cf/panel.html", title="T", slot="Inner", open="true")
    assert "accordion-content" not in html
    assert "card-section" in html


def test_navbar_keeps_the_alpine_contract(foundation_render):
    html = foundation_render("cf/navbar.html", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "top-bar-left" in html
    assert "top-bar-right" in html


def test_navbar_menu_stays_visible_on_desktop_when_collapsed(foundation_render):
    html = foundation_render("cf/navbar.html", brand="Brand", start="S", end="E")
    assert "hide-for-small-only" in html
    assert "'hide':" not in html


def test_breadcrumb_uses_foundation_breadcrumbs_class(foundation_render):
    html = foundation_render("cf/breadcrumb.html", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumbs' in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(foundation_render):
    html = foundation_render("cf/tabs.html", tabs=[{"id": "one", "url": "/one"}], slot="C")
    assert 'x-data="cfTabs"' in html
    # The id reaches Alpine as data, never as expression text (#32).
    assert 'data-cf-tab="one"' in html
    assert "setActive($el.dataset.cfTab)" in html
    assert "tabs-title" in html


def test_tabs_bind_aria_selected_because_the_css_reads_it(foundation_render):
    html = foundation_render(
        "cf/tabs.html", tabs=[{"id": "one", "url": "/one"}], active="one", slot="C"
    )
    assert 'aria-selected="true"' in html
    assert ":aria-selected=" in html
