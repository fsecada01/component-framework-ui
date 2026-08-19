"""``Cf:Button`` attribute passthrough — spike from #72, resolved for #71.

Design settled here (see the PR body for the full trade-off writeup):

* **Shape**: ``attrs: dict[str, str] | None`` rendering as literal
  ``key="value"`` pairs on the root element, iterated with
  ``{% for k, v in attrs.items() %}``. Chosen over named passthrough props
  (`data_*`/`x_*`/`hx_*`) because the caller's attribute names are open-ended
  by definition (``hx-get``, ``@click``, ``x-model.debounce.500ms``) and a
  fixed prop set can't cover them; chosen over a raw ``extra_attrs: str``
  escape hatch because the string form is exactly the shape that bypasses
  autoescaping (docs/escaping.md) and would reopen the injection risk that
  block exists to close.
* **Escaping**: no new escaping code. Every Button template already wraps its
  body in ``{% autoescape true %}`` (#36); interpolating each key/value pair
  with ``{{ }}`` gets the same guarantee every other prop gets, so a hostile
  attribute value is neutralized exactly like a hostile ``header`` string is.
* **Scope**: ``Button`` only, all five themes, per the issue's own
  recommendation ("Button first, since it's the most commonly
  attribute-bearing"). Rollout to the rest of Tier 1 is separate follow-up
  work.

These tests render straight off disk with autoescape *off* at the harness
level (see ``tests/jinja_env.py``) so a passing escaping test can only mean
the template's own block did the work — the same discipline #36 established
for every other prop.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment

from cf_ui.primitives import build_primitive_globals
from cf_ui.themes import THEMES
from tests.jinja_env import make_env

JINJA_DIR = Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "jinja"


@pytest.fixture(params=THEMES)
def theme(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def env(theme: str) -> Environment:
    """``Button.jinja`` calls ``cf_ui_validate`` — bind it, unlike the plain
    ``make_env`` fixture other Tier-2-component tests share, which never
    render a primitive that needs the guard."""
    e = make_env(JINJA_DIR / theme)
    e.globals.update(build_primitive_globals())
    return e


@pytest.fixture
def render(env: Environment) -> Callable[..., str]:
    def _render(**ctx: object) -> str:
        return env.get_template("Button.jinja").render(content="Go", **ctx)

    return _render


def test_button_renders_with_no_attrs_prop_at_all(render: Callable[..., str]) -> None:
    """Omitting ``attrs`` entirely must not break rendering (StrictUndefined)."""
    html = render()
    assert "Go" in html


def test_button_renders_passthrough_attrs(render: Callable[..., str]) -> None:
    html = render(attrs={"data-event": "submit", "hx-get": "/things"})
    assert 'data-event="submit"' in html
    assert 'hx-get="/things"' in html


def test_button_passthrough_attrs_coexist_with_named_props(
    render: Callable[..., str],
) -> None:
    html = render(variant="primary", extra_class="js-cta", attrs={"x-on:click": "go()"})
    assert 'x-on:click="go()"' in html
    assert "js-cta" in html


def test_button_escapes_a_hostile_attr_value(render: Callable[..., str]) -> None:
    html = render(attrs={"data-x": '" onmouseover="alert(1)" x="'})
    assert 'onmouseover="alert(1)"' not in html


def test_button_escapes_a_hostile_attr_name(render: Callable[..., str]) -> None:
    html = render(attrs={'x" onmouseover="alert(1)': "y"})
    assert 'onmouseover="alert(1)"' not in html
