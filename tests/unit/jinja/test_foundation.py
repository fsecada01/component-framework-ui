"""Foundation 6 component set, Jinja2/JinjaX side (issue #23).

The Jinja theme switch is directory-based — ``install_cf_ui`` registers
``templates/jinja/<theme>/`` — so this tier proves the foundation directory
ships all 14 components, that they render under ``StrictUndefined``, and that
they speak Foundation's class vocabulary rather than Bulma's.

The theme is **CSS only**: Foundation's Reveal, Tabs, Accordion and Dropdown
Menu are jQuery plugins, and adding jQuery would make a theme choice change a
consuming app's dependency graph. Alpine keeps owning behaviour, so several
tests here pin *which* Foundation state mechanism each component uses, because
Foundation's are not uniform:

* ``.tabs-panel``/``.is-active`` is a real CSS rule — bindable.
* ``.reveal`` and ``.reveal-overlay`` are ``display: none`` with **no**
  counterpart rule; the plugin opens them by writing an inline ``display``.
  So does this theme, via ``:style``.
* ``.accordion-content`` is ``display: none`` with no un-hiding rule at all,
  which is why the panel is built from ``card``/``card-section`` instead.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

FOUNDATION_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "cf_ui"
    / "templates"
    / "jinja"
    / "foundation"
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

# Bulma tokens that must not survive the port. `is-active` is deliberately
# absent: Foundation uses it too (`.tabs-title.is-active`), so asserting on it
# would forbid the correct markup.
BULMA_MARKERS = (
    "is-danger",
    "card-header-title",
    "navbar-burger",
    "modal-card",
    "pagination-link",
)


@pytest.fixture
def render() -> Callable[..., str]:
    env = Environment(
        loader=FileSystemLoader(FOUNDATION_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render


# --- Parity with the Bulma set ---------------------------------------------


def test_foundation_ships_the_same_components_as_bulma():
    bulma_dir = FOUNDATION_DIR.parent / "bulma"
    assert sorted(p.name for p in FOUNDATION_DIR.glob("*.jinja")) == sorted(
        p.name for p in bulma_dir.glob("*.jinja")
    )


def test_the_planned_stub_is_gone():
    """The stub and a real component set must not coexist."""
    assert not (FOUNDATION_DIR / "PLANNED.md").exists()


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_renders_with_only_its_required_props(render, name):
    """StrictUndefined: every optional prop needs an is-defined guard."""
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    assert html.strip()


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_carries_no_bulma_class_names(render, name):
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    for marker in BULMA_MARKERS:
        assert marker not in html, f"{name} still speaks Bulma"


# --- The CSS-only constraint (#23) -----------------------------------------


@pytest.mark.parametrize("name", COMPONENTS)
def test_no_component_reaches_for_foundation_js(render, name):
    """No jQuery, and no `data-` hooks that only Foundation's plugins read.

    A theme that quietly required jQuery would change a consuming app's
    dependency graph as a side effect of a `CF_UI_THEME` edit.
    """
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name]).lower()
    assert "jquery" not in html
    for plugin_hook in (
        "data-reveal",
        "data-toggler",
        "data-closable",
        "data-accordion",
        "data-tabs",
        "data-dropdown-menu",
        "data-responsive-toggle",
        "data-abide",
    ):
        assert plugin_hook not in html, f"{name} depends on a Foundation plugin"


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_foundation_error_classes(render):
    """Foundation's Abide plugin only ever adds these three classes.

    Server-rendering them is a complete substitute for running it.
    """
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "is-invalid-input" in html
    assert "is-invalid-label" in html
    assert "Required" in html


def test_form_field_error_text_is_visible(render):
    """`.form-error` is `display: none` until `.is-visible` joins it.

    Emitting the error text without it renders an invisible error message —
    the failure mode is silent, which is why this is pinned.
    """
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "form-error is-visible" in html


def test_form_field_without_an_error_stays_clean(render):
    html = render("FormField.jinja", name="email", label="Email")
    assert "is-invalid-input" not in html
    assert "form-error" not in html
    assert 'name="email"' in html


def test_form_field_input_class_still_applied(render):
    html = render("FormField.jinja", name="email", label="Email", input_class="my-input")
    assert "my-input" in html


def test_select_marks_the_current_value(render):
    html = render(
        "Select.jinja",
        name="c",
        label="C",
        value="a",
        options=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
    )
    assert "selected" in html


def test_select_error_uses_the_invalid_input_class(render):
    html = render(
        "Select.jinja",
        name="c",
        label="C",
        error="Pick one",
        options=[{"value": "a", "label": "Option A"}],
    )
    assert "is-invalid-input" in html
    assert "Option A" in html


def test_textarea_error_uses_the_invalid_input_class(render):
    html = render("Textarea.jinja", name="bio", label="Bio", value="Hello", error="Too short")
    assert "is-invalid-input" in html
    assert "Hello" in html


def test_checkbox_group_uses_a_fieldset(render):
    """Foundation groups checkboxes in a `fieldset`/`legend`, not a bare label."""
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="Fruits",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert 'class="fieldset' in html
    assert "<legend" in html
    assert "Fruits" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_point_at_their_own_input(render):
    """Foundation's convention is sibling `input` + `label[for]`, so the ids
    have to be unique per choice or every label targets the first box."""
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
        selected=[],
    )
    assert 'id="f-1"' in html
    assert 'for="f-1"' in html
    assert 'id="f-2"' in html
    assert 'for="f-2"' in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(render):
    html = render("Modal.jinja", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_uses_foundation_reveal_classes(render):
    html = render("Modal.jinja", id="m")
    assert "reveal-overlay" in html
    assert 'class="reveal' in html


def test_modal_toggles_an_inline_display_not_a_class(render):
    """Foundation ships no open-state class for `.reveal`.

    Both `.reveal` and `.reveal-overlay` are `display: none` in the stylesheet
    and the jQuery plugin opens them by writing an inline `display`. `x-show`
    cannot do it — showing only *removes* the inline property, which falls back
    to the rule that hid it. So the binding has to be `:style`.
    """
    html = render("Modal.jinja", id="m")
    assert ":style=" in html
    assert "display: block" in html
    assert "x-show" not in html


# --- Content + navigation --------------------------------------------------


def test_card_uses_foundation_card_sections(render):
    """Foundation has no `.card-footer`; a trailing `.card-divider` is it."""
    html = render("Card.jinja", header="Title", content="Body", footer="Foot")
    assert "card-section" in html
    assert "card-divider" in html
    assert "Title" in html
    assert "Body" in html
    assert "Foot" in html


def test_notification_maps_danger_to_the_alert_callout(render):
    """Foundation's error variant is a bare `alert`, with no `is-` prefix."""
    html = render("Notification.jinja", message="Boom", type="danger")
    assert "callout alert" in html
    assert "is-danger" not in html
    assert "alert-error" not in html


def test_notification_maps_info_to_primary(render):
    """Foundation's callout has no `info` variant; `primary` is the stand-in."""
    html = render("Notification.jinja", message="Hi", type="info")
    assert "callout primary" in html


def test_notification_success_and_dismiss(render):
    html = render("Notification.jinja", message="Saved!", type="success", dismissible=True)
    assert "callout success" in html
    assert "Saved!" in html
    assert "visible = false" in html
    assert "close-button" in html


def test_notification_non_dismissible_omits_the_button(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=False)
    assert "visible = false" not in html


def test_progress_uses_a_meter_child(render):
    """Foundation 6.7.5 does not style a native `<progress>` element.

    Its compiled CSS gives bare `progress` only `vertical-align: baseline`;
    every colour rule is `.progress.<variant> .progress-meter`, which needs a
    child element the native control cannot have.
    """
    html = render("Progress.jinja", value=40, max=100, type="primary")
    assert "progress-meter" in html
    assert "width: 40%" in html
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert 'aria-valuemax="100"' in html


def test_progress_maps_danger_to_alert(render):
    html = render("Progress.jinja", value=75, max=100, type="danger")
    assert "progress alert" in html


def test_progress_survives_a_zero_max(render):
    """A division by zero here would be a 500 on an empty result set."""
    html = render("Progress.jinja", value=0, max=0)
    assert "width: 0%" in html


def test_table_uses_the_scroll_wrapper(render):
    html = render("Table.jinja", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}])
    assert "table-scroll" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_foundation_list_classes(render):
    html = render("Pagination.jinja", page=2, total_pages=3, hx_url="/x", hx_target="#t")
    assert "pagination-previous" in html
    assert "pagination-next" in html
    assert 'class="current"' in html
    assert 'aria-current="page"' in html


def test_pagination_disables_the_edges(render):
    html = render("Pagination.jinja", page=1, total_pages=1, hx_url="/x", hx_target="#t")
    assert "pagination-previous disabled" in html
    assert "pagination-next disabled" in html


def test_panel_keeps_the_alpine_contract(render):
    html = render("Panel.jinja", title="Details", content="Inner")
    assert 'x-data="cfPanel"' in html
    assert "x-show" in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_panel_avoids_the_accordion(render):
    """`.accordion-content` is `display: none` with no un-hiding rule.

    Foundation's plugin opens it with an inline `slideDown()`, so a
    server-open accordion panel would be invisible with Alpine off — exactly
    what the accessibility phase forbids. `card-section` has no such rule.
    """
    html = render("Panel.jinja", title="T", content="Inner", open=True)
    assert "accordion-content" not in html
    assert "card-section" in html


def test_navbar_keeps_the_alpine_contract(render):
    html = render("Navbar.jinja", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "toggle()" in html
    assert "top-bar-left" in html
    assert "top-bar-right" in html


def test_navbar_menu_stays_visible_on_desktop_when_collapsed(render):
    """`hide-for-small-only`, not `hide`.

    `.hide` is `display: none !important` at every width, so binding it to
    `!menuOpen` would collapse the desktop menu too. The breakpoint-scoped
    class is the one that reproduces what Foundation's own responsive toggle
    does — and with Alpine off no class is emitted at all, so the menu is
    simply visible.
    """
    html = render("Navbar.jinja", brand="Brand", start="S", end="E")
    assert "hide-for-small-only" in html
    assert "'hide':" not in html


def test_breadcrumb_uses_foundation_breadcrumbs_class(render):
    html = render("Breadcrumb.jinja", items=[{"url": "/a", "label": "A"}])
    assert 'class="breadcrumbs' in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(render):
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], content="C")
    assert 'x-data="cfTabs"' in html
    assert "setActive('one')" in html
    assert "tabs-title" in html


def test_tabs_bind_aria_selected_because_the_css_reads_it(render):
    """`.tabs-title > a[aria-selected=true]` is what restyles the active tab.

    `.is-active` on the `<li>` alone changes nothing visually, so the aria
    attribute is load-bearing for appearance here, not only for the reader.
    """
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], active="one", content="C")
    assert 'aria-selected="true"' in html
    assert ":aria-selected=" in html
