"""The exported axis definition (issue #7).

The Tailwind plugin runs inside the CSS build, where Python is not. It cannot
import ``cf_ui.axes``, so the definition has to cross the language boundary as
data. These tests pin that boundary: the export is complete enough for the
plugin to do its job, it is genuinely JSON-serializable, and the committed
artifact has not drifted from the module that generates it.

``axes.py`` stays the single source of truth. The JSON is a build product of
it, exactly as ``cf_ui_axes.css`` is — there is no second generator.
"""

from __future__ import annotations

import json

import pytest

from cf_ui.axes import (
    AXES,
    AXIS_ATTRS,
    AXIS_DEFINITION_PATH,
    DEFAULT_COMPOSITIONS,
    DEFAULT_VALUE_SETS,
    MODE_KEYED_AXES,
    MODES,
    axis_definition,
)


@pytest.fixture(scope="module")
def definition() -> dict:
    return axis_definition()


# --- shape -----------------------------------------------------------------


def test_definition_is_json_serializable(definition):
    """A tuple or a Path in here would blow up at generation time, not here."""
    assert json.loads(json.dumps(definition)) == definition


def test_definition_carries_every_axis(definition):
    assert definition["axes"] == list(AXES)
    assert definition["modeKeyedAxes"] == list(MODE_KEYED_AXES)
    assert definition["modes"] == list(MODES)


def test_definition_carries_the_data_attribute_names(definition):
    """The plugin builds selectors from these; it must not re-derive them."""
    assert definition["axisAttrs"] == dict(AXIS_ATTRS)


def test_definition_carries_the_tailwind_aliases(definition):
    """Without the aliases the generated CSS would not feed Tailwind's theme."""
    assert definition["aliases"]["--cf-accent"] == "--color-primary"


def test_definition_carries_every_shipped_value(definition):
    for axis in AXES:
        assert set(definition["valueSets"][axis]) == set(DEFAULT_VALUE_SETS[axis])


def test_definition_carries_the_named_compositions(definition):
    assert definition["compositions"] == DEFAULT_COMPOSITIONS


def test_definition_carries_the_contrast_pairs(definition):
    """The contrast report is generated in JS, from the same thresholds."""
    pairs = definition["contrastPairs"]
    assert pairs, "no contrast pairs exported"
    for pair in pairs:
        assert set(pair) == {"foreground", "background", "minimum"}
        assert pair["foreground"].startswith("--")
        assert isinstance(pair["minimum"], float)
    assert {"foreground": "--cf-text", "background": "--cf-ground", "minimum": 4.5} in pairs


def test_definition_preserves_the_p3_blocks(definition):
    """The p3 layer is generated from this, so it has to survive the export."""
    assert definition["valueSets"]["accent"]["azure"]["p3"]["light"]["--cf-accent"].startswith(
        "oklch("
    )


def test_definition_is_a_copy_not_a_live_reference(definition):
    """Mutating the export must not corrupt the module's own value sets."""
    export = axis_definition()
    export["valueSets"]["accent"].pop("slate", None)
    assert "slate" in DEFAULT_VALUE_SETS["accent"]
    assert "slate" in axis_definition()["valueSets"]["accent"]


# --- the committed artifact ------------------------------------------------


def test_the_definition_file_is_committed():
    assert AXIS_DEFINITION_PATH.is_file(), (
        f"{AXIS_DEFINITION_PATH} is missing — regenerate with `python -m cf_ui.axes`"
    )


def test_the_definition_file_has_not_drifted(definition):
    """The same guard cf_ui_axes.css has: edit axes.py, regenerate, commit."""
    on_disk = json.loads(AXIS_DEFINITION_PATH.read_text(encoding="utf-8"))
    assert on_disk == definition, (
        "cf_ui_axes.json is stale — regenerate with `python -m cf_ui.axes`"
    )


def test_the_definition_file_ships_in_the_package():
    """It sits beside the plugin that reads it, inside the installed package."""
    from cf_ui.axes import AXIS_CSS_PATH

    assert AXIS_DEFINITION_PATH.parent == AXIS_CSS_PATH.parent
    assert AXIS_DEFINITION_PATH.name == "cf_ui_axes.json"
