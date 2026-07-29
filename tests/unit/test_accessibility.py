"""Accessibility contract for the interactive components (issue #21).

Scope split, deliberately:

* **Here** live the claims that *are* markup — a role, an ``aria-*`` value, a
  server-rendered class. Asserting those against the rendered string is not a
  proxy for anything; it is the thing itself.
* **In ``tests/e2e/``** live the claims that are behavior — where focus lands,
  whether it can escape, whether Escape closes. Issue #21 is explicit that a
  test asserting ``role="dialog"`` is present proves nothing about focus, so
  no test in this module pretends otherwise.

Every case runs against all four template sets (2 engines x 2 themes). The
point of the phase is a pattern the three themes in the expansion epic copy;
a fix that landed in one set and not the others would be worse than none.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui" / "templates"
JINJA_DIR = TEMPLATES_DIR / "jinja"

THEMES = ["bulma", "daisy", "fomantic"]

#: The class each theme puts on the *selected* tab, and the element it sits on.
#: Bulma marks the ``<li>``; DaisyUI and Fomantic mark the ``<a role="tab">``
#: itself. Fomantic's marker is the bare word ``active``, which is why every
#: assertion below matches on whole class *tokens* rather than substrings.
ACTIVE_TAB_CLASS = {"bulma": "is-active", "daisy": "tab-active", "fomantic": "active"}


@pytest.fixture(params=THEMES)
def theme(request) -> str:
    return request.param


@pytest.fixture
def jinja_render(theme: str) -> Callable[..., str]:
    """Render a JinjaX component file through plain Jinja2, for one theme.

    Plain Jinja2 with ``StrictUndefined`` rather than a JinjaX ``Catalog``,
    for the same reason the rest of ``tests/unit/jinja`` does: it is the
    harsher environment. ``{#def}`` defaults do not apply here, so every
    template has to carry its own ``is defined`` guards to pass.
    """
    env = Environment(
        loader=FileSystemLoader(JINJA_DIR / theme),
        autoescape=select_autoescape(["html", "jinja"]),
        undefined=StrictUndefined,
    )

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render


@pytest.fixture
def cotton_render(settings, theme: str) -> Callable[..., str]:
    """Render a public cotton wrapper with ``CF_UI_THEME`` set to ``theme``.

    ``render_to_string`` bypasses the django-cotton compiler, so ``<c-vars>``
    defaults never apply — props are passed explicitly here and the E2E tier
    is what exercises real ``<c-vars>`` resolution.
    """
    from django.template.loader import render_to_string

    settings.CF_UI_THEME = theme

    def _render(stem: str, **props: object) -> str:
        return render_to_string(f"cotton/cf/{stem}.html", props)

    return _render


def _attrs(html: str, tag_marker: str) -> str:
    """Return the opening tag containing ``tag_marker``, attributes included."""
    for match in re.finditer(r"<[a-zA-Z][^>]*>", html, re.DOTALL):
        if tag_marker in match.group(0):
            return match.group(0)
    raise AssertionError(f"no opening tag containing {tag_marker!r} in:\n{html}")


# ── 1. Modal: dialog semantics ────────────────────────────────────────────


def test_jinja_modal_declares_dialog_semantics(jinja_render):
    html = jinja_render("Modal.jinja", id="m", header="", footer="", content="", extra_class="")
    root = _attrs(html, 'id="m"')
    assert 'role="dialog"' in root
    assert 'aria-modal="true"' in root


def test_cotton_modal_declares_dialog_semantics(cotton_render):
    html = cotton_render("modal", id="m", header="", footer="", label="", **{"class": ""})
    root = _attrs(html, 'id="m"')
    assert 'role="dialog"' in root
    assert 'aria-modal="true"' in root


def test_jinja_modal_labels_itself_by_its_header(jinja_render):
    html = jinja_render(
        "Modal.jinja", id="m", header="Delete file", footer="", content="", extra_class=""
    )
    assert 'aria-labelledby="m-title"' in _attrs(html, 'id="m"')
    assert 'id="m-title"' in html, "nothing carries the id aria-labelledby points at"


def test_cotton_modal_labels_itself_by_its_header(cotton_render):
    html = cotton_render(
        "modal", id="m", header="Delete file", footer="", label="", **{"class": ""}
    )
    assert 'aria-labelledby="m-title"' in _attrs(html, 'id="m"')
    assert 'id="m-title"' in html, "nothing carries the id aria-labelledby points at"


def test_jinja_modal_falls_back_to_aria_label_without_a_header(jinja_render):
    """An empty aria-labelledby target is worse than no labelling at all."""
    html = jinja_render(
        "Modal.jinja", id="m", header="", footer="", content="", label="Settings", extra_class=""
    )
    root = _attrs(html, 'id="m"')
    assert 'aria-label="Settings"' in root
    assert "aria-labelledby" not in root


def test_cotton_modal_falls_back_to_aria_label_without_a_header(cotton_render):
    html = cotton_render("modal", id="m", header="", footer="", label="Settings", **{"class": ""})
    root = _attrs(html, 'id="m"')
    assert 'aria-label="Settings"' in root
    assert "aria-labelledby" not in root


def test_jinja_modal_aria_label_has_a_default(jinja_render):
    """No header and no label must still leave the dialog named."""
    html = jinja_render("Modal.jinja", id="m", header="", footer="", content="", extra_class="")
    assert re.search(r'aria-label="[^"]+"', _attrs(html, 'id="m"'))


def test_cotton_modal_aria_label_has_a_default(cotton_render):
    html = cotton_render("modal", id="m", header="", footer="", **{"class": ""})
    assert re.search(r'aria-label="[^"]+"', _attrs(html, 'id="m"'))


def test_cotton_modal_wrapper_declares_the_label_prop():
    """The fallback is only reachable if <c-vars> lets a consumer pass it."""
    source = (TEMPLATES_DIR / "cotton" / "cf" / "modal.html").read_text(encoding="utf-8")
    assert "label" in source.split("/>")[0]


@pytest.mark.parametrize("theme", THEMES)
def test_no_modal_template_implements_focus_itself(theme):
    """#21: all focus behavior in cf_ui_alpine.js, not per template.

    Five themes copying five slightly-different focus traps is the failure
    mode this checks for.
    """
    sources = [
        (JINJA_DIR / theme / "Modal.jinja").read_text(encoding="utf-8"),
        (TEMPLATES_DIR / "cotton" / "_themes" / theme / "modal.html").read_text(encoding="utf-8"),
    ]
    for source in sources:
        assert ".focus()" not in source
        assert "keydown" not in source


# ── 2. Tabs: server-rendered state ────────────────────────────────────────

TABS = [{"id": "one", "url": "/one/"}, {"id": "two", "url": "/two/"}]


def _tab_tags(html: str) -> list[str]:
    return re.findall(r'<a[^>]*role="tab"[^>]*>', html)


def test_jinja_tabs_render_the_active_tab_without_js(jinja_render, theme):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    marker = ACTIVE_TAB_CLASS[theme]
    assert html.count(marker) >= 1, "no tab carries the active class server-side"
    # Exactly one, in the static markup — Alpine is not running here.
    static_classes = re.findall(r'\sclass="([^"]*)"', html)
    assert sum(1 for c in static_classes if marker in c.split()) == 1


def test_cotton_tabs_render_the_active_tab_without_js(cotton_render, theme):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    marker = ACTIVE_TAB_CLASS[theme]
    static_classes = re.findall(r'\sclass="([^"]*)"', html)
    assert sum(1 for c in static_classes if marker in c.split()) == 1


def test_jinja_tabs_mark_no_tab_active_when_no_active_prop(jinja_render, theme):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="", content="", extra_class=""
    )
    marker = ACTIVE_TAB_CLASS[theme]
    static_classes = re.findall(r'\sclass="([^"]*)"', html)
    assert not [c for c in static_classes if marker in c.split()]


def test_jinja_tabs_keep_the_alpine_binding(jinja_render, theme):
    """Server state is the initial value, not a replacement (#21)."""
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    assert ":class=" in html
    assert "cfTabs" in html


def test_cotton_tabs_keep_the_alpine_binding(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    assert ":class=" in html
    assert "cfTabs" in html


def test_jinja_tabs_seed_alpine_from_a_data_attribute(jinja_render):
    """The initial value crosses into Alpine as data, never as expression text.

    ``x-data="cfTabs('{{ active }}')"`` would splice a request-controlled
    string into an evaluated expression; an apostrophe alone breaks out of it.
    A ``data-`` attribute is escaped by the template engine like any other.
    """
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    assert 'data-cf-active="two"' in html
    assert "cfTabs(" not in html


def test_cotton_tabs_seed_alpine_from_a_data_attribute(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    assert 'data-cf-active="two"' in html
    assert "cfTabs(" not in html


def test_jinja_tabs_escape_a_hostile_active_value(jinja_render):
    html = jinja_render(
        "Tabs.jinja",
        tabs=TABS,
        hx_target="tc",
        active="' + alert(1) + '",
        content="",
        extra_class="",
    )
    value = re.search(r'data-cf-active="([^"]*)"', html)
    assert value, "no data-cf-active attribute to escape into"
    assert "'" not in value.group(1), "a raw apostrophe survived into the attribute"


def test_jinja_tabs_expose_the_tablist_roles(jinja_render):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="one", content="", extra_class=""
    )
    assert 'role="tablist"' in html
    assert len(_tab_tags(html)) == len(TABS)
    assert 'role="tabpanel"' in html


def test_cotton_tabs_expose_the_tablist_roles(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="one", **{"class": ""})
    assert 'role="tablist"' in html
    assert len(_tab_tags(html)) == len(TABS)
    assert 'role="tabpanel"' in html


def test_jinja_tabs_render_aria_selected_server_side(jinja_render):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    tags = _tab_tags(html)
    assert 'aria-selected="false"' in tags[0]
    assert 'aria-selected="true"' in tags[1]


def test_cotton_tabs_render_aria_selected_server_side(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    tags = _tab_tags(html)
    assert 'aria-selected="false"' in tags[0]
    assert 'aria-selected="true"' in tags[1]


def test_jinja_tabs_point_aria_controls_at_the_panel(jinja_render):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="one", content="", extra_class=""
    )
    for tag in _tab_tags(html):
        assert 'aria-controls="tc"' in tag
    assert 'id="tc"' in html, "aria-controls points at an id nothing carries"


def test_cotton_tabs_point_aria_controls_at_the_panel(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="one", **{"class": ""})
    for tag in _tab_tags(html):
        assert 'aria-controls="tc"' in tag
    assert 'id="tc"' in html


def test_jinja_tabs_use_a_roving_tabindex(jinja_render):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    tags = _tab_tags(html)
    assert 'tabindex="-1"' in tags[0]
    assert 'tabindex="0"' in tags[1]


def test_cotton_tabs_use_a_roving_tabindex(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    tags = _tab_tags(html)
    assert 'tabindex="-1"' in tags[0]
    assert 'tabindex="0"' in tags[1]


def test_jinja_tabs_stay_keyboard_reachable_with_no_active_tab(jinja_render):
    """A roving tabindex with nothing at 0 removes the whole widget from the
    tab order. These anchors have no href, so tabindex is the only thing
    making them focusable at all."""
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="", content="", extra_class=""
    )
    tags = _tab_tags(html)
    assert 'tabindex="0"' in tags[0]
    assert 'tabindex="-1"' in tags[1]


def test_cotton_tabs_stay_keyboard_reachable_with_no_active_tab(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="", **{"class": ""})
    tags = _tab_tags(html)
    assert 'tabindex="0"' in tags[0]
    assert 'tabindex="-1"' in tags[1]


def test_cotton_tabs_wrapper_declares_the_active_prop():
    source = (TEMPLATES_DIR / "cotton" / "cf" / "tabs.html").read_text(encoding="utf-8")
    assert "active" in source.split("/>")[0]


@pytest.mark.parametrize("theme", THEMES)
def test_tab_keyboard_handling_lives_in_alpine(theme):
    """Roving-tabindex arrow keys belong in cf_ui_alpine.js, same as the modal."""
    for source in (
        (JINJA_DIR / theme / "Tabs.jinja").read_text(encoding="utf-8"),
        (TEMPLATES_DIR / "cotton" / "_themes" / theme / "tabs.html").read_text(encoding="utf-8"),
    ):
        assert "onKeydown($event)" in source
        assert "ArrowRight" not in source


# ── 3. Panel: server-rendered open state ──────────────────────────────────


def test_jinja_panel_renders_its_body_visible_when_open(jinja_render):
    """x-cloak on a server-open panel hides it forever without JS."""
    html = jinja_render("Panel.jinja", id="p", title="T", content="Body", open=True, extra_class="")
    assert "x-cloak" not in html


def test_jinja_panel_cloaks_its_body_when_closed(jinja_render):
    html = jinja_render(
        "Panel.jinja", id="p", title="T", content="Body", open=False, extra_class=""
    )
    assert "x-cloak" in html


def test_cotton_panel_renders_its_body_visible_when_open(cotton_render):
    html = cotton_render("panel", id="p", title="T", open="true", **{"class": ""})
    assert "x-cloak" not in html


def test_cotton_panel_cloaks_its_body_when_closed(cotton_render):
    html = cotton_render("panel", id="p", title="T", open="", **{"class": ""})
    assert "x-cloak" in html


def test_jinja_panel_seeds_alpine_from_a_data_attribute(jinja_render):
    html = jinja_render("Panel.jinja", id="p", title="T", content="Body", open=True, extra_class="")
    assert 'data-cf-open="true"' in html
    assert "cfPanel(" not in html


def test_cotton_panel_seeds_alpine_from_a_data_attribute(cotton_render):
    html = cotton_render("panel", id="p", title="T", open="true", **{"class": ""})
    assert 'data-cf-open="true"' in html
    assert "cfPanel(" not in html


def test_jinja_panel_toggle_declares_aria_expanded_and_controls(jinja_render):
    html = jinja_render(
        "Panel.jinja", id="p", title="T", content="Body", open=False, extra_class=""
    )
    toggle = _attrs(html, "aria-controls=")
    assert 'aria-controls="p-body"' in toggle
    assert 'aria-expanded="false"' in toggle
    assert ':aria-expanded="open"' in toggle, "the Alpine binding must survive"
    assert 'id="p-body"' in html, "aria-controls points at an id nothing carries"


def test_cotton_panel_toggle_declares_aria_expanded_and_controls(cotton_render):
    html = cotton_render("panel", id="p", title="T", open="", **{"class": ""})
    toggle = _attrs(html, "aria-controls=")
    assert 'aria-controls="p-body"' in toggle
    assert 'aria-expanded="false"' in toggle
    assert ':aria-expanded="open"' in toggle
    assert 'id="p-body"' in html


def test_jinja_panel_reports_expanded_when_server_open(jinja_render):
    html = jinja_render("Panel.jinja", id="p", title="T", content="Body", open=True, extra_class="")
    assert 'aria-expanded="true"' in _attrs(html, "aria-controls=")


def test_cotton_panel_reports_expanded_when_server_open(cotton_render):
    html = cotton_render("panel", id="p", title="T", open="true", **{"class": ""})
    assert 'aria-expanded="true"' in _attrs(html, "aria-controls=")


def test_cotton_panel_wrapper_declares_id_and_open():
    source = (TEMPLATES_DIR / "cotton" / "cf" / "panel.html").read_text(encoding="utf-8")
    header = source.split("/>")[0]
    assert "id" in header
    assert "open" in header


@pytest.mark.parametrize("theme", THEMES)
def test_panel_toggle_is_a_real_button(theme):
    """A div with a click handler is not reachable by keyboard."""
    for source in (
        (JINJA_DIR / theme / "Panel.jinja").read_text(encoding="utf-8"),
        (TEMPLATES_DIR / "cotton" / "_themes" / theme / "panel.html").read_text(encoding="utf-8"),
    ):
        assert 'type="button"' in source
