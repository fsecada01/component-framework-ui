"""Theme dispatch for the django-cotton template set (issue #6).

The Jinja side already switches themes by directory — ``install_cf_ui``
registers ``templates/jinja/<theme>/`` with JinjaX. Cotton has no equivalent:
``<c-cf.card>`` resolves through django-cotton's single global ``COTTON_DIR``
to exactly one file, and cf-ui deliberately does not touch ``COTTON_DIR``
(see tests/unit/test_consumer_compatibility.py).

So the public component at ``cotton/cf/<name>.html`` stays a stable, theme-free
entry point and dispatches to a per-theme partial at
``cotton/_themes/<theme>/<name>.html``. One setting — ``CF_UI_THEME`` — moves
all 14 components at once, with no template edits in the consuming app.
"""

from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui" / "templates"
COTTON_DIR = TEMPLATES_DIR / "cotton"

# Cotton file stems (hyphenated), as used by <c-cf.form-field>.
COMPONENT_STEMS = [
    "breadcrumb",
    "card",
    "checkbox-group",
    "form-field",
    "modal",
    "navbar",
    "notification",
    "pagination",
    "panel",
    "progress",
    "select",
    "table",
    "tabs",
    "textarea",
]

IMPLEMENTED_THEMES = ["bulma", "daisy", "bootstrap", "foundation"]


# --- The theme registry ----------------------------------------------------


def test_themes_module_lists_the_implemented_themes():
    from cf_ui.themes import THEMES

    assert sorted(THEMES) == sorted(IMPLEMENTED_THEMES)


def test_components_tuple_matches_the_shipped_cotton_files():
    """Drift guard: the registry and the filesystem must not disagree."""
    from cf_ui.themes import COMPONENTS

    assert sorted(COMPONENTS) == sorted(COMPONENT_STEMS)


def test_resolve_theme_defaults_to_bulma():
    from cf_ui.themes import resolve_theme

    assert resolve_theme(None) == "bulma"


def test_resolve_theme_accepts_an_implemented_theme():
    from cf_ui.themes import resolve_theme

    assert resolve_theme("daisy") == "daisy"


def test_resolve_theme_accepts_bootstrap():
    from cf_ui.themes import resolve_theme

    assert resolve_theme("bootstrap") == "bootstrap"


def test_resolve_theme_accepts_foundation():
    from cf_ui.themes import resolve_theme

    assert resolve_theme("foundation") == "foundation"


def test_resolve_theme_rejects_a_stub_theme_by_name():
    """fomantic is still a PLANNED.md stub, not a usable theme."""
    from cf_ui.themes import ThemeError, resolve_theme

    with pytest.raises(ThemeError, match="fomantic"):
        resolve_theme("fomantic")


def test_resolve_theme_error_names_the_available_themes():
    from cf_ui.themes import ThemeError, resolve_theme

    with pytest.raises(ThemeError) as exc:
        resolve_theme("tailwind")
    assert "daisy" in str(exc.value)


def test_cotton_partial_builds_the_theme_scoped_path():
    from cf_ui.themes import cotton_partial

    assert cotton_partial("modal", "daisy") == "cotton/_themes/daisy/modal.html"


def test_cotton_partial_rejects_an_unknown_component():
    """Guards against a typo in a wrapper silently resolving to nothing."""
    from cf_ui.themes import ThemeError, cotton_partial

    with pytest.raises(ThemeError, match="dropdown"):
        cotton_partial("dropdown", "bulma")


# --- The partials exist on disk -------------------------------------------


@pytest.mark.parametrize("theme", IMPLEMENTED_THEMES)
@pytest.mark.parametrize("stem", COMPONENT_STEMS)
def test_every_theme_ships_every_cotton_partial(theme, stem):
    assert (COTTON_DIR / "_themes" / theme / f"{stem}.html").is_file()


@pytest.mark.parametrize("stem", COMPONENT_STEMS)
def test_public_cotton_component_holds_no_theme_markup(stem):
    """The wrapper declares props and dispatches — nothing else.

    If Bulma class names leak back into cotton/cf/*.html, switching themes
    stops being a config change, which is exactly what this phase promises.
    """
    source = (COTTON_DIR / "cf" / f"{stem}.html").read_text(encoding="utf-8")
    assert "{% include" in source
    for bulma_marker in ('class="field', 'class="card', "is-danger", 'class="navbar'):
        assert bulma_marker not in source


@pytest.mark.parametrize("stem", COMPONENT_STEMS)
def test_theme_partials_declare_no_cotton_vars(stem):
    """<c-vars> belongs on the public wrapper only — it is the prop contract.

    Duplicating it in each partial would mean 28 places to keep in sync.
    """
    for theme in IMPLEMENTED_THEMES:
        source = (COTTON_DIR / "_themes" / theme / f"{stem}.html").read_text(encoding="utf-8")
        assert "<c-vars" not in source


# --- The template tag ------------------------------------------------------


def test_theme_path_tag_follows_the_configured_theme(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_theme_path

    settings.CF_UI_THEME = "daisy"
    assert cf_ui_theme_path("card") == "cotton/_themes/daisy/card.html"


def test_theme_path_tag_defaults_to_bulma(settings):
    from cf_ui.templatetags.cf_ui import cf_ui_theme_path

    settings.CF_UI_THEME = "bulma"
    assert cf_ui_theme_path("card") == "cotton/_themes/bulma/card.html"


def test_theme_path_tag_supports_the_as_syntax(settings):
    """The wrappers use `{% cf_ui_theme_path "x" as cf_ui_partial %}`."""
    from django.template import Context, Template

    settings.CF_UI_THEME = "daisy"
    rendered = Template('{% load cf_ui %}{% cf_ui_theme_path "modal" as p %}{{ p }}').render(
        Context({})
    )
    assert rendered == "cotton/_themes/daisy/modal.html"


# --- Startup validation ----------------------------------------------------


def test_appconfig_rejects_an_unimplemented_theme(settings):
    from django.apps import apps
    from django.core.exceptions import ImproperlyConfigured

    settings.CF_UI_THEME = "fomantic"
    with pytest.raises(ImproperlyConfigured, match="fomantic"):
        apps.get_app_config("cf_ui").ready()


@pytest.mark.parametrize("theme", IMPLEMENTED_THEMES)
def test_appconfig_accepts_every_implemented_theme(settings, theme):
    from django.apps import apps

    settings.CF_UI_THEME = theme
    apps.get_app_config("cf_ui").ready()


# --- End-to-end through the Django template engine ------------------------


@pytest.mark.parametrize("stem", COMPONENT_STEMS)
def test_switching_the_setting_switches_the_rendered_markup(settings, stem):
    """The whole point of the phase: one setting, no consumer template edits."""
    from django.template.loader import render_to_string

    props = {
        "name": "field",
        "label": "Label",
        "title": "Title",
        "message": "Message",
        "items": [{"url": "/a", "label": "A"}],
        "columns": [{"key": "k", "label": "K"}],
        "rows": [{"k": "v"}],
        "choices": [{"value": "c", "label": "C"}],
        "options": [{"value": "o", "label": "O"}],
        "tabs": [{"id": "one", "url": "/one"}],
        # `render_to_string` bypasses the cotton compiler, so <c-vars>
        # defaults never apply. Restating this one matters: Bootstrap and
        # DaisyUI both spell a plain info alert `alert alert-info`, and the
        # themes only diverge once the dismiss control is rendered.
        "dismissible": "true",
    }

    rendered = {}
    for theme in IMPLEMENTED_THEMES:
        settings.CF_UI_THEME = theme
        html = render_to_string(f"cotton/cf/{stem}.html", props)
        assert html.strip(), f"{theme} render produced nothing"
        rendered[theme] = html

    assert len(set(rendered.values())) == len(IMPLEMENTED_THEMES), (
        f"{stem} rendered identically under two themes: {sorted(rendered)}"
    )


def test_dispatch_passes_the_slot_through_to_the_partial(settings):
    from django.template.loader import render_to_string

    settings.CF_UI_THEME = "daisy"
    out = render_to_string("cotton/cf/card.html", {"slot": "SLOT-MARKER"})
    assert "SLOT-MARKER" in out
