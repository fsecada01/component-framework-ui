"""Attribute escaping on the JinjaX path, against a real catalog (#36).

The escaping under test lives in the templates themselves — every cf-ui
component wraps its body in ``{% autoescape true %}`` — so the main fixture
here is deliberately a **bare** ``Catalog()``: environment escaping off,
``install_cf_ui`` never called. Anything these tests observe escaped can only
have come from the template files, which is the shipped guarantee. Two earlier
mechanisms failed the harder cases: leaving it to the consumer's environment
missed both installers' defaults, and having the installer set the flag was
order-dependent (the flag is read at compile time, and JinjaX caches), trampled
``select_autoescape`` policies, and covered only consumers who called the
installer.

The gap all of this closes is #35's other half: that ticket stopped tab ids
being *evaluated* as JavaScript by routing them through ``data-cf-tab``. That
fix stands, but it moves the value from an expression into an attribute value,
and attribute-value safety is what this file is for.
"""

import pytest
from jinjax import Catalog

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.fastapi import install_cf_ui

#: A double quote, a live event handler, and a dangling attribute to swallow
#: the closing quote the template supplies. Escaped correctly this is inert
#: text; unescaped it is a working ``onmouseover`` on the rendered element.
HOSTILE = '" onmouseover="window.cfPwned=true" x="'


@pytest.fixture
def catalog() -> Catalog:
    """A bare catalog: autoescape off, installer never called.

    The unfriendliest configuration a consumer can hand cf-ui's templates —
    and a supported one: ``add_folder`` directly is how ``install_cf_ui``
    itself registers the templates.
    """
    cat = Catalog()
    cat.add_folder(JINJA_TEMPLATES_DIR / "bulma", prefix="Cf")
    return cat


# --- The premise -------------------------------------------------------------


def test_a_bare_catalog_is_not_autoescaping(catalog: Catalog) -> None:
    """Pins that the escaping asserted below cannot be the environment's.

    ``jinjax.Catalog`` builds ``Environment(undefined=StrictUndefined)`` and
    autoescape defaults to ``False``. If a future JinjaX release flips this,
    the templates' own blocks become redundant rather than wrong — but this
    file would start proving the wrong thing, and this test is what says so.
    """
    assert not catalog.jinja_env.autoescape


# --- The injection itself ----------------------------------------------------


def test_a_hostile_tab_id_cannot_open_a_new_attribute(catalog: Catalog) -> None:
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


def test_escaping_holds_before_and_after_the_installer_runs(catalog: Catalog) -> None:
    """The ordering hazard that killed the environment-level mechanism.

    ``autoescape`` is read at *compile* time and JinjaX caches compiled
    components, so under the installer-sets-a-flag design a component rendered
    before ``install_cf_ui`` stayed compiled unescaped for the process
    lifetime — silently, with the flag reading ``True``. With the block in the
    template there is no ordering to get wrong; both renders here compile from
    the same source and the second exercises the cached component.
    """
    tabs = {"tabs": [{"id": HOSTILE, "url": "/x/"}], "active": "", "hx_target": "tc"}

    before = catalog.render("Cf:Tabs", extra_class="", **tabs)
    assert 'onmouseover="window.cfPwned=true"' not in before

    install_cf_ui(catalog, theme="bulma")

    after = catalog.render("Cf:Tabs", extra_class="", **tabs)
    assert 'onmouseover="window.cfPwned=true"' not in after


# --- What must NOT change ----------------------------------------------------


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


def test_a_nested_component_is_not_double_escaped(catalog: Catalog) -> None:
    """Each component autoescapes its own body; composition must not compound.

    ``Catalog.render`` returns ``Markup``, so a component passed into another
    component's slot arrives already marked safe — the inner block escaped its
    interpolations once, and the outer block must not escape the result again.
    """
    inner = catalog.render(
        "Cf:Tabs",
        tabs=[{"id": "one", "url": "/one/"}],
        active="one",
        hx_target="tc",
        extra_class="",
    )
    outer = catalog.render("Cf:Card", _content=inner, header="H", footer="", extra_class="")

    assert 'role="tablist"' in outer
    assert "&lt;" not in outer.split('role="tablist"')[0]


def test_a_markup_prop_is_the_documented_way_to_pass_real_markup(catalog: Catalog) -> None:
    """The migration path, pinned — a prop is escaped unless it says otherwise.

    Not hypothetical: cf-ui's own E2E gallery passed a raw ``<button>`` string
    as ``footer=``, and escaping rendered it as text, taking the focus-trap
    and backdrop tests' control with it. Wrapping in ``Markup`` is the fix a
    consumer makes, so both halves are asserted here rather than left to the
    release note.
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


def test_axis_globals_still_emit_live_attributes() -> None:
    """``cf_ui_axis_attrs`` renders attributes, so it must survive escaping.

    ``build_axis_globals`` wraps both globals in ``Markup``; ``assets.jinja``
    additionally pipes them through ``|safe``. Asserted through the macro that
    consumers actually call, on an installed catalog, since the globals only
    exist after install.
    """
    cat = Catalog()
    install_cf_ui(cat, theme="bulma")
    out = cat.jinja_env.from_string(
        "{% autoescape true %}<html {{ cf_ui_axis_attrs() }}>{% endautoescape %}"
    ).render()

    assert 'data-accent="' in out
    assert "&#34;" not in out and "&quot;" not in out


def test_axis_style_global_still_emits_a_live_style_element() -> None:
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
    out = cat.jinja_env.from_string(
        "{% autoescape true %}{{ cf_ui_axis_style() }}{% endautoescape %}"
    ).render()

    assert "<style>" in out
    assert "&lt;style&gt;" not in out
