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


def test_density_does_not_alias_tailwinds_spacing_base_unit():
    """#20: --spacing is Tailwind's whole spacing scale, not a name cf-ui owns.

    Aliasing it meant `data-density` silently rescaled every `p-4` and `gap-2`
    in the consuming app, including for Bulma consumers who use none of it.
    `--cf-spacing` is still emitted; wiring it up is now the app's explicit
    one-line opt-in.
    """
    from cf_ui.axes import AXIS_CSS_PATH

    css = AXIS_CSS_PATH.read_text(encoding="utf-8")
    assert "--cf-spacing:" in css, "the axis token itself must still be emitted"
    assert "--spacing:" not in css.replace("--cf-spacing:", "")


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


# --------------------------------------------------------------------------
# Issue #20 §1: token *values* are validated, not just token names.
#
# Values are interpolated straight into a <style> element. A value carrying a
# semicolon or a brace closes its own declaration and writes rules the app
# never authored; "</style>" escapes the element entirely.
# --------------------------------------------------------------------------

UNSAFE_VALUES = [
    pytest.param("0; } body { display: none", id="semicolon-and-braces"),
    pytest.param("red; color: blue", id="semicolon"),
    pytest.param("}", id="close-brace"),
    pytest.param("{", id="open-brace"),
    pytest.param("red /* c", id="comment-open"),
    pytest.param("red */", id="comment-close"),
    pytest.param("</style><script>alert(1)</script>", id="style-escape"),
    pytest.param("<", id="angle-bracket"),
]


@pytest.mark.parametrize("value", UNSAFE_VALUES)
def test_unsafe_token_values_are_rejected(value):
    from cf_ui.axes import AxisConfigError, merge_value_sets

    with pytest.raises(AxisConfigError, match="unsafe value"):
        merge_value_sets({"form": {"evil": {"--cf-radius": value}}})


@pytest.mark.parametrize("value", UNSAFE_VALUES)
def test_unsafe_token_values_are_rejected_inside_a_mode_block(value):
    """Mode-keyed axes validate through a different branch — cover it too."""
    from cf_ui.axes import AxisConfigError, merge_value_sets

    payload = {
        "accent": {
            "evil": {
                "light": {"--cf-accent": value},
                "dark": {"--cf-accent": "#ffffff"},
            }
        }
    }
    with pytest.raises(AxisConfigError, match="unsafe value"):
        merge_value_sets(payload)


def test_unsafe_token_values_are_rejected_inside_a_p3_block():
    """The p3 block reaches the same stylesheet, so it needs the same gate."""
    from cf_ui.axes import AxisConfigError, merge_value_sets

    payload = {
        "accent": {
            "evil": {
                "light": {"--cf-accent": "#0369a1"},
                "dark": {"--cf-accent": "#38bdf8"},
                "p3": {"light": {"--cf-accent": "oklch(50% 0.1 240); } html { x: y"}},
            }
        }
    }
    with pytest.raises(AxisConfigError, match="unsafe value"):
        merge_value_sets(payload)


def test_a_non_string_token_value_is_rejected():
    """Mirrors the plugin, which rejects anything that is not a string."""
    from cf_ui.axes import AxisConfigError, merge_value_sets

    with pytest.raises(AxisConfigError, match="non-string"):
        merge_value_sets({"form": {"odd": {"--cf-radius": 0}}})


@pytest.mark.parametrize(
    "value",
    ["0", "0.375rem", "none", "0 1px 2px rgb(0 0 0 / 0.08)", "#ffffff", "1.25"],
)
def test_legitimate_token_values_are_still_accepted(value):
    from cf_ui.axes import merge_value_sets

    merged = merge_value_sets({"form": {"fine": {"--cf-radius": value}}})
    assert merged["form"]["fine"]["--cf-radius"] == value


def test_no_shipped_value_trips_the_new_rule():
    """Font stacks carry commas and quotes — they must survive the gate."""
    from cf_ui.axes import DEFAULT_VALUE_SETS, merge_value_sets

    # Re-validating the shipped sets through the public entry point is the
    # point: a rule that rejected our own defaults would be caught here.
    merged = merge_value_sets(DEFAULT_VALUE_SETS)
    assert "Segoe UI" in merged["type"]["system"]["--cf-font-display"]


def test_the_injection_payload_never_reaches_a_style_element():
    """End-to-end: the escape hatch this closes is style_element()."""
    from cf_ui.axes import AxisConfigError, merge_value_sets

    with pytest.raises(AxisConfigError):
        merge_value_sets({"form": {"evil": {"--cf-radius": "0; } body { display: none"}}})


# --------------------------------------------------------------------------
# Issue #20 §4: the exported generators validate too, not just merge_value_sets.
#
# An exported function that generates CSS with the gate switched off is the
# generator with the build error removed. The plugin's buildAxisBase/buildAxisCss
# were fixed for exactly this; these are their Python counterparts, and
# style_element() is the sink the whole §1 gate exists to protect.
# --------------------------------------------------------------------------

EVIL_SET = {"form": {"evil": {"--cf-radius": "0; } body { display: none"}}}


@pytest.mark.parametrize("generator", ["render_axis_css", "custom_axis_css", "style_element"])
def test_the_exported_generators_validate_by_default(generator):
    import cf_ui.axes as axes

    with pytest.raises(axes.AxisConfigError, match="unsafe value"):
        getattr(axes, generator)(EVIL_SET)


@pytest.mark.parametrize("generator", ["render_axis_css", "custom_axis_css", "style_element"])
def test_the_generators_take_an_explicit_opt_out(generator):
    """The escape hatch stays — you just have to ask for it."""
    import cf_ui.axes as axes

    output = getattr(axes, generator)(EVIL_SET, validate=False)
    assert "display: none" in output


def test_style_element_no_longer_emits_an_injection_payload():
    """The concrete regression: this used to render the payload into the page."""
    from cf_ui.axes import AxisConfigError, style_element

    with pytest.raises(AxisConfigError):
        style_element(EVIL_SET)


def test_the_opt_out_does_not_change_what_valid_input_produces():
    """Guards against validation quietly altering the generated CSS."""
    from cf_ui.axes import DEFAULT_VALUE_SETS, render_axis_css

    assert render_axis_css(DEFAULT_VALUE_SETS) == render_axis_css(
        DEFAULT_VALUE_SETS, validate=False
    )


def test_the_generators_reject_an_unknown_axis():
    from cf_ui.axes import AxisConfigError, render_axis_css

    with pytest.raises(AxisConfigError, match="flavour"):
        render_axis_css({"flavour": {"vanilla": {"--cf-radius": "0"}}})


# --------------------------------------------------------------------------
# Issue #20 §3: the p3 layer holds the base declaration's lightness.
#
# The contrast gate is computed against the sRGB base. The docs claim the p3
# override is "layered over that base at the same lightness, so the contrast
# guarantee still holds" — that was a convention held by hand until now.
# --------------------------------------------------------------------------


def test_oklab_lightness_matches_known_reference_values():
    """Guards the conversion itself — a wrong L would make the gate vacuous."""
    from cf_ui.axes import oklab_lightness

    assert oklab_lightness("#000000") == pytest.approx(0.0, abs=0.001)
    assert oklab_lightness("#ffffff") == pytest.approx(1.0, abs=0.001)
    # Authored p3 override for azure/light is oklch(50.0% ...)
    assert oklab_lightness("#0369a1") == pytest.approx(0.500, abs=0.002)


def test_oklch_lightness_parses_the_authored_form():
    from cf_ui.axes import oklch_lightness

    assert oklch_lightness("oklch(50.0% 0.137 242.7)") == pytest.approx(0.50, abs=0.0001)
    assert oklch_lightness("oklch(82.8% 0.116 230.3)") == pytest.approx(0.828, abs=0.0001)


def test_shipped_p3_overrides_hold_the_lightness_invariant():
    """This is the guarantee the docs already claim. Now it fails CI."""
    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    assert p3_lightness_failures(DEFAULT_VALUE_SETS) == []


def test_a_p3_override_with_a_different_lightness_is_flagged():
    """The mutation the gate exists to catch."""
    from copy import deepcopy

    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    drifted = deepcopy(DEFAULT_VALUE_SETS)
    drifted["accent"]["azure"]["p3"]["light"]["--cf-accent"] = "oklch(72.0% 0.137 242.7)"
    failures = p3_lightness_failures(drifted)
    assert failures, "a 22-point lightness shift must be flagged"
    assert "--cf-accent" in failures[0]
    assert "azure" in failures[0]


def test_the_lightness_gate_tolerates_authored_rounding():
    """Values are authored to one decimal place; the gate must not be brittle."""
    from copy import deepcopy

    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    rounded = deepcopy(DEFAULT_VALUE_SETS)
    # azure/light base measures 49.998%; the authored 50.0% must stay legal.
    rounded["accent"]["azure"]["p3"]["light"]["--cf-accent"] = "oklch(50.0% 0.137 242.7)"
    assert p3_lightness_failures(rounded) == []


def test_a_p3_override_of_an_undeclared_token_is_flagged():
    """A p3 block may only refine tokens the base declares."""
    from copy import deepcopy

    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    orphan = deepcopy(DEFAULT_VALUE_SETS)
    orphan["accent"]["azure"]["p3"]["light"]["--cf-nonexistent"] = "oklch(50% 0.1 240)"
    failures = p3_lightness_failures(orphan)
    assert any("--cf-nonexistent" in failure for failure in failures)


def test_a_non_oklch_p3_value_is_flagged_rather_than_skipped():
    """Silently skipping unparseable values is how the gate went blind before."""
    from copy import deepcopy

    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    bad = deepcopy(DEFAULT_VALUE_SETS)
    bad["accent"]["azure"]["p3"]["light"]["--cf-accent"] = "#0369a1"
    assert p3_lightness_failures(bad) != []
