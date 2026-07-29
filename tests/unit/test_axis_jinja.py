"""Jinja2/JinjaX-side wiring for the theme composition axes (issue #5).

The assets.jinja macros hold no axis data of their own — they delegate to the
``cf_ui_axis_attrs`` / ``cf_ui_axis_style`` globals that the FastAPI and
Litestar installers register, so cf_ui.axes stays the single source of truth.
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui" / "templates"

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


@pytest.fixture
def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )


def _render(env: Environment, body: str) -> str:
    return env.from_string(
        '{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_root_attrs %}' + body
    ).render()


class _Catalog:
    """Minimal stand-in for a JinjaX ComponentCatalog."""

    def __init__(self, env: Environment) -> None:
        self.jinja_env = env
        self.folders: list = []

    def add_folder(self, path, prefix=None) -> None:
        self.folders.append((path, prefix))


class _LitestarEngine:
    def __init__(self, env: Environment) -> None:
        self.engine = env


# --- Criterion 1: stylesheet delivered through the existing asset tags -----


def test_head_macro_links_the_axis_stylesheet(env):
    assert "cf_ui_axes.css" in _render(env, '{{ cf_ui_head(theme="bulma") }}')


def test_head_macro_axis_stylesheet_url_is_overridable(env):
    out = _render(env, '{{ cf_ui_head(theme="bulma", cf_axes_url="/assets/axes.css") }}')
    assert "/assets/axes.css" in out


def test_head_macro_still_links_the_theme_css(env):
    out = _render(env, '{{ cf_ui_head(theme="bulma") }}')
    assert "bulma.min.css" in out


# --- Criterion 3: the root-attribute helper --------------------------------


def test_root_attrs_macro_is_inert_without_the_installer(env):
    """A plain Jinja2 app that never called install_cf_ui must not explode."""
    assert "data-" not in _render(env, "<html {{ cf_ui_root_attrs() }}>")


def test_root_attrs_macro_stamps_five_attributes_after_install(env):
    from cf_ui.axes import AXES
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma", composition="default")
    out = _render(env, "<html {{ cf_ui_root_attrs() }}>")
    for axis in AXES:
        assert f'data-{axis}="' in out


def test_root_attrs_macro_is_not_html_escaped(env):
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma", composition={"accent": "jade"})
    out = _render(env, "<html {{ cf_ui_root_attrs() }}>")
    assert 'data-accent="jade"' in out
    assert "&quot;" not in out


# --- FastAPI installer -----------------------------------------------------


def test_fastapi_installer_still_registers_the_template_folder(env):
    from cf_ui import JINJA_TEMPLATES_DIR
    from cf_ui.fastapi import install_cf_ui

    catalog = _Catalog(env)
    install_cf_ui(catalog, theme="bulma")
    assert catalog.folders == [(JINJA_TEMPLATES_DIR / "bulma", "Cf")]


def test_fastapi_installer_registers_the_axis_globals(env):
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma", composition="default")
    assert callable(env.globals["cf_ui_axis_attrs"])
    assert callable(env.globals["cf_ui_axis_style"])


def test_fastapi_installer_rejects_an_invalid_composition(env):
    from cf_ui.axes import AxisConfigError
    from cf_ui.fastapi import install_cf_ui

    with pytest.raises(AxisConfigError, match="hotpink"):
        install_cf_ui(_Catalog(env), theme="bulma", composition={"accent": "hotpink"})


def test_fastapi_installer_defaults_the_composition_when_omitted(env):
    """Absent config means the default composition — same as the Django tag."""
    from cf_ui.axes import root_attrs
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma")
    assert env.globals["cf_ui_axis_attrs"]() == root_attrs(None)


# --- Criterion 4: custom value sets on the Jinja side ----------------------


def test_installer_accepts_custom_value_sets(env):
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(
        _Catalog(env),
        theme="bulma",
        composition={"accent": "brand"},
        value_sets=CUSTOM_ACCENT,
    )
    out = _render(env, "<html {{ cf_ui_root_attrs() }}>")
    assert 'data-accent="brand"' in out


def test_head_macro_inlines_custom_axis_css_after_install(env):
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma", composition="default", value_sets=CUSTOM_ACCENT)
    out = _render(env, '{{ cf_ui_head(theme="bulma") }}')
    assert '[data-accent="brand"]' in out
    assert "#6d28d9" in out


def test_head_macro_emits_no_custom_css_when_none_supplied(env):
    from cf_ui.fastapi import install_cf_ui

    install_cf_ui(_Catalog(env), theme="bulma", composition="default")
    assert '[data-accent="' not in _render(env, '{{ cf_ui_head(theme="bulma") }}')


def test_installer_honours_replace_mode(env):
    from cf_ui.axes import AxisConfigError
    from cf_ui.fastapi import install_cf_ui

    with pytest.raises(AxisConfigError, match="azure"):
        install_cf_ui(
            _Catalog(env),
            theme="bulma",
            composition={"accent": "azure"},
            value_sets=CUSTOM_ACCENT,
            value_sets_mode="replace",
        )


# --- Litestar installer ----------------------------------------------------


def test_litestar_installer_still_appends_the_template_directory(env):
    from unittest.mock import MagicMock

    from cf_ui import JINJA_TEMPLATES_DIR
    from cf_ui.litestar import install_cf_ui

    config = MagicMock()
    config.directory = []
    install_cf_ui(config, theme="bulma")
    assert JINJA_TEMPLATES_DIR / "bulma" in config.directory


def test_litestar_installer_registers_globals_via_engine_callback(env):
    from unittest.mock import MagicMock

    from cf_ui.litestar import install_cf_ui

    config = MagicMock()
    config.directory = []
    config.engine_callback = None
    install_cf_ui(config, theme="bulma", composition="default")

    config.engine_callback(_LitestarEngine(env))
    assert callable(env.globals["cf_ui_axis_attrs"])


def test_litestar_installer_chains_an_existing_engine_callback(env):
    from unittest.mock import MagicMock

    from cf_ui.litestar import install_cf_ui

    seen = []
    config = MagicMock()
    config.directory = []
    config.engine_callback = seen.append
    install_cf_ui(config, theme="bulma", composition="default")

    engine = _LitestarEngine(env)
    config.engine_callback(engine)
    assert seen == [engine], "the app's own engine_callback must still run"
    assert callable(env.globals["cf_ui_axis_attrs"])
