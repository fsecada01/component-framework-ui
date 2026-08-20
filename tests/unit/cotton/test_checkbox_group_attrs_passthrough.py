"""``<c-cf.checkbox-group>`` attrs passthrough — rollout of #73's ``Button``
precedent, scoped by #70.

See ``tests/unit/jinja/test_checkbox_group_attrs_passthrough.py`` for the
full design writeup — ``attrs`` lands on the outer wrapper, not on any
per-choice ``<input>``, because ``CheckboxGroup`` renders N checkboxes and
has no single control to target. These go through ``cotton_render``
(``render_to_string``), which bypasses the django-cotton compiler per this
repo's CLAUDE.md — every prop, including ``attrs``, must be passed
explicitly here; the ``<c-vars attrs="{}" />`` default is only exercised by
the E2E tier.
"""

import re
from collections.abc import Callable

import pytest

from cf_ui.primitives import PrimitiveConfigError
from cf_ui.themes import THEMES

BASE_PROPS = {
    "name": "interests",
    "label": "Interests",
    "error": "",
    "choices": [{"value": "a", "label": "Alpha"}, {"value": "b", "label": "Beta"}],
    "selected": [],
    "control_class": "",
    "class": "",
}


@pytest.fixture(params=THEMES)
def render(
    request: pytest.FixtureRequest, settings: object, cotton_render: Callable[..., str]
) -> Callable[..., str]:
    settings.CF_UI_THEME = request.param

    def _render(**ctx: object) -> str:
        return cotton_render("cf/checkbox-group.html", **{**BASE_PROPS, "attrs": {}, **ctx})

    return _render


def test_cotton_renders_with_empty_attrs(render: Callable[..., str]) -> None:
    assert render().strip()


def test_cotton_renders_passthrough_attrs_on_the_wrapper(render: Callable[..., str]) -> None:
    """``cotton_render`` bypasses the django-cotton compiler, so the wrapper
    template's literal ``<c-vars .../>`` stub survives into the output ahead
    of the real markup — its own closing ``/>`` would be the first ``>`` in
    the document. Partition on the first per-choice ``<input`` instead, which
    correctly spans everything up to and including the real wrapper's
    opening tag."""
    html = render(attrs={"data-marker": "wrapper-only", "x-data": "{}"})
    before_first_input, _, _rest = html.partition("<input")
    assert 'data-marker="wrapper-only"' in before_first_input
    assert 'x-data="{}"' in before_first_input


def test_cotton_passthrough_attrs_do_not_land_on_a_checkbox_input(
    render: Callable[..., str],
) -> None:
    html = render(attrs={"data-marker": "wrapper-only"})
    for input_tag in re.findall(r"<input\b[^>]*>", html):
        assert "data-marker" not in input_tag


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
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"class": "override"})
