"""``attrs`` passthrough for Icon/Badge/Box/CheckboxGroup on the JinjaX path,
against a real catalog (#70).

See ``test_jinja_attrs_passthrough.py`` for the full writeup of why this
tier exists at all: the unit tier's Jinja2-``Environment``-only tests never
exercise a real ``jinjax.Catalog``, so a ``{#def}``/``ARGS_ATTRS``-level
regression like #78's would pass every unit test and only surface here.
These four primitives got unit coverage when their ``attrs`` passthrough was
added but no real-``Catalog`` coverage, unlike Button/FormField above — this
file closes that gap for the same reason #78 exists.
"""

import pytest
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui
from cf_ui.primitives import PrimitiveConfigError

HOSTILE = '" onmouseover="window.cfPwned=true" x="'


@pytest.fixture
def catalog() -> Catalog:
    cat = Catalog()
    install_cf_ui(cat, theme="bulma")
    return cat


def test_icon_attrs_pass_through_via_the_underscore_attrs_kwarg(catalog: Catalog) -> None:
    html = catalog.render("Cf:Icon", _content="*", _attrs={"data-testid": "star"})
    assert 'data-testid="star"' in html


def test_icon_attrs_collision_with_role_raises(catalog: Catalog) -> None:
    with pytest.raises(PrimitiveConfigError):
        catalog.render("Cf:Icon", _content="*", _attrs={"role": "override"})


def test_badge_attrs_pass_through_via_the_underscore_attrs_kwarg(catalog: Catalog) -> None:
    html = catalog.render("Cf:Badge", _content="New", _attrs={"data-testid": "badge"})
    assert 'data-testid="badge"' in html


def test_badge_attrs_collision_with_class_raises(catalog: Catalog) -> None:
    with pytest.raises(PrimitiveConfigError):
        catalog.render("Cf:Badge", _content="New", _attrs={"class": "override"})


def test_box_attrs_pass_through_via_the_underscore_attrs_kwarg(catalog: Catalog) -> None:
    html = catalog.render("Cf:Box", _content="Hello", _attrs={"data-testid": "box"})
    assert 'data-testid="box"' in html


def test_checkbox_group_attrs_land_on_the_wrapper_not_a_choice_input(catalog: Catalog) -> None:
    html = catalog.render(
        "Cf:CheckboxGroup",
        name="interests",
        label="Interests",
        choices=[{"value": "a", "label": "Alpha"}],
        _attrs={"data-testid": "group"},
    )
    before_first_input, _, _rest = html.partition("<input")
    assert 'data-testid="group"' in before_first_input


def test_checkbox_group_attrs_collision_with_class_raises(catalog: Catalog) -> None:
    with pytest.raises(PrimitiveConfigError):
        catalog.render(
            "Cf:CheckboxGroup",
            name="interests",
            label="Interests",
            choices=[],
            _attrs={"class": "override"},
        )


def test_hostile_attrs_value_is_still_escaped(catalog: Catalog) -> None:
    html = catalog.render("Cf:Icon", _content="*", _attrs={"data-x": HOSTILE})
    assert 'onmouseover="window.cfPwned=true"' not in html
