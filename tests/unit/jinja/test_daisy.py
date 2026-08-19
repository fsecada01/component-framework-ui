"""DaisyUI component set, Jinja2/JinjaX side (issue #6).

The Jinja theme switch is already directory-based — ``install_cf_ui`` registers
``templates/jinja/<theme>/`` — so this tier only has to prove the daisy
directory ships all 14 components, that they render under ``StrictUndefined``,
and that they speak DaisyUI's class vocabulary rather than Bulma's.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from cf_ui.primitives import build_primitive_globals

DAISY_DIR = (
    Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "jinja" / "daisy"
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
        loader=FileSystemLoader(DAISY_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )
    env.globals.update(build_primitive_globals())

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render


# --- Parity with the Bulma set ---------------------------------------------


def test_daisy_ships_the_same_components_as_bulma():
    bulma_dir = DAISY_DIR.parent / "bulma"
    assert sorted(p.name for p in DAISY_DIR.glob("*.jinja")) == sorted(
        p.name for p in bulma_dir.glob("*.jinja")
    )


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_renders_with_only_its_required_props(render, name):
    """StrictUndefined: every optional prop needs an is-defined guard."""
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    assert html.strip()


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_carries_no_bulma_class_names(render, name):
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    for bulma_marker in ("is-danger", "is-active", "card-header-title", "navbar-burger", "help"):
        assert bulma_marker not in html, f"{name} still speaks Bulma"


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_daisy_input_classes(render):
    html = render("FormField.jinja", name="email", label="Email")
    assert "form-control" in html
    assert "input-bordered" in html
    assert 'name="email"' in html


def test_form_field_error_uses_daisy_error_classes(render):
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "input-error" in html
    assert "text-error" in html
    assert "Required" in html


def test_form_field_input_class_still_applied(render):
    html = render("FormField.jinja", name="email", label="Email", input_class="input-lg")
    assert "input-lg" in html


def test_select_uses_daisy_select_classes(render):
    html = render(
        "Select.jinja", name="c", label="C", options=[{"value": "a", "label": "Option A"}]
    )
    assert "select-bordered" in html
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


def test_textarea_uses_daisy_textarea_classes(render):
    html = render("Textarea.jinja", name="bio", label="Bio", value="Hello")
    assert "textarea-bordered" in html
    assert "Hello" in html


def test_checkbox_group_uses_daisy_checkbox_class(render):
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert 'class="checkbox' in html
    assert "checked" in html
    assert "Apple" in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(render):
    html = render("Modal.jinja", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_daisy_modal_classes(render):
    html = render("Modal.jinja", id="m")
    assert "modal-box" in html
    assert "modal-open" in html


def test_notification_maps_danger_to_daisy_error(render):
    """DaisyUI has no `alert-danger`; the prop vocabulary stays stable."""
    html = render("Notification.jinja", message="Boom", type="danger")
    assert "alert-error" in html
    assert "alert-danger" not in html


def test_notification_success_and_dismiss(render):
    html = render("Notification.jinja", message="Saved!", type="success", dismissible=True)
    assert "alert-success" in html
    assert "Saved!" in html
    assert "visible = false" in html


def test_notification_non_dismissible_omits_the_button(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=False)
    assert "visible = false" not in html


def test_progress_uses_daisy_progress_classes(render):
    html = render("Progress.jinja", value=40, max=100, type="primary")
    assert "progress-primary" in html
    assert 'value="40"' in html
    assert 'max="100"' in html


def test_progress_maps_danger_to_error(render):
    html = render("Progress.jinja", value=75, max=100, type="danger")
    assert "progress-error" in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(render):
    html = render("Card.jinja", header="Title", content="Body", footer="Foot")
    assert "card-body" in html
    assert "card-title" in html
    assert "Title" in html
    assert "Body" in html
    assert "Foot" in html


def test_table_uses_daisy_table_classes(render):
    html = render("Table.jinja", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}])
    assert "table-zebra" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_join_group(render):
    html = render("Pagination.jinja", page=2, total_pages=3, hx_url="/x", hx_target="#t")
    assert "join-item" in html
    assert "btn-active" in html
    assert 'aria-current="page"' in html


def test_panel_keeps_the_alpine_contract(render):
    html = render("Panel.jinja", title="Details", content="Inner")
    assert 'x-data="cfPanel"' in html
    assert "x-show" in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_navbar_keeps_the_alpine_contract(render):
    html = render("Navbar.jinja", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "toggle()" in html
    assert "navbar-start" in html
    assert "navbar-end" in html


def test_breadcrumb_uses_daisy_breadcrumbs_class(render):
    html = render("Breadcrumb.jinja", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumbs' in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(render):
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], content="C")
    assert 'x-data="cfTabs"' in html
    # The id reaches Alpine as data, never as expression text (#32).
    assert 'data-cf-tab="one"' in html
    assert "setActive($el.dataset.cfTab)" in html
    assert "tab-active" in html
