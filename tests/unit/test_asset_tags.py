import re
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui" / "templates"


def test_cf_ui_head_returns_bulma_cdn_link(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_head

    result = cf_ui_head()
    assert "bulma" in result
    assert '<link rel="stylesheet"' in result
    assert "cdn.jsdelivr.net" in result


def test_cf_ui_head_includes_xcloak_style(settings):
    settings.CF_UI_THEME = "bulma"
    from cf_ui.templatetags.cf_ui import cf_ui_head

    result = cf_ui_head()
    assert "[x-cloak]" in result
    assert "display: none" in result


def test_cf_ui_head_respects_version_override(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {"bulma": "0.9.4"}
    from cf_ui.templatetags.cf_ui import cf_ui_head

    result = cf_ui_head()
    assert "0.9.4" in result


def test_cf_ui_body_includes_alpine_scripts(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body

    result = cf_ui_body()
    assert "alpinejs" in result
    assert "cf_ui_alpine.js" in result
    assert "defer" in result


def test_cf_ui_body_alpine_false_omits_scripts(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body

    result = cf_ui_body(alpine=False)
    assert result == ""


def test_cf_ui_body_cf_alpine_loads_before_alpine(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body

    result = cf_ui_body()
    cf_pos = result.find("cf_ui_alpine.js")
    alpine_pos = result.find("alpinejs")
    assert cf_pos < alpine_pos, "cf_ui_alpine.js must appear before Alpine CDN"


# --- The two asset surfaces must not drift (#22) ---------------------------
#
# `_CDN_CSS` serves Django and the `assets.jinja` macro serves Jinja2 apps, and
# they hold the same URLs in two places. A theme wired into one and not the
# other renders unstyled on half the supported frameworks, with no error — so
# the agreement is executed here rather than eyeballed when a theme lands.


def _assets_head(theme: str) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "jinja"]),
    )
    module = env.get_template("cf_ui/assets.jinja").make_module()
    return str(module.cf_ui_head(theme=theme))


@pytest.mark.parametrize("theme", ["bulma", "daisy", "bootstrap", "foundation", "fomantic"])
def test_the_jinja_macro_and_the_django_tag_serve_the_same_css_url(settings, theme):
    from cf_ui.templatetags.cf_ui import _DEFAULTS, cf_ui_head

    settings.CF_UI_THEME = theme
    settings.CF_UI_CDN_VERSIONS = {}

    def _href(html: str) -> str:
        found = re.findall(r'<link rel="stylesheet" href="(https://[^"]+)"', html)
        assert found, f"no CDN stylesheet for {theme}"
        return found[0]

    assert _href(cf_ui_head()) == _href(_assets_head(theme))
    assert _DEFAULTS[theme] in _href(_assets_head(theme))


def test_every_implemented_theme_has_a_cdn_entry(settings):
    """A theme selectable at startup but unstyled at render is worse than one
    rejected at startup."""
    from cf_ui.templatetags.cf_ui import _CDN_CSS, _DEFAULTS
    from cf_ui.themes import THEMES

    for theme in THEMES:
        assert theme in _CDN_CSS, f"{theme} is in THEMES but has no CDN entry"
        assert theme in _DEFAULTS, f"{theme} is in THEMES but has no pinned version"


def test_bootstrap_head_links_the_stylesheet_and_no_bundle(settings):
    """cf-ui drives Bootstrap's components with Alpine — see issue #22."""
    from cf_ui.templatetags.cf_ui import cf_ui_body, cf_ui_head

    settings.CF_UI_THEME = "bootstrap"
    settings.CF_UI_CDN_VERSIONS = {}

    head = cf_ui_head()
    assert "bootstrap@5.3.3/dist/css/bootstrap.min.css" in head
    assert "bootstrap.bundle" not in head
    assert "bootstrap.bundle" not in cf_ui_body()
    assert "bootstrap.bundle" not in _assets_head("bootstrap")
