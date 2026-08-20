"""``CheckboxGroup`` attrs passthrough — rollout of #73's ``Button``
precedent, scoped by #70.

Same shape/escaping decisions as ``Button`` (see ``test_attrs_passthrough.py``
for the full writeup) — routed through the one
:func:`cf_ui.primitives.render_attrs` implementation, so no new validation or
escaping logic exists here.

``CheckboxGroup`` is the one primitive that departs from the
``Select``/``Textarea``/``FormField`` precedent (#76): those three route
``attrs`` onto the single control they render. ``CheckboxGroup`` renders N
``<input type="checkbox">`` elements from ``choices`` — there is no single
control to target — so ``attrs`` lands on the outer wrapper element instead
(the ``field``/``mb-3``/``form-control``/``ui form``/``fieldset`` container).
Every assertion below checks the inverse of #76's: the passthrough attribute
belongs on the wrapper, and must never leak onto a per-choice checkbox.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment

from cf_ui.primitives import PrimitiveConfigError, build_primitive_globals
from cf_ui.themes import THEMES
from tests.jinja_env import make_env

JINJA_DIR = Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "jinja"

BASE_PROPS = {
    "name": "interests",
    "label": "Interests",
    "choices": [{"value": "a", "label": "Alpha"}, {"value": "b", "label": "Beta"}],
    "selected": [],
    "error": "",
    "extra_class": "",
    "control_class": "",
}


@pytest.fixture(params=THEMES)
def theme(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def env(theme: str) -> Environment:
    e = make_env(JINJA_DIR / theme)
    e.globals.update(build_primitive_globals())
    return e


@pytest.fixture
def render(env: Environment) -> Callable[..., str]:
    def _render(**ctx: object) -> str:
        return env.get_template("CheckboxGroup.jinja").render(**{**BASE_PROPS, **ctx})

    return _render


def test_renders_with_no_attrs_prop_at_all(render: Callable[..., str]) -> None:
    """Omitting ``attrs`` entirely must not break rendering (StrictUndefined)."""
    html = render()
    assert html.strip()


def test_renders_passthrough_attrs_on_the_wrapper(render: Callable[..., str]) -> None:
    html = render(attrs={"data-marker": "wrapper-only", "x-data": "{}"})
    wrapper_open, _, _rest = html.partition(">")
    assert 'data-marker="wrapper-only"' in wrapper_open
    assert 'x-data="{}"' in wrapper_open


def test_passthrough_attrs_do_not_land_on_a_checkbox_input(render: Callable[..., str]) -> None:
    """The inverse of #76's field-wrapper assertion: here the wrapper is the
    intended target, and a per-choice ``<input>`` must never see it."""
    html = render(attrs={"data-marker": "wrapper-only"})
    for input_tag in re.findall(r"<input\b[^>]*>", html):
        assert "data-marker" not in input_tag


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
    """``class`` is RESERVED_ATTRS-listed but never a declared prop
    (``extra_class`` is), so the guard fires reliably."""
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"class": "override"})
