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


def _assets_head(theme: str, daisy_cdn: str = "play") -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "jinja"]),
    )
    module = env.get_template("cf_ui/assets.jinja").make_module()
    return str(module.cf_ui_head(theme=theme, daisy_cdn=daisy_cdn))


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


# --- daisyUI CDN utilities (#56) --------------------------------------------
#
# daisyUI is a Tailwind *plugin*: its CDN bundle is the component layer only
# (`.btn{`, `.card{`), never the utility layer (`.flex{`, `.w-full{`,
# `.gap-4{`) the shipped daisy templates lean on for layout. daisyUI's own CDN
# docs (https://v4.daisyui.com/docs/cdn/) pair the stylesheet with Tailwind's
# Play CDN script for exactly that reason — cf-ui shipped the first tag and
# silently dropped the second. `CF_UI_DAISY_CDN` ("play"/"off") controls it;
# "play" (the default) completes the documented pair, "off" is for a consumer
# with a real Tailwind build supplying both layers itself.

_SCRIPT_TAG_RE = re.compile(r"<script[^>]*>")
_TAILWIND_PLAY_SCRIPT = '<script src="https://cdn.tailwindcss.com"></script>'


def test_daisy_head_in_play_mode_emits_the_tailwind_play_cdn_script(settings):
    """daisyUI's own CDN recipe is a two-tag pair; "play" ships both."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = "play"
    settings.CF_UI_CDN_VERSIONS = {}

    result = cf_ui_head()
    assert _TAILWIND_PLAY_SCRIPT in result


@pytest.mark.parametrize("theme", ["bulma", "bootstrap", "foundation", "fomantic"])
def test_non_daisy_themes_emit_no_script_tag_from_cf_ui_head(settings, theme):
    """The Play CDN script is a daisy-only concern — the other four themes
    ship self-contained CSS and must render byte-identically to today."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = theme
    settings.CF_UI_CDN_VERSIONS = {}

    assert not _SCRIPT_TAG_RE.search(cf_ui_head())
    assert not _SCRIPT_TAG_RE.search(_assets_head(theme))


def test_daisy_head_in_off_mode_emits_neither_stylesheet_nor_script(settings):
    """ "off" is for a consumer with a real Tailwind build — cf-ui must not
    hand it a stylesheet or script it did not ask for."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = "off"
    settings.CF_UI_CDN_VERSIONS = {}

    result = cf_ui_head()
    assert "daisyui@" not in result
    assert "full.min.css" not in result
    assert _TAILWIND_PLAY_SCRIPT not in result
    assert not _SCRIPT_TAG_RE.search(result)


def test_daisy_head_in_off_mode_still_emits_axes_css_and_xcloak_style(settings):
    """Turning the CDN off must not turn off cf-ui's own assets."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = "off"
    settings.CF_UI_CDN_VERSIONS = {}

    result = cf_ui_head()
    assert "cf_ui_axes.css" in result
    assert "[x-cloak]" in result
    assert "display: none" in result


def test_daisy_play_mode_carries_the_explanatory_comment(settings):
    """The comment is the unmissable signal that this is a dev-only CDN."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = "play"
    settings.CF_UI_CDN_VERSIONS = {}

    result = cf_ui_head()
    assert "<!--" in result
    assert "Play CDN" in result
    assert "development" in result
    assert "CF_UI_DAISY_CDN" in result


@pytest.mark.parametrize("daisy_cdn", ["play", "off"])
def test_the_jinja_macro_and_the_django_tag_agree_on_the_daisy_script_tag(settings, daisy_cdn):
    """Mirrors the href-parity test above, but for the script half of the
    daisy pair — the two surfaces are independent implementations and #22
    already proved they can drift."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = daisy_cdn
    settings.CF_UI_CDN_VERSIONS = {}

    def _scripts(html: str) -> list[str]:
        return _SCRIPT_TAG_RE.findall(html)

    django_scripts = _scripts(cf_ui_head())
    jinja_scripts = _scripts(_assets_head("daisy", daisy_cdn=daisy_cdn))
    assert django_scripts == jinja_scripts


def test_invalid_cf_ui_daisy_cdn_raises_at_startup_naming_the_valid_values(settings):
    """A bad `CF_UI_DAISY_CDN` must fail at boot, not at render — the same
    treatment `CF_UI_THEME` and `CF_UI_COMPOSITION` already get."""
    from django.apps import apps
    from django.core.exceptions import ImproperlyConfigured

    settings.CF_UI_DAISY_CDN = "cdn-please"
    with pytest.raises(ImproperlyConfigured, match="play") as excinfo:
        apps.get_app_config("cf_ui").ready()
    assert "off" in str(excinfo.value)
    assert "cdn-please" in str(excinfo.value)


def test_regression_daisy_stylesheet_alone_is_not_a_complete_head_issue_56(settings):
    """Tripwire for the exact bug in #56: a future refactor that quietly
    drops the script while keeping the stylesheet must fail this test, not
    ship a silently half-styled page."""
    from cf_ui.templatetags.cf_ui import cf_ui_head

    settings.CF_UI_THEME = "daisy"
    settings.CF_UI_DAISY_CDN = "play"
    settings.CF_UI_CDN_VERSIONS = {}

    result = cf_ui_head()
    has_stylesheet = "daisyui@" in result and "full.min.css" in result
    has_script = _TAILWIND_PLAY_SCRIPT in result
    assert has_stylesheet, "the daisyUI stylesheet is expected in play mode"
    assert has_script, (
        "the daisyUI stylesheet alone is not sufficient (#56) — "
        "the Tailwind Play CDN script must ship alongside it"
    )
