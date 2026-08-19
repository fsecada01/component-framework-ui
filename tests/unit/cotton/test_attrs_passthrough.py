"""``<c-cf.button>`` attribute passthrough — spike from #72, resolved for #71.

See ``tests/unit/jinja/test_attrs_passthrough.py`` for the full design
writeup (shape/escaping/scope) — the decision is engine-agnostic and applies
identically here. ``attrs`` is forwarded through the public wrapper's
``{% include %}`` the same untouched way ``variant``/``size``/``extra_class``
already are, and it is rendered with plain ``{{ }}`` interpolation, so
Django's own default auto-escaping is what neutralizes a hostile value —
consistent with docs/escaping.md's "same rule applies through the template
layer" note for cotton.

These go through ``cotton_render`` (``render_to_string``), which bypasses the
django-cotton compiler per this repo's CLAUDE.md — props arrive as plain
context, not via ``<c-vars>`` defaulting. That means ``attrs`` must be passed
explicitly as a real ``dict`` here; the ``<c-vars attrs="{}" />`` default is
only exercised by the E2E tier.

Post-review addendum (PR #73 review): validation and escaping now live once,
in :func:`cf_ui.primitives.render_attrs`, called through the
``{% cf_ui_render_attrs %}`` tag — not inline per theme partial. See
``tests/unit/jinja/test_attrs_passthrough.py`` for the full addendum
rationale; the cases below mirror it for the cotton side.
"""

from collections.abc import Callable

import pytest

from cf_ui.primitives import PrimitiveConfigError
from cf_ui.themes import THEMES


@pytest.fixture(params=THEMES)
def render(
    request: pytest.FixtureRequest, settings: object, cotton_render: Callable[..., str]
) -> Callable[..., str]:
    settings.CF_UI_THEME = request.param

    def _render(**ctx: object) -> str:
        # render_to_string bypasses the cotton compiler, so <c-vars> defaults
        # (including `type="button"`) never apply — supply them explicitly.
        return cotton_render(
            "cf/button.html", **{"class": "", "type": "button", "attrs": {}, **ctx}
        )

    return _render


def test_button_cotton_renders_with_empty_attrs(render: Callable[..., str]) -> None:
    html = render()
    assert "<button" in html or "<a" in html


def test_button_cotton_renders_passthrough_attrs(render: Callable[..., str]) -> None:
    html = render(attrs={"data-event": "submit", "hx-get": "/things"})
    assert 'data-event="submit"' in html
    assert 'hx-get="/things"' in html


def test_button_cotton_passthrough_attrs_coexist_with_named_props(
    render: Callable[..., str],
) -> None:
    html = render(**{"variant": "primary", "class": "js-cta", "attrs": {"x-on:click": "go()"}})
    assert 'x-on:click="go()"' in html
    assert "js-cta" in html


def test_button_cotton_renders_with_attrs_explicitly_none(
    render: Callable[..., str],
) -> None:
    html = render(attrs=None)
    assert "<button" in html or "<a" in html


def test_button_cotton_escapes_a_hostile_attr_value(render: Callable[..., str]) -> None:
    html = render(attrs={"data-x": '" onmouseover="alert(1)" x="'})
    assert 'onmouseover="alert(1)"' not in html


def test_button_cotton_rejects_a_quote_based_hostile_attr_name(
    render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={'x" onmouseover="alert(1)': "y"})


def test_button_cotton_rejects_a_whitespace_and_equals_hostile_attr_name(
    render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"x onmouseover=alert(1)//": "y"})


def test_button_cotton_rejects_attrs_colliding_with_a_reserved_prop(
    render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"type": "submit"})
