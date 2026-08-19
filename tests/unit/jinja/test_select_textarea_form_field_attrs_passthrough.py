"""``Select``/``Textarea``/``FormField`` attrs passthrough — rollout of #73's
``Button`` precedent, scoped by #76.

Same shape/escaping decisions as ``Button`` (see
``test_attrs_passthrough.py`` for the full writeup) — routed through the one
:func:`cf_ui.primitives.render_attrs` implementation, so no new validation or
escaping logic exists here.

The one design point specific to this rollout: all three components render
more than one element (a ``<div class="field">`` wrapper around the actual
control), and a caller's ``attrs`` belongs on the control — the ``<select>``,
``<textarea>``, or ``<input>`` — not the wrapper. Every assertion below checks
the passthrough attribute lands next to the control's own attributes (``id``,
``name``), which only holds if it renders on the right element.
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
        "select",
        "Select.jinja",
        {
            "name": "choice",
            "label": "Choose",
            "value": "",
            "error": "",
            "options": [],
            "extra_class": "",
            "input_class": "",
        },
    ),
    (
        "textarea",
        "Textarea.jinja",
        {
            "name": "bio",
            "label": "Bio",
            "value": "",
            "error": "",
            "rows": 4,
            "extra_class": "",
            "input_class": "",
        },
    ),
    (
        "form-field",
        "FormField.jinja",
        {
            "name": "email",
            "label": "Email",
            "value": "",
            "error": "",
            "type": "text",
            "required": False,
            "extra_class": "",
            "input_class": "",
        },
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


def test_renders_passthrough_attrs_on_the_control(render: Callable[..., str]) -> None:
    html = render(attrs={"data-event": "submit", "hx-get": "/things"})
    assert 'data-event="submit"' in html
    assert 'hx-get="/things"' in html


def test_passthrough_attrs_coexist_with_named_props(render: Callable[..., str]) -> None:
    html = render(input_class="js-field", attrs={"x-on:change": "go()"})
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


def test_rejects_attrs_colliding_with_id(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"id": "override"})


def test_rejects_attrs_colliding_with_name(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"name": "override"})


def test_attrs_do_not_land_on_the_field_wrapper(render: Callable[..., str]) -> None:
    """The passthrough belongs on the control, not the outer ``.field`` div —
    the design question #70 raised for every multi-element primitive."""
    html = render(attrs={"data-marker": "control-only"})
    wrapper_open, _, rest = html.partition(">")
    assert "data-marker" not in wrapper_open
    assert 'data-marker="control-only"' in rest
