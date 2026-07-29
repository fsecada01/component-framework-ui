"""Fomantic UI component set, Jinja2/JinjaX side (issue #24).

Same shape as ``test_daisy.py``: the Jinja theme switch is directory-based, so
this tier proves the ``fomantic`` directory ships all 14 components, that they
render under ``StrictUndefined``, and that they speak Fomantic's class
vocabulary rather than Bulma's or DaisyUI's.

Two things are specific to this theme and are asserted here rather than left to
review:

* **No jQuery, no Fomantic JS.** Fomantic's Modal, Tab, Accordion and Dropdown
  are jQuery plugins. cf-ui's behavioural contract is Alpine, and a theme that
  dragged jQuery in would make a *styling* choice change a consuming app's
  dependency graph. The templates therefore use Fomantic's classes and markup
  structure only.
* **State classes Fomantic's JS would normally add** — ``active`` on the modal
  and its dimmer, on the accordion title/content, on the tabular menu item —
  are server-rendered and Alpine-bound instead.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates"
FOMANTIC_DIR = TEMPLATES_DIR / "jinja" / "fomantic"
COTTON_FOMANTIC_DIR = TEMPLATES_DIR / "cotton" / "_themes" / "fomantic"

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
        loader=FileSystemLoader(FOMANTIC_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render


# --- Parity with the Bulma set ---------------------------------------------


def test_fomantic_ships_the_same_components_as_bulma():
    bulma_dir = FOMANTIC_DIR.parent / "bulma"
    assert sorted(p.name for p in FOMANTIC_DIR.glob("*.jinja")) == sorted(
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


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_carries_no_daisy_class_names(render, name):
    html = render(f"{name}.jinja", **REQUIRED_PROPS[name])
    for daisy_marker in ("form-control", "input-bordered", "modal-box", "join-item", "alert-"):
        assert daisy_marker not in html, f"{name} still speaks DaisyUI"


# --- The whole point of the theme: no jQuery, no Fomantic JS ---------------


@pytest.mark.parametrize(
    "path",
    sorted([*FOMANTIC_DIR.glob("*.jinja"), *COTTON_FOMANTIC_DIR.glob("*.html")]),
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_no_fomantic_template_reaches_for_jquery_or_fomantic_js(path):
    """Adding jQuery for one theme would change a consuming app's deps.

    Fomantic's Modal/Tab/Accordion/Dropdown are jQuery plugins; Alpine owns all
    of that behaviour in cf-ui, for every theme.

    Template comments are stripped first — Jinja's ``{# #}`` and Django's
    ``{% comment %}`` both. Several of these templates explain in prose *which*
    jQuery module they are standing in for, and a guard that forbade naming the
    thing would push that reasoning out of the code.
    """
    source = path.read_text(encoding="utf-8")
    source = re.sub(r"\{#.*?#\}", "", source, flags=re.DOTALL)
    source = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", source, flags=re.DOTALL)
    source = source.lower()
    for forbidden in ("jquery", "semantic.min.js", "semantic.js", "fomantic.min.js", "$("):
        assert forbidden not in source, f"{path.name} pulls in {forbidden!r}"


def test_the_fomantic_template_set_is_complete():
    """Without this, the scan above could silently degrade to zero cases."""
    found = [*FOMANTIC_DIR.glob("*.jinja"), *COTTON_FOMANTIC_DIR.glob("*.html")]
    assert len(found) == 28, f"expected 14 jinja + 14 cotton, got {sorted(p.name for p in found)}"


# --- Forms -----------------------------------------------------------------


def test_form_field_uses_fomantic_form_classes(render):
    html = render("FormField.jinja", name="email", label="Email")
    assert "ui form" in html
    assert 'class="field' in html
    assert "ui fluid input" in html
    assert 'name="email"' in html


def test_form_field_error_marks_the_field_and_prompts(render):
    """Fomantic styles the input through `.ui.form .field.error`."""
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "field error" in html
    assert "ui basic red pointing prompt label" in html
    assert "Required" in html


def test_form_field_error_does_not_use_a_ui_error_message(render):
    """`.ui.form .error.message` is `display:none` until the *form* has .error.

    A prompt label is the element Fomantic actually shows for a field error.
    """
    html = render("FormField.jinja", name="email", label="Email", error="Required")
    assert "ui error message" not in html


def test_form_field_input_class_still_applied(render):
    html = render("FormField.jinja", name="email", label="Email", input_class="mini")
    assert "mini" in html


def test_form_field_required_flag(render):
    html = render("FormField.jinja", name="email", label="Email", required=True)
    assert "required" in html


def test_select_uses_a_plain_styled_select(render):
    """Fomantic's `ui dropdown` widget is JS-built; the contract is a control.

    A real `<select>` styled with `ui fluid selection dropdown` degrades to a
    working form control with no JS at all.
    """
    html = render(
        "Select.jinja", name="c", label="C", options=[{"value": "a", "label": "Option A"}]
    )
    assert "<select" in html
    assert "ui fluid selection dropdown" in html
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


def test_textarea_uses_fomantic_field_markup(render):
    html = render("Textarea.jinja", name="bio", label="Bio", value="Hello")
    assert "ui form" in html
    assert "<textarea" in html
    assert "Hello" in html


def test_checkbox_group_uses_fomantic_checkbox_class(render):
    html = render(
        "CheckboxGroup.jinja",
        name="f",
        label="F",
        choices=[{"value": "a", "label": "Apple"}],
        selected=["a"],
    )
    assert "ui checkbox" in html
    assert "checked" in html
    assert "Apple" in html


def test_checkbox_group_labels_are_associated_with_their_inputs(render):
    """Fomantic's CSS-only checkbox relies on an overlay input; a reader does not."""
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="F",
        choices=[{"value": "a", "label": "Apple"}],
    )
    assert 'id="fruits-1"' in html
    assert 'for="fruits-1"' in html


# --- Feedback --------------------------------------------------------------


def test_modal_keeps_the_alpine_contract(render):
    html = render("Modal.jinja", id="my-modal")
    assert 'id="my-modal"' in html
    assert 'x-data="cfModal"' in html
    assert "initModal" in html
    assert "close()" in html


def test_modal_renders_its_own_dimmer(render):
    """`$('.ui.modal').modal('show')` builds the dimmer; we render it instead."""
    html = render("Modal.jinja", id="m")
    assert "ui page dimmer" in html
    assert "ui modal" in html


def test_modal_toggles_the_active_class_from_alpine(render):
    """Both `.ui.dimmer` and `.ui.modal` are display:none until `.active`."""
    html = render("Modal.jinja", id="m")
    assert html.count("{ 'active': open }") == 2


def test_modal_renders_header_content_and_actions(render):
    html = render("Modal.jinja", id="m", header="Head", content="Body", footer="Foot")
    assert 'class="header"' in html
    assert 'class="content"' in html
    assert 'class="actions"' in html
    assert "Head" in html and "Body" in html and "Foot" in html


def test_notification_maps_danger_to_fomantic_negative(render):
    """Fomantic has no `message-danger`; the prop vocabulary stays stable."""
    html = render("Notification.jinja", message="Boom", type="danger")
    assert "ui negative message" in html
    assert "message ui" not in html, "Fomantic's class order is conventionally ui-first"


def test_notification_success_maps_to_positive_and_dismisses(render):
    html = render("Notification.jinja", message="Saved!", type="success", dismissible=True)
    assert "ui positive message" in html
    assert "Saved!" in html
    assert "visible = false" in html


def test_notification_warning_and_info(render):
    assert "ui warning message" in render("Notification.jinja", message="M", type="warning")
    assert "ui info message" in render("Notification.jinja", message="M", type="info")


def test_notification_non_dismissible_omits_the_button(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=False)
    assert "visible = false" not in html


def test_progress_uses_fomantic_progress_markup(render):
    """`.ui.progress` needs a `.bar` child, and a bar with no width shows nothing."""
    html = render("Progress.jinja", value=40, max=100, type="primary")
    assert "ui blue progress" in html
    assert 'class="bar"' in html
    assert "width:40%" in html.replace(" ", "")


def test_progress_emits_data_percent(render):
    """`.ui.progress:not([data-percent]) .bar` is given a transparent background."""
    html = render("Progress.jinja", value=40, max=100)
    assert 'data-percent="40"' in html


def test_progress_maps_danger_to_error(render):
    html = render("Progress.jinja", value=75, max=100, type="danger")
    assert "ui error progress" in html


def test_progress_declares_progressbar_semantics(render):
    """A div is not a `<progress>` — the ARIA has to be written out."""
    html = render("Progress.jinja", value=40, max=100)
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert 'aria-valuemin="0"' in html
    assert 'aria-valuemax="100"' in html


def test_progress_survives_a_zero_max(render):
    html = render("Progress.jinja", value=0, max=0)
    assert 'data-percent="0"' in html


def test_progress_clamps_a_value_above_max(render):
    """Bulma and Daisy get this free from ``<progress>``; a div does not.

    A native ``<progress value="150" max="100">`` renders full and reports 100%
    to assistive tech. Fomantic has no native element behind it, so an
    unclamped percentage would emit ``width: 150%`` — a bar wider than its
    track — and ``aria-valuenow="150"`` against ``aria-valuemax="100"``, which
    is invalid.
    """
    html = render("Progress.jinja", value=150, max=100, label="L")
    assert 'data-percent="100"' in html
    assert "width:100%" in html.replace(" ", "")
    assert 'aria-valuenow="100"' in html
    assert "150" not in html


def test_progress_clamps_a_negative_value(render):
    html = render("Progress.jinja", value=-10, max=100, label="L")
    assert 'data-percent="0"' in html
    assert "width:0%" in html.replace(" ", "")
    assert 'aria-valuenow="0"' in html
    assert "-10" not in html


# --- Content + navigation --------------------------------------------------


def test_card_renders_header_body_footer(render):
    html = render("Card.jinja", header="Title", content="Body", footer="Foot")
    assert "ui card" in html
    assert 'class="header"' in html
    assert 'class="description"' in html
    assert 'class="extra content"' in html
    assert "Title" in html and "Body" in html and "Foot" in html


def test_table_uses_fomantic_table_classes(render):
    html = render("Table.jinja", columns=[{"key": "n", "label": "Name"}], rows=[{"n": "Ada"}])
    assert "ui celled striped table" in html
    assert "is-striped" not in html
    assert "Name" in html
    assert "Ada" in html


def test_pagination_uses_the_pagination_menu(render):
    html = render("Pagination.jinja", page=2, total_pages=3, hx_url="/x", hx_target="#t")
    assert "ui pagination menu" in html
    assert "active item" in html
    assert 'aria-current="page"' in html


def test_pagination_disables_the_edges(render):
    html = render("Pagination.jinja", page=1, total_pages=1, hx_url="/x", hx_target="#t")
    assert "disabled item" in html
    assert 'aria-disabled="true"' in html


def test_panel_uses_the_accordion_vocabulary(render):
    html = render("Panel.jinja", title="Details", content="Inner", open=False)
    assert "ui styled fluid accordion" in html
    assert 'class="title"' in html
    assert 'x-data="cfPanel"' in html
    assert "x-cloak" in html
    assert "Inner" in html


def test_panel_body_carries_the_active_class_when_open(render):
    """`.ui.accordion .title~.content:not(.active)` is display:none.

    x-show alone would not be enough: Alpine removing its inline style leaves
    the CSS rule in force, so the open state has to be a class as well.
    """
    html = render("Panel.jinja", id="p", title="T", content="Body", open=True)
    assert "content active" in html
    assert "{ 'active': open }" in html


def test_panel_body_omits_the_active_class_when_closed(render):
    html = render("Panel.jinja", id="p", title="T", content="Body", open=False)
    assert "content active" not in html


def test_navbar_keeps_the_alpine_contract(render):
    html = render("Navbar.jinja", brand="Brand", start="S", end="E")
    assert 'x-data="cfNavbar"' in html
    assert "toggle()" in html
    assert "ui stackable menu" in html
    assert "Brand" in html and "S" in html and "E" in html


def test_breadcrumb_uses_fomantic_breadcrumb_markup(render):
    html = render(
        "Breadcrumb.jinja", items=[{"url": "/a", "label": "A"}, {"url": "/b", "label": "B"}]
    )
    assert "ui breadcrumb" in html
    assert 'class="divider"' in html
    assert "active section" in html
    assert 'aria-current="page"' in html


def test_tabs_keeps_the_alpine_contract(render):
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], content="C")
    assert 'x-data="cfTabs"' in html
    assert "setActive('one')" in html
    assert "ui top attached tabular menu" in html


def test_tabs_panel_is_not_given_the_hidden_ui_tab_class(render):
    """`.ui.tab` is display:none until `.active` — the panel is always shown."""
    html = render("Tabs.jinja", tabs=[{"id": "one", "url": "/one"}], content="C", active="one")
    assert "ui bottom attached segment" in html
    assert 'class="ui tab' not in html
