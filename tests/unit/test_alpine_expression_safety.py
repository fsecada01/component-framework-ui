"""Request-controlled values must never reach Alpine as expression text (#32).

Alpine evaluates the *value* of `:attr`, `@event` and `x-*` attributes as
JavaScript source. Interpolating a template variable into one of those is not
an escaping problem that a template engine can solve: the HTML parser decodes
`&#x27;` back to `'` while building the DOM, and Alpine reads the decoded
attribute. By the time the string reaches Alpine's evaluator the escaping is
gone, so a quote-bearing value breaks out of its string literal and runs.

`cf_ui_alpine.js` already states the rule in `initTabs()` and already follows
it for the seed value — `data-cf-active` crosses the boundary as data, and
`x-data="cfTabs('{{ active }}')"` is deliberately not used. This module is the
enforcement for the same rule one level down, plus a tree-wide guard so a
sixth theme cannot reintroduce the pattern by copying a fifth.

The proof that the fix works lives in `tests/e2e/test_alpine_injection.py` —
only a real browser can show the payload does not execute, because only a real
browser runs the HTML parser and Alpine's evaluator. What is asserted *here*
is the property that makes that possible: the rendered attribute holds no
splice point at all.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui" / "templates"
JINJA_DIR = TEMPLATES_DIR / "jinja"
COTTON_DIR = TEMPLATES_DIR / "cotton"

THEMES = ["bulma", "daisy"]

#: A tab id that closes the string literal it would be spliced into, runs, and
#: reopens it so the surrounding expression still parses. An expression that
#: merely *fails* to parse is not the interesting case — Alpine logs and moves
#: on. This one succeeds.
HOSTILE_ID = "');window.cfPwned=true;('"

TABS = [{"id": "one", "url": "/one/"}, {"id": "two", "url": "/two/"}]


# ── 1. Tree-wide guard ────────────────────────────────────────────────────
#
# Every template, every theme, every engine. This is the test that keeps the
# fix from being a one-time cleanup: it fails on the next template that gets
# the pattern wrong, wherever it lands.

#: Attributes Alpine evaluates. The lookbehind matters — without it, `x-`
#: matches inside `hx-get`, and HTMX attributes are values (a URL, a selector),
#: not source text, so interpolating into them is correct and expected.
ALPINE_ATTR = re.compile(
    r"""(?<![\w-])            # not the tail of hx-get / data-x-thing
        (?: : [a-zA-Z][\w:-]*  # :class, :aria-selected, :tabindex
          | @ [a-zA-Z][\w.:-]* # @click.prevent, @keydown
          | x- [a-zA-Z][\w.:-]*# x-data, x-init, x-show, x-on:click
        )
        \s*=\s*"([^"]*)"      # its value
    """,
    re.VERBOSE,
)

#: What a template engine's output looks like, in either engine.
INTERPOLATION = re.compile(r"\{\{|\{%")


def _all_templates() -> list[Path]:
    return sorted([p for p in JINJA_DIR.rglob("*.jinja")] + [p for p in COTTON_DIR.rglob("*.html")])


def _rel(path: Path) -> str:
    return str(path.relative_to(TEMPLATES_DIR)).replace("\\", "/")


@pytest.mark.parametrize("template", _all_templates(), ids=_rel)
def test_no_alpine_expression_attribute_interpolates_template_output(template: Path):
    source = template.read_text(encoding="utf-8")
    offenders = [
        match.group(0)
        for match in ALPINE_ATTR.finditer(source)
        if INTERPOLATION.search(match.group(1))
    ]
    assert not offenders, (
        f"{_rel(template)} splices template output into an Alpine expression:\n"
        + "\n".join(f"  {o}" for o in offenders)
        + "\n\nAlpine evaluates these values as JavaScript. Pass the value through a "
        "`data-` attribute and read it back with `$el.dataset.*` instead — see "
        "docs/accessibility.md."
    )


# ── 2. The tab bindings specifically ──────────────────────────────────────


@pytest.fixture(params=THEMES)
def theme(request) -> str:
    return request.param


@pytest.fixture
def jinja_render(theme: str) -> Callable[..., str]:
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
    from django.template.loader import render_to_string

    settings.CF_UI_THEME = theme

    def _render(stem: str, **props: object) -> str:
        return render_to_string(f"cotton/cf/{stem}.html", props)

    return _render


def _alpine_values(html: str) -> list[str]:
    return [match.group(1) for match in ALPINE_ATTR.finditer(html)]


def test_jinja_tab_bindings_read_the_tab_id_from_a_data_attribute(jinja_render):
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    assert "$el.dataset.cfTab" in html
    assert "tabIndexFor('" not in html
    assert "setActive('" not in html


def test_cotton_tab_bindings_read_the_tab_id_from_a_data_attribute(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    assert "$el.dataset.cfTab" in html
    assert "tabIndexFor('" not in html
    assert "setActive('" not in html


def test_jinja_every_element_bound_to_the_tab_id_carries_it_as_data(jinja_render):
    """`$el.dataset.cfTab` only resolves on an element that has the attribute.

    The active-class binding sits on the row wrapper in some themes and on the
    anchor in others, so both have to carry `data-cf-tab` — reaching across
    the DOM from one to the other would put theme structure back into
    `cf_ui_alpine.js`.
    """
    html = jinja_render(
        "Tabs.jinja", tabs=TABS, hx_target="tc", active="two", content="", extra_class=""
    )
    for tag in re.findall(r"<[a-zA-Z][^>]*>", html, re.DOTALL):
        if "$el.dataset.cfTab" in tag:
            assert "data-cf-tab=" in tag, (
                f"reads $el.dataset.cfTab but carries no data-cf-tab:\n  {tag}"
            )


def test_cotton_every_element_bound_to_the_tab_id_carries_it_as_data(cotton_render):
    html = cotton_render("tabs", tabs=TABS, hx_target="tc", active="two", **{"class": ""})
    for tag in re.findall(r"<[a-zA-Z][^>]*>", html, re.DOTALL):
        if "$el.dataset.cfTab" in tag:
            assert "data-cf-tab=" in tag, (
                f"reads $el.dataset.cfTab but carries no data-cf-tab:\n  {tag}"
            )


# ── 3. A hostile id, rendered ─────────────────────────────────────────────


def test_jinja_tabs_leave_a_hostile_tab_id_out_of_every_expression(jinja_render):
    html = jinja_render(
        "Tabs.jinja",
        tabs=[{"id": HOSTILE_ID, "url": "/x/"}],
        hx_target="tc",
        active=HOSTILE_ID,
        content="",
        extra_class="",
    )
    assert "cfPwned" not in "".join(_alpine_values(html)), (
        "the payload reached an attribute Alpine evaluates as JavaScript"
    )
    assert "cfPwned" in html, "the hostile id never rendered at all — this test proved nothing"


def test_cotton_tabs_leave_a_hostile_tab_id_out_of_every_expression(cotton_render):
    html = cotton_render(
        "tabs",
        tabs=[{"id": HOSTILE_ID, "url": "/x/"}],
        hx_target="tc",
        active=HOSTILE_ID,
        **{"class": ""},
    )
    assert "cfPwned" not in "".join(_alpine_values(html))
    assert "cfPwned" in html, "the hostile id never rendered at all"
