"""Django-side wiring for the theme composition axes (issue #5).

Covers the config setting, the root-attribute template tag, and delivery of
the axis stylesheet through the existing asset tags.
"""

import pytest
from django.utils.safestring import SafeString

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


# --- Criterion 2: CfUiConfig gains a composition setting -------------------


def test_appconfig_accepts_a_named_composition(settings):
    from django.apps import apps

    settings.CF_UI_COMPOSITION = "default"
    apps.get_app_config("cf_ui").ready()


def test_appconfig_rejects_an_unknown_axis_value(settings):
    from django.apps import apps
    from django.core.exceptions import ImproperlyConfigured

    settings.CF_UI_COMPOSITION = {"accent": "hotpink"}
    with pytest.raises(ImproperlyConfigured, match="hotpink"):
        apps.get_app_config("cf_ui").ready()


def test_appconfig_rejects_an_unknown_composition_name(settings):
    from django.apps import apps
    from django.core.exceptions import ImproperlyConfigured

    settings.CF_UI_COMPOSITION = "brutalist"
    with pytest.raises(ImproperlyConfigured, match="brutalist"):
        apps.get_app_config("cf_ui").ready()


def test_appconfig_accepts_a_custom_value_supplied_by_the_app(settings):
    from django.apps import apps

    settings.CF_UI_AXIS_VALUES = CUSTOM_ACCENT
    settings.CF_UI_COMPOSITION = {"accent": "brand"}
    apps.get_app_config("cf_ui").ready()


# --- Criterion 3: one setting, five attributes -----------------------------


def test_root_attrs_tag_stamps_all_five_axes(settings):
    from cf_ui.axes import AXES
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_COMPOSITION = "default"
    result = cf_ui_root_attrs()
    for axis in AXES:
        assert f'data-{axis}="' in result


def test_root_attrs_tag_reflects_the_configured_composition(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_COMPOSITION = {"accent": "jade", "density": "compact"}
    result = cf_ui_root_attrs()
    assert 'data-accent="jade"' in result
    assert 'data-density="compact"' in result


def test_root_attrs_tag_defaults_when_setting_is_absent(settings):
    from cf_ui.axes import AXES
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_THEME = "bulma"  # CF_UI_COMPOSITION deliberately left unset
    result = cf_ui_root_attrs()
    for axis in AXES:
        assert f'data-{axis}="' in result


def test_root_attrs_tag_output_is_marked_safe(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_COMPOSITION = "default"
    assert isinstance(cf_ui_root_attrs(), SafeString)


def test_root_attrs_tag_renders_in_a_template(settings):
    from django.template import Context, Template

    settings.CF_UI_COMPOSITION = {"accent": "azure"}
    rendered = Template("{% load cf_ui %}<html {% cf_ui_root_attrs %}>").render(Context({}))
    assert 'data-accent="azure"' in rendered
    assert "&quot;" not in rendered


def test_root_attrs_tag_honours_custom_value_sets(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_AXIS_VALUES = CUSTOM_ACCENT
    settings.CF_UI_COMPOSITION = {"accent": "brand"}
    assert 'data-accent="brand"' in cf_ui_root_attrs()


# --- Criterion 1 + 4: stylesheet delivery through the asset tags -----------


def test_cf_ui_head_links_the_axis_stylesheet(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "bulma"
    assert "cf_ui_axes.css" in cf_ui_head()


def test_cf_ui_head_inlines_css_for_custom_value_sets(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_AXIS_VALUES = CUSTOM_ACCENT
    result = cf_ui_head()
    assert "<style>" in result
    assert '[data-accent="brand"]' in result
    assert "#6d28d9" in result


def test_cf_ui_head_has_no_inline_style_block_without_custom_sets(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_AXIS_VALUES = {}
    assert '[data-accent="' not in cf_ui_head()


def test_replace_mode_makes_shipped_values_unavailable(settings):
    from cf_ui.axes import AxisConfigError
    from cf_ui.templatetags.cf_ui import cf_ui_root_attrs

    settings.CF_UI_AXIS_VALUES = CUSTOM_ACCENT
    settings.CF_UI_AXIS_VALUES_MODE = "replace"
    settings.CF_UI_COMPOSITION = {"accent": "brand"}
    assert 'data-accent="brand"' in cf_ui_root_attrs()

    settings.CF_UI_COMPOSITION = {"accent": "azure"}
    with pytest.raises(AxisConfigError, match="azure"):
        cf_ui_root_attrs()
