"""``<c-cf.select>``/``<c-cf.textarea>``/``<c-cf.form-field>`` attrs
passthrough — rollout of #73's ``Button`` precedent, scoped by #76.

See ``tests/unit/jinja/test_select_textarea_form_field_attrs_passthrough.py``
for the full design writeup (shape/escaping/wrapper-vs-control). These go
through ``cotton_render`` (``render_to_string``), which bypasses the
django-cotton compiler per this repo's CLAUDE.md — every prop, including
``attrs``, must be passed explicitly here; the ``<c-vars attrs="{}" />``
default is only exercised by the E2E tier.
"""

from collections.abc import Callable

import pytest

from cf_ui.primitives import PrimitiveConfigError
from cf_ui.themes import THEMES

CASES = [
    (
        "select",
        "cf/select.html",
        {"name": "choice", "label": "Choose", "value": "", "error": "", "options": [], "class": ""},
    ),
    (
        "textarea",
        "cf/textarea.html",
        {"name": "bio", "label": "Bio", "value": "", "error": "", "rows": "4", "class": ""},
    ),
    (
        "form-field",
        "cf/form-field.html",
        {
            "name": "email",
            "label": "Email",
            "value": "",
            "error": "",
            "type": "text",
            "required": "false",
            "class": "",
        },
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


def test_cotton_renders_passthrough_attrs_on_the_control(render: Callable[..., str]) -> None:
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


def test_cotton_rejects_attrs_colliding_with_id(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"id": "override"})


def test_cotton_rejects_attrs_colliding_with_name(render: Callable[..., str]) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"name": "override"})


def test_cotton_rejects_attrs_colliding_with_aria_invalid(render: Callable[..., str]) -> None:
    """Static reservation — only Foundation renders ``aria-invalid`` itself,
    but the guard must reject the collision for every theme regardless."""
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"aria-invalid": "false"})


def test_cotton_rejects_attrs_colliding_with_aria_describedby(
    render: Callable[..., str],
) -> None:
    with pytest.raises(PrimitiveConfigError):
        render(attrs={"aria-describedby": "custom-hint"})


def test_cotton_attrs_do_not_land_on_the_field_wrapper(render: Callable[..., str]) -> None:
    html = render(attrs={"data-marker": "control-only"})
    wrapper_open, _, rest = html.partition(">")
    assert "data-marker" not in wrapper_open
    assert 'data-marker="control-only"' in rest
