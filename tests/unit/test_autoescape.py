"""Escaping is a property of cf-ui's template files, not of any environment (#36).

Every cf-ui Jinja template wraps its body in ``{% autoescape true %}``, so a
hostile prop is escaped on a bare ``Catalog()``, on Litestar's plain-Jinja
path, and for a consumer who never calls ``install_cf_ui`` at all. The
installers, in turn, must never touch the caller's ``autoescape`` — an earlier
cut of #36 set it on the shared environment, and every defect that followed
(a trampled ``select_autoescape`` callable, compile-cache ordering, an escape
hatch) came from that one choice.

Three groups here:

1. A drift guard over the whole template tree, so theme #6 cannot ship without
   the block — modelled on ``test_alpine_expression_safety.py``, and like it,
   the guard's own behaviour is pinned so it cannot rot into reporting clean.
2. A behavioural check per theme: hostile input, environment escaping off,
   output escaped anyway. The guard reads source; this renders it.
3. The installers leave the environment exactly as they found it.
"""

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from jinja2 import Environment, select_autoescape
from jinjax import Catalog

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.themes import THEMES

HOSTILE = '" onmouseover="window.cfPwned=true" x="'

#: The `{#def ...#}` header JinjaX locates by position — it must stay the very
#: first thing in the file, so the autoescape block has to open *after* it.
DEF_HEADER = re.compile(r"\A\{#def\b.*?#\}", re.S)


# ── 1. Drift guard ────────────────────────────────────────────────────────


def _all_component_templates() -> list[Path]:
    return sorted(JINJA_TEMPLATES_DIR.glob("*/*.jinja"))


def _rel(path: Path) -> str:
    return str(path.relative_to(JINJA_TEMPLATES_DIR)).replace("\\", "/")


def _placement_error(source: str) -> str | None:
    """Why this template's autoescape block is wrong, or None if it is right.

    Three rules, each one a failure actually hit while building this:

    * The block must exist at all, once — nested or repeated blocks are a sign
      of a bad merge.
    * It must open **after** the ``{#def}`` header with nothing but whitespace
      between: wrapping the header makes JinjaX stop seeing the props
      (``UndefinedError`` on every prop), and any output before the block is
      unescaped output.
    * It must close at end of file, so no output trails outside it.
    """
    opens = source.count("{% autoescape true %}")
    closes = source.count("{% endautoescape %}")
    if opens != 1 or closes != 1:
        return f"expected exactly one autoescape block, found {opens} open/{closes} close"

    header = DEF_HEADER.match(source)
    if not header:
        return "no {#def} header at the start of the file"

    between = source[header.end() : source.index("{% autoescape true %}")]
    if between.strip():
        return f"output before the block is unescaped output: {between.strip()[:60]!r}"

    tail = source[source.index("{% endautoescape %}") + len("{% endautoescape %}") :]
    if tail.strip():
        return f"output after the block is unescaped output: {tail.strip()[:60]!r}"
    return None


@pytest.mark.parametrize("template", _all_component_templates(), ids=_rel)
def test_every_component_template_carries_its_own_autoescape_block(template: Path):
    error = _placement_error(template.read_text(encoding="utf-8"))
    assert error is None, (
        f"{_rel(template)}: {error}\n\n"
        "Every cf-ui Jinja template escapes its own output — the block opens "
        "right after the {#def} header and closes at end of file. See "
        "CLAUDE.md, 'Adding a New Theme'."
    )


def test_the_template_count_is_what_the_guard_thinks_it_is():
    """Every registered component × every registered theme.

    Derived from ``themes.COMPONENTS`` rather than a literal, so adding a
    primitive does not mean editing a number in four files (#52) — but a
    guard over an empty glob passes, so the registry is asserted non-empty
    first. ``test_theme_dispatch`` pins ``COMPONENTS`` itself against an
    independent literal list, which is what keeps this from circling.
    """
    from cf_ui.themes import COMPONENTS

    assert COMPONENTS, "the component registry is empty — this guard would pass over nothing"
    assert len(_all_component_templates()) == len(COMPONENTS) * len(THEMES)


# The guard's own behaviour, pinned — a lint that stops matching reports clean
# forever, which is worse than no lint.
GUARD_CASES = [
    (None, "{#def a #}\n{% autoescape true %}\n<p>{{ a }}</p>\n{% endautoescape %}\n"),
    ("no {#def}", "{% autoescape true %}\n<p>hi</p>\n{% endautoescape %}\n"),
    ("expected exactly one", "{#def a #}\n<p>{{ a }}</p>\n"),
    (
        "expected exactly one",
        "{#def a #}\n" + "{% autoescape true %}\n" * 2 + "{% endautoescape %}\n" * 2,
    ),
    ("output before", "{#def a #}\n<p>leak</p>\n{% autoescape true %}\n{% endautoescape %}\n"),
    ("output after", "{#def a #}\n{% autoescape true %}\n{% endautoescape %}\n<p>leak</p>\n"),
]


@pytest.mark.parametrize(("expected", "source"), GUARD_CASES, ids=lambda v: str(v)[:32])
def test_the_guard_flags_what_it_claims_to(expected: str | None, source: str):
    error = _placement_error(source)
    if expected is None:
        assert error is None, f"false positive: {error}"
    else:
        assert error is not None and expected in error


# ── 2. The behaviour the guard's subject exists for ───────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_a_hostile_prop_is_escaped_with_environment_escaping_off(theme: str):
    """Bare catalog, autoescape off — the template is the only escaper left.

    This is the configuration a consumer gets by calling ``add_folder``
    directly and never touching ``install_cf_ui``, which the environment-level
    fix could not cover at all.
    """
    catalog = Catalog()
    catalog.add_folder(JINJA_TEMPLATES_DIR / theme, prefix="Cf")
    assert not catalog.jinja_env.autoescape

    html = catalog.render(
        "Cf:Tabs", tabs=[{"id": HOSTILE, "url": "/x/"}], active="", hx_target="tc", extra_class=""
    )
    assert 'onmouseover="window.cfPwned=true"' not in html
    assert "&#34;" in html or "&quot;" in html


def test_the_assets_macros_escape_their_arguments_with_escaping_off():
    """``assets.jinja``'s blocks live *inside* each macro body — a file-scope
    block would stop the macros being exported and break every
    ``{% from ... import %}`` downstream. This is the behavioural pin for
    those blocks: a hostile URL argument is escaped even when the consuming
    environment does not escape, while the ``Markup``-wrapped axis globals
    stay live through ``|safe``.
    """
    from cf_ui.axes import root_attrs
    from tests.jinja_env import make_env

    env = make_env(JINJA_TEMPLATES_DIR.parent)
    assert not env.autoescape
    env.globals["cf_ui_axis_attrs"] = lambda: root_attrs(None)

    hostile_url = '/a.css" onload="window.cfPwned=true'
    out = env.from_string(
        '{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_root_attrs, cf_ui_body %}'
        '{{ cf_ui_head(theme="bulma", cf_axes_url=u) }}|<html {{ cf_ui_root_attrs() }}>|'
        "{{ cf_ui_body(theme='bulma', cf_alpine_url=u) }}"
    ).render(u=hostile_url)
    head, attrs, body = out.split("|")

    assert 'onload="window.cfPwned=true' not in head
    assert 'onload="window.cfPwned=true' not in body
    assert 'data-accent="' in attrs and "&#34;" not in attrs


# ── 3. The installers leave the environment alone ─────────────────────────


def test_fastapi_installer_does_not_touch_autoescape():
    """Both starting values, so this cannot become the test that could not fail.

    A previous version of this property asserted ``True`` stayed ``True``
    against an installer that only ever set ``True`` — it passed with the
    install call deleted. ``False`` staying ``False`` is the direction that
    can actually break, and a caller's ``select_autoescape`` callable is the
    identity that must survive.
    """
    from cf_ui.fastapi import install_cf_ui

    cat = Catalog()
    install_cf_ui(cat, theme="bulma")
    assert cat.jinja_env.autoescape is False

    selector = select_autoescape(["html"])
    cat = Catalog(jinja_env=Environment(autoescape=selector))
    install_cf_ui(cat, theme="bulma")
    assert cat.jinja_env.autoescape is selector


def _fresh_config() -> MagicMock:
    """A TemplateConfig double with no callback of its own.

    ``engine_callback`` is set to ``None`` explicitly: a bare ``MagicMock``
    attribute is callable, so the installer would treat it as a previous
    callback and invoke it, which is not the case under test here.
    """
    config = MagicMock()
    config.directory = []
    config.engine_callback = None
    return config


def test_litestar_installer_does_not_touch_autoescape():
    from cf_ui.litestar import install_cf_ui

    selector = select_autoescape(["html"])
    for supplied in (False, selector):
        config = _fresh_config()
        install_cf_ui(config, theme="bulma")

        env = Environment(autoescape=supplied)
        config.engine_callback(SimpleNamespace(engine=env))
        assert env.autoescape is supplied


def test_litestar_installer_still_chains_a_previous_callback():
    """The callback chaining predates #36 and must survive its removal."""
    from cf_ui.litestar import install_cf_ui

    seen: list[object] = []
    config = MagicMock()
    config.directory = []
    config.engine_callback = seen.append

    install_cf_ui(config, theme="bulma")
    engine = SimpleNamespace(engine=Environment())
    config.engine_callback(engine)

    assert seen == [engine]
    assert "cf_ui_axis_attrs" in engine.engine.globals


def test_litestar_installer_handles_an_engine_without_a_nested_environment():
    """``getattr(engine, "engine", engine)`` — the existing fallback path."""
    from cf_ui.litestar import install_cf_ui

    config = _fresh_config()
    install_cf_ui(config, theme="bulma")

    env = Environment()
    config.engine_callback(env)

    assert "cf_ui_axis_attrs" in env.globals


# ── History, kept executable ──────────────────────────────────────────────


@pytest.mark.parametrize("extension_list", [["html"], ["html", "htm", "xml"]])
def test_select_autoescape_would_not_have_covered_dot_jinja(extension_list: list[str]):
    """Why environment-level escaping kept going wrong, in one line.

    ``select_autoescape`` keys off the file extension and cf-ui's templates
    are ``.jinja`` — so the idiomatic selector answers ``False`` for them.
    Two test fixtures fell into this, and the interim installer guard
    ("respect any truthy autoescape") reopened #36 for every consumer using
    it. In-template blocks are the mechanism this trap cannot reach.
    """
    assert select_autoescape(extension_list)("Tabs.jinja") is False


def test_litestar_args_prefix_matches_jinjax():
    """``cf_ui.litestar`` depends on a jinjax internal; pin it (#42).

    JinjaX rewrites ``<Cf:Card>`` into ``catalog.irender("Cf:Card",
    __prefix=__prefix, ...)``. cf-ui binds that name as a global so a page
    template rendered by Litestar — which has no enclosing component to supply
    it — does not raise ``'__prefix' is undefined``. If jinjax ever renames
    the constant, the fallback literal in ``cf_ui/litestar.py`` would silently
    bind the wrong name and component rendering would break on that path.
    """
    import jinjax.utils

    from cf_ui.litestar import ARGS_PREFIX

    assert ARGS_PREFIX == jinjax.utils.ARGS_PREFIX == "__prefix"


def test_litestar_catalog_install_does_not_touch_autoescape():
    """The catalog install is new (#42); #36's promise has to survive it."""
    from cf_ui.litestar import _install_catalog

    selector = select_autoescape(["html"])
    for supplied in (False, selector):
        env = Environment(autoescape=supplied)
        _install_catalog(env, JINJA_TEMPLATES_DIR / "bulma")
        assert env.autoescape is supplied
