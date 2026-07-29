"""Unit tests for the theme composition axis layer (issue #5).

Each test group maps to one acceptance-criteria checklist item on the issue.
"""

import pytest

# --------------------------------------------------------------------------
# Criterion 1: axis definitions as CSS custom properties keyed on data
# attributes, shipped as a static asset.
# --------------------------------------------------------------------------


def test_axes_are_the_five_declared_axes():
    from cf_ui.axes import AXES

    assert AXES == ("accent", "surface", "form", "density", "type")


def test_theme_is_not_an_axis():
    """data-theme is the light/dark mode switch, not an identity axis."""
    from cf_ui.axes import AXES, AXIS_ATTRS

    assert "theme" not in AXES
    assert "data-theme" not in AXIS_ATTRS.values()


def test_each_axis_maps_to_its_data_attribute():
    from cf_ui.axes import AXES, AXIS_ATTRS

    assert set(AXIS_ATTRS) == set(AXES)
    for axis in AXES:
        assert AXIS_ATTRS[axis] == f"data-{axis}"


def test_axis_css_static_asset_exists():
    from cf_ui.axes import AXIS_CSS_PATH

    assert AXIS_CSS_PATH.is_file()
    assert AXIS_CSS_PATH.name == "cf_ui_axes.css"
    assert "static" in AXIS_CSS_PATH.parts


def test_axis_css_declares_a_selector_for_every_axis_value():
    from cf_ui.axes import AXIS_CSS_PATH, DEFAULT_VALUE_SETS

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    for axis, values in DEFAULT_VALUE_SETS.items():
        for value in values:
            assert f'[data-{axis}="{value}"]' in css


def test_axis_css_declares_custom_properties_not_bare_classes():
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert "--cf-accent:" in css
    assert "--cf-ground:" in css
    assert "--cf-radius:" in css


def test_shipped_axis_css_matches_generator_output():
    """The static asset is generated — this guards against hand-edit drift."""
    from cf_ui.axes import AXIS_CSS_PATH, DEFAULT_VALUE_SETS, render_axis_css

    expected = render_axis_css(DEFAULT_VALUE_SETS)
    actual = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert actual == expected, "run `python -m cf_ui.axes` to regenerate the axis stylesheet"


def test_wide_gamut_chroma_is_gated_on_color_gamut_not_supports():
    """@supports (color: oklch(...)) is a no-op — every current browser parses it."""
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert "@media (color-gamut: p3)" in css
    assert "@supports" not in css


def test_p3_layer_is_layered_over_an_srgb_base_declaration():
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    base, _, p3 = css.partition("@media (color-gamut: p3)")
    # sRGB-safe hex base must be declared before the p3 override
    assert "#0369a1" in base
    assert "oklch(" not in base
    assert "oklch(" in p3


def test_density_drives_tailwind_spacing_base_unit():
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert "--spacing:" in css


def test_accent_exposes_a_strong_token_for_small_text():
    from cf_ui.axes import DEFAULT_VALUE_SETS

    for value in DEFAULT_VALUE_SETS["accent"].values():
        for mode in ("light", "dark"):
            assert "--cf-accent-strong" in value[mode]


# --------------------------------------------------------------------------
# Criterion 2: a composition setting — one value per axis, or a named
# composition resolving to five.
# --------------------------------------------------------------------------


def test_named_composition_resolves_to_all_five_axes():
    from cf_ui.axes import AXES, resolve_composition

    resolved = resolve_composition("default")
    assert set(resolved) == set(AXES)


def test_every_shipped_composition_resolves_to_all_five_axes():
    from cf_ui.axes import AXES, DEFAULT_COMPOSITIONS, resolve_composition

    for name in DEFAULT_COMPOSITIONS:
        resolved = resolve_composition(name)
        assert set(resolved) == set(AXES), f"composition {name!r} is incomplete"


def test_none_resolves_to_the_default_composition():
    from cf_ui.axes import resolve_composition

    assert resolve_composition(None) == resolve_composition("default")


def test_per_axis_mapping_overrides_only_named_axes():
    from cf_ui.axes import resolve_composition

    resolved = resolve_composition({"accent": "jade"})
    assert resolved["accent"] == "jade"
    assert resolved["surface"] == resolve_composition("default")["surface"]


def test_unknown_composition_name_is_rejected():
    from cf_ui.axes import AxisConfigError, resolve_composition

    with pytest.raises(AxisConfigError, match="nope"):
        resolve_composition("nope")


def test_unknown_axis_name_is_rejected():
    from cf_ui.axes import AxisConfigError, resolve_composition

    with pytest.raises(AxisConfigError, match="flavour"):
        resolve_composition({"flavour": "vanilla"})


def test_unknown_axis_value_is_rejected_and_lists_valid_values():
    from cf_ui.axes import AxisConfigError, resolve_composition

    with pytest.raises(AxisConfigError) as exc:
        resolve_composition({"accent": "hotpink"})
    message = str(exc.value)
    assert "hotpink" in message
    assert "azure" in message, "error should name the valid values"


# --------------------------------------------------------------------------
# Criterion 3: one template helper stamping all five attributes.
# --------------------------------------------------------------------------


def test_root_attrs_stamps_all_five_attributes():
    from cf_ui.axes import AXES, root_attrs

    attrs = root_attrs("default")
    for axis in AXES:
        assert f'data-{axis}="' in attrs


def test_root_attrs_reflects_the_resolved_values():
    from cf_ui.axes import root_attrs

    attrs = root_attrs({"accent": "jade", "density": "compact"})
    assert 'data-accent="jade"' in attrs
    assert 'data-density="compact"' in attrs


def test_root_attrs_does_not_stamp_theme():
    from cf_ui.axes import root_attrs

    assert "data-theme" not in root_attrs("default")


def test_root_attrs_rejects_an_invalid_composition():
    from cf_ui.axes import AxisConfigError, root_attrs

    with pytest.raises(AxisConfigError):
        root_attrs({"accent": "hotpink"})


# --------------------------------------------------------------------------
# Criterion 4: apps may supply their own value sets, replacing or extending.
# --------------------------------------------------------------------------

CUSTOM_ACCENT = {
    "accent": {
        "brand": {
            "light": {
                "--cf-accent": "#6d28d9",
                "--cf-accent-content": "#ffffff",
                "--cf-accent-strong": "#5b21b6",
            },
            "dark": {
                "--cf-accent": "#a78bfa",
                "--cf-accent-content": "#2e1065",
                "--cf-accent-strong": "#c4b5fd",
            },
        }
    }
}


def test_extend_keeps_the_defaults_and_adds_the_custom_value():
    from cf_ui.axes import merge_value_sets

    merged = merge_value_sets(CUSTOM_ACCENT, mode="extend")
    assert "brand" in merged["accent"]
    assert "azure" in merged["accent"], "extend must not drop shipped values"


def test_replace_drops_the_defaults_for_that_axis_only():
    from cf_ui.axes import merge_value_sets

    merged = merge_value_sets(CUSTOM_ACCENT, mode="replace")
    assert set(merged["accent"]) == {"brand"}
    assert "regular" in merged["density"], "untouched axes keep their defaults"


def test_merge_does_not_mutate_the_shipped_defaults():
    from cf_ui.axes import DEFAULT_VALUE_SETS, merge_value_sets

    merge_value_sets(CUSTOM_ACCENT, mode="replace")
    assert "azure" in DEFAULT_VALUE_SETS["accent"]


def test_unknown_merge_mode_is_rejected():
    from cf_ui.axes import AxisConfigError, merge_value_sets

    with pytest.raises(AxisConfigError, match="clobber"):
        merge_value_sets(CUSTOM_ACCENT, mode="clobber")


def test_custom_value_is_resolvable_and_stampable():
    from cf_ui.axes import merge_value_sets, root_attrs

    merged = merge_value_sets(CUSTOM_ACCENT)
    assert 'data-accent="brand"' in root_attrs({"accent": "brand"}, value_sets=merged)


def test_custom_value_is_still_rejected_against_the_defaults():
    from cf_ui.axes import AxisConfigError, root_attrs

    with pytest.raises(AxisConfigError):
        root_attrs({"accent": "brand"})


def test_custom_axis_css_emits_only_the_values_the_static_asset_lacks():
    from cf_ui.axes import custom_axis_css, merge_value_sets

    css = custom_axis_css(merge_value_sets(CUSTOM_ACCENT))
    assert '[data-accent="brand"]' in css
    assert '[data-accent="azure"]' not in css, "shipped values already live in the static asset"


def test_custom_axis_css_is_empty_when_nothing_was_customised():
    from cf_ui.axes import DEFAULT_VALUE_SETS, custom_axis_css

    assert custom_axis_css(DEFAULT_VALUE_SETS) == ""


def test_custom_axis_css_emits_a_shadowed_value_whose_tokens_differ():
    """Same name, different tokens — the static asset's copy is now wrong."""
    from cf_ui.axes import custom_axis_css, merge_value_sets

    shadow = {"accent": {"azure": CUSTOM_ACCENT["accent"]["brand"]}}
    css = custom_axis_css(merge_value_sets(shadow))
    assert '[data-accent="azure"]' in css


# --------------------------------------------------------------------------
# Criterion 5: every accent x surface x mode combination passes WCAG AA.
# --------------------------------------------------------------------------


def test_contrast_ratio_matches_known_reference_values():
    from cf_ui.axes import contrast_ratio

    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, abs=0.01)


ACCENT_SURFACE_MODE = [
    (accent, surface, mode)
    for accent in ("slate", "azure", "jade")
    for surface in ("plain", "muted")
    for mode in ("light", "dark")
]


@pytest.mark.parametrize(("accent", "surface", "mode"), ACCENT_SURFACE_MODE)
def test_default_value_sets_pass_wcag_aa(accent, surface, mode):
    from cf_ui.axes import DEFAULT_VALUE_SETS, contrast_failures

    failures = contrast_failures(DEFAULT_VALUE_SETS, accent, surface, mode)
    assert failures == [], f"{accent}/{surface}/{mode}: {failures}"


def test_wcag_matrix_covers_every_shipped_combination():
    """Guard against a new accent or surface skipping the contrast gate."""
    from cf_ui.axes import DEFAULT_VALUE_SETS

    expected = {
        (accent, surface, mode)
        for accent in DEFAULT_VALUE_SETS["accent"]
        for surface in DEFAULT_VALUE_SETS["surface"]
        for mode in ("light", "dark")
    }
    assert set(ACCENT_SURFACE_MODE) == expected


def test_contrast_failures_flags_an_inaccessible_custom_value():
    from cf_ui.axes import contrast_failures, merge_value_sets

    washed_out = {
        "accent": {
            "pale": {
                "light": {
                    "--cf-accent": "#fef9c3",
                    "--cf-accent-content": "#fefce8",
                    "--cf-accent-strong": "#fef08a",
                },
                "dark": {
                    "--cf-accent": "#fef9c3",
                    "--cf-accent-content": "#fefce8",
                    "--cf-accent-strong": "#fef08a",
                },
            }
        }
    }
    merged = merge_value_sets(washed_out)
    assert contrast_failures(merged, "pale", "plain", "light") != []


def test_contrast_requirement_is_documented():
    from pathlib import Path

    doc = Path(__file__).parent.parent.parent / "docs" / "theming.md"
    assert doc.is_file(), "theming docs must exist"
    text = doc.read_text(encoding="utf-8").lower()
    assert "wcag" in text
    assert "contrast" in text


# --------------------------------------------------------------------------
# Criterion 6: light and dark are independently declared, never derived by
# inversion.
# --------------------------------------------------------------------------


def test_mode_keyed_axes_declare_both_modes_explicitly():
    from cf_ui.axes import DEFAULT_VALUE_SETS, MODE_KEYED_AXES

    for axis in MODE_KEYED_AXES:
        for name, value in DEFAULT_VALUE_SETS[axis].items():
            assert "light" in value, f"{axis}/{name} has no light declaration"
            assert "dark" in value, f"{axis}/{name} has no dark declaration"


def test_light_and_dark_declare_the_same_token_names():
    from cf_ui.axes import DEFAULT_VALUE_SETS, MODE_KEYED_AXES

    for axis in MODE_KEYED_AXES:
        for name, value in DEFAULT_VALUE_SETS[axis].items():
            assert set(value["light"]) == set(value["dark"]), f"{axis}/{name} token sets differ"


def _invert(hexstr: str) -> str:
    h = hexstr.lstrip("#")
    return "#" + "".join(f"{255 - int(h[i : i + 2], 16):02x}" for i in (0, 2, 4))


def test_dark_is_not_a_mechanical_inversion_of_light():
    from cf_ui.axes import DEFAULT_VALUE_SETS, MODE_KEYED_AXES

    for axis in MODE_KEYED_AXES:
        for name, value in DEFAULT_VALUE_SETS[axis].items():
            inverted = {k: _invert(v) for k, v in value["light"].items()}
            assert value["dark"] != inverted, f"{axis}/{name} dark looks machine-inverted"


def test_dark_mode_css_is_keyed_on_data_theme():
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert '[data-theme="dark"][data-accent="azure"]' in css


def test_light_mode_css_is_the_unqualified_declaration():
    """Light must not require data-theme="light" to be present."""
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert '[data-theme="light"]' not in css
