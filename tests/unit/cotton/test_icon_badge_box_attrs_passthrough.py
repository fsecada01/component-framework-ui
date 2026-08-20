"""``<c-cf.icon>``/``<c-cf.badge>``/``<c-cf.box>`` attrs passthrough —
rollout of #73's ``Button`` precedent, scoped by #70.

See ``tests/unit/jinja/test_icon_badge_box_attrs_passthrough.py`` for the
full design writeup (shape/escaping/single-element target). These go through
``cotton_render`` (``render_to_string``), which bypasses the django-cotton
compiler per this repo's CLAUDE.md — every prop, including ``attrs``, must
be passed explicitly here; the ``<c-vars attrs="{}" />`` default is only
exercised by the E2E tier.
"""

from collections.abc import Callable

import pytest

from cf_ui.primitives import PrimitiveConfigError
from cf_ui.themes import THEMES

CASES = [
    (
        "icon",
        "cf/icon.html",
        {"size": "normal", "label": "", "class": "", "slot": "*"},
    ),
    (
        "badge",
        "cf/badge.html",
        {"variant": "neutral", "size": "normal", "class": "", "slot": "New"},
    ),
    (
        "box",
        "cf/box.html",
        {"variant": "neutral", "class": "", "slot": "Hello"},
    ),
]


@pytest.fixture(params=CASES, ids=[c[0] for c in CASES])
def case(request: pytest.FixtureRequest) -> tuple[str, str, dict[str, object]]:
    return request.param


@pytest.fixture(params=THEMES)
def render(
    request: pytest.FixtureRequest,
    settings: object,
    cotton_render: Callable[..., str],
    case: tuple[str, str, dict[str, object]],
) -> Callable[..., str]:
    settings.CF_UI_THEME = request.param
    _component, template_name, base_props = case

    def _render(**ctx: object) -> str:
        return cotton_render(template_name, **{**base_props, "attrs": {}, **ctx})

    return _render


def test_cotton_renders_with_empty_attrs(render: Callable[..., str]) -> None:
    assert render().strip()


def test_cotton_renders_passthrough_attrs(render: Callable[..., str]) -> None:
    html = render(attrs={"data-event": "submit", "hx-get": "/things"})
    assert 'data-event="submit"' in html
    assert 'hx-get="/things"' in html


def test_cotton_passthrough_attrs_coexist_with_named_props(render: Callable[..., str]) -> None:
    html = render(**{"class": "js-field", "attrs": {"x-on:change": "go()"}})
    assert 'x-on:change="go()"' in html
    assert "js-field" in html


def test_cotton_renders_with_attrs_explicitly_none(render: Callable[..., str]) -> None:
    assert render(attrs=None).strip()


def test_cotton_escapes_a_hostile_attr_value(render: Callable[..., str]) -> None:
    html = render(attrs={"data-x": '" onmouseover="alert(1)" x="'})
    assert 'onmouseover="alert(1)"' not in html


def test_cotton_rejects_a_quote_based_hostile_attr_name(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={'x" onmouseover="alert(1)': "y"})


def test_cotton_rejects_a_whitespace_and_equals_hostile_attr_name(
    render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"x onmouseover=alert(1)//": "y"})


def test_cotton_rejects_attrs_colliding_with_class(render: Callable[..., str]) -> None:
    """``class`` is RESERVED_ATTRS-listed but is its own dedicated ``<c-vars>``
    prop for these three, not routed through ``attrs`` — the guard fires
    reliably, no declared-prop-name bypass like Button's ``type``/``href``
    (#78)."""
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"class": "override"})


ICON_CASE = CASES[0]


@pytest.fixture(params=THEMES)
def icon_render(
    request: pytest.FixtureRequest, settings: object, cotton_render: Callable[..., str]
) -> Callable[..., str]:
    """Icon-only render, independent of the ``case`` fixture — the
    icon-reserved-name collision tests below have nothing to assert for
    badge/box, so they must not be parametrized over ``CASES`` at all rather
    than parametrized and then skipped 2/3 of the time."""
    settings.CF_UI_THEME = request.param
    _component, template_name, base_props = ICON_CASE

    def _render(**ctx: object) -> str:
        return cotton_render(template_name, **{**base_props, "attrs": {}, **ctx})

    return _render


def test_cotton_rejects_attrs_colliding_with_icon_role(icon_render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        icon_render(attrs={"role": "override"})


def test_cotton_rejects_attrs_colliding_with_icon_aria_label(
    icon_render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        icon_render(attrs={"aria-label": "override"})


def test_cotton_rejects_attrs_colliding_with_icon_aria_hidden(
    icon_render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        icon_render(attrs={"aria-hidden": "false"})
