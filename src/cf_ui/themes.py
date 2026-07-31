"""Theme registry and django-cotton theme dispatch.

The two template sets switch themes differently, for reasons that are not
cosmetic:

* **Jinja2/JinjaX** switches by *directory*. ``install_cf_ui`` registers
  ``templates/jinja/<theme>/`` with the catalog, so ``<CfCard>`` resolves to
  whichever theme was installed. Nothing in this module is needed for that.

* **django-cotton** cannot. ``<c-cf.card>`` resolves through django-cotton's
  single global ``COTTON_DIR`` prefix, and cf-ui deliberately does not touch
  ``COTTON_DIR`` — an earlier release did, and it broke every consumer whose
  own components lived at ``cotton/<their-app>/*.html``
  (see tests/unit/test_consumer_compatibility.py).

  So the public component stays at the fixed, theme-free path
  ``cotton/cf/<name>.html`` and its body is one ``{% include %}`` of a
  per-theme partial at ``cotton/_themes/<theme>/<name>.html``. The consuming
  app keeps writing ``<c-cf.card>``; ``CF_UI_THEME`` moves all 14 components
  at once.
"""

from pathlib import Path

_HERE = Path(__file__).parent

#: Themes with a real component set. The other directories under
#: ``templates/`` hold a ``PLANNED.md`` stub and are not selectable.
THEMES = ("bulma", "daisy", "bootstrap", "foundation", "fomantic")

DEFAULT_THEME = "bulma"

#: django-cotton file stems, as used by ``<c-cf.form-field>``.
#:
#: A name here must have a partial under every theme in :data:`THEMES` —
#: ``cotton_partial`` validates the name, not the file, so an unbacked entry
#: trades a clear ``ThemeError`` for a ``TemplateDoesNotExist`` at first
#: render. ``tests/unit/test_primitives.py`` holds this tuple against the
#: primitives that actually ship.
COMPONENTS = (
    "breadcrumb",
    "button",
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
)

#: Where the per-theme cotton partials live, relative to a template root.
#: Leading underscore marks them private — consumers render ``<c-cf.card>``,
#: never ``<c-_themes.bulma.card>``.
COTTON_THEME_ROOT = "cotton/_themes"

#: The tail of the Tailwind content glob, in Tailwind's own brace syntax.
#: Kept as a constant so docs and code cannot drift apart.
TAILWIND_CONTENT_SUFFIX = "cf_ui/templates/**/*.{html,jinja}"


class ThemeError(ValueError):
    """Raised for an unknown theme or component name."""


def resolve_theme(theme: str | None = None) -> str:
    """Validate a theme name, defaulting to Bulma.

    Fails loudly here rather than as a ``TemplateDoesNotExist`` at first
    render — a stub theme name is a configuration mistake, not a missing file.
    """
    if not theme:
        return DEFAULT_THEME
    if theme not in THEMES:
        available = ", ".join(THEMES)
        raise ThemeError(f"unknown theme {theme!r} — implemented themes are: {available}")
    return theme


def cotton_partial(component: str, theme: str | None = None) -> str:
    """Template path of a component's partial for ``theme``."""
    if component not in COMPONENTS:
        known = ", ".join(COMPONENTS)
        raise ThemeError(f"unknown component {component!r} — known components: {known}")
    return f"{COTTON_THEME_ROOT}/{resolve_theme(theme)}/{component}.html"


def tailwind_content_globs() -> list[str]:
    """Absolute globs a Tailwind build must scan to keep cf-ui's classes.

    DaisyUI compiles through Tailwind, so any class in these templates that
    Tailwind's scanner never sees is removed from the output — silently, with
    no error and an unstyled page as the only symptom. Paths are absolute and
    derived from ``cf_ui.__file__`` so they work from a site-packages install,
    an editable install, or a vendored copy.

    Separators are always forward slashes, including on Windows. These strings
    are pasted into a ``tailwind.config.js`` or an ``@source`` directive, where
    a backslash is a JavaScript escape character and fast-glob (Tailwind's
    matcher) treats it as an escape rather than a separator — a native Windows
    path would match nothing and shake every class out, silently.
    """
    templates = _HERE / "templates"
    return [
        (templates / "**" / "*.html").as_posix(),
        (templates / "**" / "*.jinja").as_posix(),
    ]


if __name__ == "__main__":  # pragma: no cover - developer convenience
    for pattern in tailwind_content_globs():
        print(pattern)
