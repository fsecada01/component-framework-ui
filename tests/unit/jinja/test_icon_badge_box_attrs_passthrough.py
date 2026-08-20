"""``Icon``/``Badge``/``Box`` attrs passthrough — rollout of #73's ``Button``
precedent, scoped by #70.

Same shape/escaping decisions as ``Button`` (see ``test_attrs_passthrough.py``
for the full writeup) — routed through the one
:func:`cf_ui.primitives.render_attrs` implementation, so no new validation or
escaping logic exists here.

Unlike ``Select``/``Textarea``/``FormField`` (#76), each of these three
renders exactly one element — there is no wrapper to get it wrong. ``attrs``
lands directly on that element.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment

from cf_ui.primitives import PrimitiveConfigError, build_primitive_globals
from cf_ui.themes import THEMES
from tests.jinja_env import make_env

JINJA_DIR = Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "jinja"

# component key (matches RESERVED_ATTRS), template file, base props every
# theme needs (bulma's templates carry no `is defined` guards for its other
# props, unlike the other four themes, so the full set must always be passed
# explicitly regardless of theme).
CASES = [
    (
        "icon",
        "Icon.jinja",
        {"content": "*", "size": "normal", "label": "", "extra_class": ""},
    ),
    (
        "badge",
        "Badge.jinja",
        {"content": "New", "variant": "neutral", "size": "normal", "extra_class": ""},
    ),
    (
        "box",
        "Box.jinja",
        {"content": "Hello", "variant": "neutral", "extra_class": ""},
    ),
]


@pytest.fixture(params=THEMES)
def theme(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=CASES, ids=[c[0] for c in CASES])
def case(request: pytest.FixtureRequest) -> tuple[str, str, dict[str, object]]:
    return request.param


@pytest.fixture
def env(theme: str) -> Environment:
    e = make_env(JINJA_DIR / theme)
    e.globals.update(build_primitive_globals())
    return e


@pytest.fixture
def render(env: Environment, case: tuple[str, str, dict[str, object]]) -> Callable[..., str]:
    _component, template_name, base_props = case

    def _render(**ctx: object) -> str:
        return env.get_template(template_name).render(**{**base_props, **ctx})

    return _render


@pytest.fixture
def component(case: tuple[str, str, dict[str, object]]) -> str:
    return case[0]


def test_renders_with_no_attrs_prop_at_all(render: Callable[..., str]) -> None:
    """Omitting ``attrs`` entirely must not break rendering (StrictUndefined)."""
    html = render()
    assert html.strip()


def test_renders_passthrough_attrs(render: Callable[..., str]) -> None:
    html = render(attrs={"data-event": "submit", "hx-get": "/things"})
    assert 'data-event="submit"' in html
    assert 'hx-get="/things"' in html


def test_passthrough_attrs_coexist_with_named_props(render: Callable[..., str]) -> None:
    html = render(extra_class="js-field", attrs={"x-on:change": "go()"})
    assert 'x-on:change="go()"' in html
    assert "js-field" in html


def test_renders_with_attrs_explicitly_none(render: Callable[..., str]) -> None:
    html = render(attrs=None)
    assert html.strip()


def test_escapes_a_hostile_attr_value(render: Callable[..., str]) -> None:
    html = render(attrs={"data-x": '" onmouseover="alert(1)" x="'})
    assert 'onmouseover="alert(1)"' not in html


def test_rejects_a_quote_based_hostile_attr_name(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={'x" onmouseover="alert(1)': "y"})


def test_rejects_a_whitespace_and_equals_hostile_attr_name(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"x onmouseover=alert(1)//": "y"})


def test_rejects_attrs_colliding_with_class(render: Callable[..., str]) -> None:
    """``class`` is RESERVED_ATTRS-listed but never a declared prop on any of
    these three (``extra_class`` is), so the guard fires reliably — no
    declared-prop-name bypass like Button's ``type``/``href`` (#78)."""
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"class": "override"})


def test_rejects_attrs_colliding_with_icon_role(render: Callable[..., str], component: str) -> None:
    if component != "icon":
        pytest.skip("role is only reserved for icon")
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"role": "override"})


def test_rejects_attrs_colliding_with_icon_aria_label(
    render: Callable[..., str], component: str
) -> None:
    if component != "icon":
        pytest.skip("aria-label is only reserved for icon")
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"aria-label": "override"})


def test_rejects_attrs_colliding_with_icon_aria_hidden(
    render: Callable[..., str], component: str
) -> None:
    """The reservation is static, not conditioned on ``label`` — only the
    no-label branch renders ``aria-hidden`` itself, but the guard must reject
    the collision regardless, since it fires before the template runs."""
    if component != "icon":
        pytest.skip("aria-hidden is only reserved for icon")
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"aria-hidden": "false"})
