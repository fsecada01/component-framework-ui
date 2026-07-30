"""Attribute escaping on the JinjaX path, against a real catalog (#36).

Every other Jinja test in the suite builds its own ``Environment``, so what it
asserts is a property of the harness. This file builds the catalog the way
``install_cf_ui``'s own docstring tells a consumer to and asserts against that,
which is the only place the shipped configuration is actually under test.

The gap this closes is narrow and was invisible for exactly that reason.
``jinjax.Catalog`` builds ``Environment(undefined=StrictUndefined)`` and
autoescape defaults to ``False``; ``install_cf_ui`` never touched it. So on
FastAPI and Litestar every ``{{ … }}`` in a cf-ui template emitted raw output,
and a request-controlled value carrying a double quote could close the
attribute it landed in and open one of its own.

#35 stopped tab ids being *evaluated* as JavaScript by routing them through
``data-cf-tab``. That fix stands, but it moves the value from an expression
into an attribute value, and attribute-value safety is what this file is for.
Without it, #35 closed the execution path and left the injection path open on
one of the two supported engines.
"""

import pytest
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui

#: A double quote, a live event handler, and a dangling attribute to swallow
#: the closing quote the template supplies. Escaped correctly this is inert
#: text; unescaped it is a working ``onmouseover`` on the rendered element.
HOSTILE = '" onmouseover="window.cfPwned=true" x="'


@pytest.fixture
def catalog() -> Catalog:
    """A catalog built exactly as a consuming app builds one."""
    cat = Catalog()
    install_cf_ui(cat, theme="bulma")
    return cat


# --- The installed configuration -------------------------------------------


def test_install_cf_ui_leaves_the_catalog_autoescaping(catalog: Catalog) -> None:
    """The property every other assertion in this file rests on."""
    assert catalog.jinja_env.autoescape is True


def test_a_bare_catalog_is_not_autoescaping() -> None:
    """Pins *why* the installer has to act: JinjaX's own default is off.

    If a future JinjaX release flips this, the installer becomes a no-op and
    this test is the thing that says so, rather than the guarantee quietly
    coming from somewhere else.
    """
    assert not Catalog().jinja_env.autoescape


# --- The injection itself ---------------------------------------------------


def test_a_hostile_tab_id_cannot_open_a_new_attribute(catalog: Catalog) -> None:
    """The test that was missing. #35 moved this value; it did not escape it."""
    html = catalog.render(
        "Cf:Tabs",
        tabs=[{"id": HOSTILE, "url": "/x/"}],
        active="",
        hx_target="tc",
        extra_class="",
    )

    assert 'onmouseover="window.cfPwned=true"' not in html
    assert "&#34;" in html or "&quot;" in html


def test_a_hostile_url_cannot_open_a_new_attribute(catalog: Catalog) -> None:
    """Not specific to tab ids — every interpolated attribute was exposed."""
    html = catalog.render(
        "Cf:Tabs",
        tabs=[{"id": "one", "url": HOSTILE}],
        active="",
        hx_target="tc",
        extra_class="",
    )

    assert 'onmouseover="window.cfPwned=true"' not in html


def test_a_hostile_component_prop_cannot_open_a_new_attribute(catalog: Catalog) -> None:
    """A prop that is not a tab: the exposure was the engine, not the widget."""
    html = catalog.render("Cf:Modal", id=HOSTILE, extra_class="")

    assert 'onmouseover="window.cfPwned=true"' not in html


def test_text_nodes_are_escaped_too(catalog: Catalog) -> None:
    html = catalog.render(
        "Cf:Notification",
        message="<script>window.cfPwned=true</script>",
        type="info",
        dismissible=False,
        extra_class="",
    )

    assert "<script>window.cfPwned=true</script>" not in html
    assert "&lt;script&gt;" in html


# --- What must NOT change ---------------------------------------------------


def test_slot_content_still_renders_as_markup(catalog: Catalog) -> None:
    """The regression most likely to bite: JinjaX wraps slots in ``Markup``.

    A consumer passing real markup into a slot is passing markup deliberately;
    escaping it would turn every composed component into visible entities.
    """
    html = catalog.render(
        "Cf:Card",
        _content="<b>Bold body</b>",
        header="Title",
        footer="",
        extra_class="",
    )

    assert "<b>Bold body</b>" in html
    assert "&lt;b&gt;" not in html


def test_a_markup_prop_is_the_documented_way_to_pass_real_markup(catalog: Catalog) -> None:
    """The migration path, pinned — a prop is escaped unless it says otherwise.

    Not hypothetical: cf-ui's own E2E gallery passed a raw ``<button>`` string
    as ``footer=``, and turning autoescape on rendered it as text, taking the
    focus-trap and backdrop tests' control with it. Wrapping in ``Markup`` is
    the fix a consumer makes, so both halves are asserted here rather than left
    to the release note.
    """
    escaped = catalog.render(
        "Cf:Modal",
        id="m",
        header="H",
        footer='<button id="ok">OK</button>',
        extra_class="",
    )
    assert '<button id="ok">' not in escaped

    from markupsafe import Markup

    live = catalog.render(
        "Cf:Modal",
        id="m",
        header="H",
        footer=Markup('<button id="ok">OK</button>'),
        extra_class="",
    )
    assert '<button id="ok">' in live


def test_axis_globals_still_emit_live_attributes(catalog: Catalog) -> None:
    """``cf_ui_axis_attrs`` renders attributes, so it must survive autoescape.

    ``assets.jinja`` pipes it through ``|safe``, but a global that is only safe
    when every caller remembers a filter is not a guarantee. Asserted here
    without the filter.
    """
    out = catalog.jinja_env.from_string("<html {{ cf_ui_axis_attrs() }}>").render()

    assert 'data-accent="' in out
    assert "&#34;" not in out and "&quot;" not in out


def test_axis_style_global_still_emits_a_live_style_element(catalog: Catalog) -> None:
    cat = Catalog()
    install_cf_ui(
        cat,
        theme="bulma",
        value_sets={
            "accent": {
                "brand": {
                    "light": {
                        "--cf-accent": "#6d28d9",
                        "--cf-accent-content": "#ffffff",
                        "--cf-accent-strong": "#5b21b6",
                    },
                    "dark": {
                        "--cf-accent": "#a78bfa",
                        "--cf-accent-content": "#2e1065",
                        "--cf-accent-strong": "#c4b5fd",
                    },
                }
            }
        },
    )
    out = cat.jinja_env.from_string("{{ cf_ui_axis_style() }}").render()

    assert "<style>" in out
    assert "&lt;style&gt;" not in out


# --- The escape hatch -------------------------------------------------------


def test_cf_ui_autoescape_false_leaves_the_environment_alone() -> None:
    """The opt-out for anyone whose templates depend on the old behaviour.

    Deliberately not a no-op wrapper around the same result: this is the
    documented way to keep 0.1.x rendering after upgrading, so it is asserted
    to actually leave autoescape off rather than merely to be accepted.
    """
    cat = Catalog()
    install_cf_ui(cat, theme="bulma", cf_ui_autoescape=False)

    assert not cat.jinja_env.autoescape

    html = cat.render(
        "Cf:Tabs",
        tabs=[{"id": HOSTILE, "url": "/x/"}],
        active="",
        hx_target="tc",
        extra_class="",
    )
    assert 'onmouseover="window.cfPwned=true"' in html


def test_a_caller_supplied_autoescaping_env_is_not_disturbed() -> None:
    """Someone who already did the right thing keeps their configuration."""
    from jinja2 import Environment

    cat = Catalog(jinja_env=Environment(autoescape=True))
    install_cf_ui(cat, theme="bulma")

    assert cat.jinja_env.autoescape is True
