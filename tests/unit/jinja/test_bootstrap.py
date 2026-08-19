"""Bootstrap 5 component set, Jinja2/JinjaX side (issue #22).

The Jinja theme switch is already directory-based — ``install_cf_ui`` registers
``templates/jinja/<theme>/`` — so this tier only has to prove the bootstrap
directory ships all 14 components, that they render under ``StrictUndefined``,
and that they speak Bootstrap 5's class vocabulary rather than Bulma's or
DaisyUI's.

One claim gets more attention than the rest: **no Bootstrap JavaScript.**
``data-bs-*`` is Bootstrap's own state API, and cf-ui already has one —
``cf_ui_alpine.js``. Two owners for the same ``open`` flag is how
``Alpine.store('cf').modal.open(id)`` stops meaning the same thing in every
theme, so the absence of ``data-bs-`` is asserted per component, not in prose.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from cf_ui.primitives import build_primitive_globals

BOOTSTRAP_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "cf_ui"
    / "templates"
    / "jinja"
    / "bootstrap"
)

COMPONENTS = [
    "Breadcrumb",
    "Card",
    "CheckboxGroup",
    "FormField",
    "Modal",
    "Navbar",
    "Notification",
    "Pagination",
    "Panel",
    "Progress",
    "Select",
    "Table",
    "Tabs",
    "Textarea",
]

# Minimum props each component needs to render at all.
REQUIRED_PROPS = {
    "Breadcrumb": {"items": [{"url": "/a", "label": "A"}]},
    "Card": {},
    "CheckboxGroup": {"name": "f", "label": "F", "choices": [{"value": "a", "label": "A"}]},
    "FormField": {"name": "f", "label": "F"},
    "Modal": {},
    "Navbar": {},
    "Notification": {"message": "Hi"},
    "Pagination": {"page": 1, "total_pages": 3},
    "Panel": {"title": "T"},
    "Progress": {},
    "Select": {"name": "f", "label": "F", "options": [{"value": "a", "label": "A"}]},
    "Table": {"columns": [{"key": "k", "label": "K"}], "rows": [{"k": "v"}]},
    "Tabs": {"tabs": [{"id": "one", "url": "/one"}]},
    "Textarea": {"name": "f", "label": "F"},
}


@pytest.fixture
def render() -> Callable[..., str]:
    env = Environment(
        loader=FileSystemLoader(BOOTSTRAP_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )
    env.globals.update(build_primitive_globals())

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render


# --- Parity with the Bulma set ---------------------------------------------


def test_bootstrap_ships_the_same_components_as_bulma():
    bulma_dir = BOOTSTRAP_DIR.parent / "bulma"
    assert sorted(p.name for p in BOOTSTRAP_DIR.glob("*.jinja")) == sorted(
        p.name for p in bulma_dir.glob("*.jinja")
    )


def test_the_planned_stub_is_gone():
    """A theme cannot be both shipped and planned."""
    assert not (BOOTSTRAP_DIR / "PLANNED.md").exists()


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_renders_with_only_its_required_props(render, name):
    """StrictUndefined: every optional prop needs an is-defined guard."""
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    assert html.strip()


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_carries_no_other_themes_class_names(render, name):
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    for marker in (
        "is-danger",
        "is-active",
        "card-header-title",
        "navbar-burger",
        "input-bordered",
        "tab-active",
        "join-item",
    ):
        assert marker not in html, f"{name} still speaks another theme"


# --- The constraint that makes this theme cf-ui's rather than Bootstrap's ---


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_uses_no_bootstrap_javascript_api(render, name):
    """Alpine owns modal/tab/panel state in every theme — see issue #22.

    ``data-bs-toggle`` would hand the same state to Bootstrap's bundle, and
    the two would fight the moment a page loaded both.
    """
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    assert "data-bs-" not in html


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_source_names_no_bootstrap_bundle(name):
    source = (BOOTSTRAP_DIR / f"{name}.jinja").read_text(encoding="utf-8")
    assert "bootstrap.bundle" not in source
    assert "data-bs-" not in source


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_bootstrap_input_classes(render):
    html = render("FormField.jinja", name="email", label="Email")
    assert "form-label" in html
    assert "form-control" in html
    assert 'name="email"' in html


def test_form_field_error_uses_bootstrap_validation_classes(render):
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "is-invalid" in html
    assert "invalid-feedback" in html
    assert "Required" in html


def test_form_field_error_text_is_forced_visible(render):
    """`.invalid-feedback` is display:none until a sibling is `.is-invalid`.

    The rule is `~`, so it only fires for the input case. Every error slot in
    this theme carries `d-block` so the message never renders invisibly.
    """
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "invalid-feedback d-block" in html


def test_form_field_input_class_still_applied(render):
    html = render("FormField.jinja", name="email", label="Email", input_class="form-control-lg")
    assert "form-control-lg" in html


def test_form_field_required_flag(render):
    html = render("FormField.jinja", name="email", label="Email", required=True)
    assert "required" in html


def test_select_uses_the_bootstrap_select_class(render):
    html = render(
        "Select.jinja", name="c", label="C", options=[{"value": "a", "label": "Option A"}]
    )
    assert "form-select" in html
    assert "Option A" in html


def test_select_marks_the_current_value(render):
    html = render(
        "Select.jinja",
        name="c",
        label="C",
        value="a",
        options=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
    )
    assert "selected" in html


def test_textarea_uses_the_form_control_class(render):
    html = render("Textarea.jinja", name="bio", label="Bio", value="Hello")
    assert "form-control" in html
    assert "Hello" in html
    assert 'rows="4"' in html


def test_checkbox_group_uses_the_form_check_classes(render):
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert "form-check" in html
    assert "form-check-input" in html
    assert "form-check-label" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_point_at_their_input(render):
    """`for=` must be unique per choice or every label toggles the first box."""
    html = render(
        "CheckboxGroup.jinja",
        name="fruit",
        label="Fruit",
        choices=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
    )
    assert 'id="fruit-a"' in html
    assert 'for="fruit-a"' in html
    assert 'id="fruit-b"' in html
    assert 'for="fruit-b"' in html


def test_checkbox_group_control_class_still_applied(render):
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}],
        control_class="d-flex",
    )
    assert "d-flex" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(render):
    html = render("Modal.jinja", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_bootstrap_modal_classes(render):
    html = render("Modal.jinja", id="m")
    assert "modal-dialog" in html
    assert "modal-content" in html
    assert "modal-body" in html
    assert "btn-close" in html


def test_modal_reveal_toggles_display_not_just_show(render):
    """`.modal` is `display:none`; `.show` alone never reveals it.

    Bootstrap's own JS sets `style.display = 'block'` — cf-ui has no Bootstrap
    JS, so the reveal has to come from a class Alpine can toggle. Asserting
    only `show` here would pass against a modal that never becomes visible.
    """
    html = render("Modal.jinja", id="m")
    assert "d-block" in html
    assert "'show'" in html


def test_notification_maps_type_onto_a_bootstrap_alert(render):
    html = render("Notification.jinja", message="Boom", type="danger")
    assert "alert-danger" in html
    assert "alert-error" not in html


def test_notification_maps_error_onto_danger(render):
    """Bootstrap has no `alert-error`; the prop vocabulary stays stable."""
    html = render("Notification.jinja", message="Boom", type="error")
    assert "alert-danger" in html


def test_notification_success_and_dismiss(render):
    html = render("Notification.jinja", message="Saved!", type="success", dismissible=True)
    assert "alert-success" in html
    assert "alert-dismissible" in html
    assert "Saved!" in html
    assert "visible = false" in html


def test_notification_non_dismissible_omits_the_button(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=False)
    assert "visible = false" not in html
    assert "alert-dismissible" not in html


def test_progress_uses_the_bootstrap_progress_bar_markup(render):
    html = render("Progress.jinja", value=40, max=100, type="primary")
    assert "progress-bar" in html
    assert "bg-primary" in html
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert 'aria-valuemax="100"' in html
    assert "width: 40%" in html


def test_progress_scales_the_bar_to_a_non_percentage_max(render):
    """`max` is a prop; a bar hard-coded to `value%` is wrong for max != 100."""
    html = render("Progress.jinja", value=1, max=4)
    assert "width: 25%" in html


def test_progress_survives_a_zero_max(render):
    html = render("Progress.jinja", value=0, max=0)
    assert "width: 0%" in html


def test_progress_maps_danger_to_bg_danger(render):
    html = render("Progress.jinja", value=75, max=100, type="danger")
    assert "bg-danger" in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(render):
    html = render("Card.jinja", header="Title", content="Body", footer="Foot")
    assert "card-header" in html
    assert "card-body" in html
    assert "card-footer" in html
    assert "Title" in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_bootstrap_table_classes(render):
    html = render("Table.jinja", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}])
    assert "table-striped" in html
    assert "table-responsive" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_page_item_list(render):
    html = render("Pagination.jinja", page=2, total_pages=3, hx_url="/x", hx_target="#t")
    assert "page-item" in html
    assert "page-link" in html
    assert 'aria-current="page"' in html


def test_pagination_disables_the_edges(render):
    html = render("Pagination.jinja", page=1, total_pages=1, hx_url="/x", hx_target="#t")
    assert html.count("disabled") >= 2
    assert 'aria-disabled="true"' in html


def test_panel_uses_the_accordion_markup(render):
    html = render("Panel.jinja", title="Details", content="Inner")
    assert "accordion" in html
    assert "accordion-button" in html
    assert "accordion-body" in html
    assert "Inner" in html


def test_panel_body_is_not_a_bootstrap_collapse(render):
    """`.collapse` is `display:none` without `.show`, and x-show owns display.

    Carrying both would hide a server-open panel permanently with JS off —
    exactly the bug the accessibility phase fixed.
    """
    html = render("Panel.jinja", id="p", title="T", content="Inner", open=True)
    assert 'class="collapse' not in html
    assert " collapse " not in html


def test_panel_keeps_the_alpine_contract(render):
    html = render("Panel.jinja", title="Details", content="Inner")
    assert 'x-data="cfPanel"' in html
    assert "x-show" in html
    assert "x-cloak" in html


def test_navbar_keeps_the_alpine_contract(render):
    html = render("Navbar.jinja", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "toggle()" in html
    assert "navbar-toggler" in html
    assert "navbar-collapse" in html
    assert "Brand" in html


def test_breadcrumb_uses_the_bootstrap_breadcrumb_classes(render):
    html = render("Breadcrumb.jinja", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumb"' in html
    assert "breadcrumb-item" in html
    assert 'aria-current="page"' in html


def test_tabs_keep_the_alpine_contract(render):
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], content="C")
    assert 'x-data="cfTabs"' in html
    # The id reaches Alpine as data, never as expression text (#32).
    assert 'data-cf-tab="one"' in html
    assert "setActive($el.dataset.cfTab)" in html
    assert "nav-tabs" in html
    assert "nav-link" in html
