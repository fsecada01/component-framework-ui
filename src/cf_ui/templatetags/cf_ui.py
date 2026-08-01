from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from cf_ui.axes import root_attrs, style_element
from cf_ui.django import axis_value_sets
from cf_ui.primitives import validate as validate_primitive
from cf_ui.themes import cotton_partial, resolve_daisy_cdn

register = template.Library()

_CDN_CSS = {
    "bulma": "https://cdn.jsdelivr.net/npm/bulma@{v}/css/bulma.min.css",
    "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@{v}/dist/css/bootstrap.min.css",
    "foundation": "https://cdn.jsdelivr.net/npm/foundation-sites@{v}/dist/css/foundation.min.css",
    "fomantic": "https://cdn.jsdelivr.net/npm/fomantic-ui@{v}/dist/semantic.min.css",
    "daisy": "https://cdn.jsdelivr.net/npm/daisyui@{v}/dist/full.min.css",
}
_ALPINE_CDN = "https://cdn.jsdelivr.net/npm/alpinejs@{v}/dist/cdn.min.js"

# daisyUI's own CDN recipe (https://v4.daisyui.com/docs/cdn/) is this
# stylesheet paired with Tailwind's Play CDN script, in this order — daisyUI
# is a Tailwind plugin, so the stylesheet alone has no utility layer (#56).
_TAILWIND_PLAY_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
_DAISY_PLAY_COMMENT = (
    '<!-- cf-ui: daisyUI CDN mode ("play"). Loads Tailwind\'s Play CDN, which\n'
    '     compiles utilities in the browser; upstream labels it "for development\n'
    '     purposes only, and not intended for production"\n'
    "     (https://v4.daisyui.com/docs/cdn/). For production, run a real\n"
    '     Tailwind build and set CF_UI_DAISY_CDN = "off". -->'
)
_DEFAULTS = {
    "bulma": "1.0.2",
    "bootstrap": "5.3.3",
    "foundation": "6.7.5",
    "fomantic": "2.9.3",
    "daisy": "4.7.2",
    "alpinejs": "3.14.1",
}


def _versions() -> dict:
    overrides = getattr(settings, "CF_UI_CDN_VERSIONS", {})
    return {**_DEFAULTS, **overrides}


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def make_list_1_to_n(n):
    try:
        return list(range(1, int(n) + 1))
    except (ValueError, TypeError):
        return []


@register.simple_tag
def cf_ui_head() -> str:
    theme = getattr(settings, "CF_UI_THEME", "bulma")
    v = _versions()
    parts = []

    if theme == "daisy":
        daisy_cdn = resolve_daisy_cdn(getattr(settings, "CF_UI_DAISY_CDN", None))
        if daisy_cdn == "play":
            url = _CDN_CSS["daisy"].format(v=v.get("daisy", ""))
            parts.append(_DAISY_PLAY_COMMENT)
            parts.append(f'<link rel="stylesheet" href="{url}">')
            parts.append(_TAILWIND_PLAY_CDN)
        # "off": a real Tailwind build supplies both the stylesheet and the
        # utility layer, so cf-ui emits neither tag.
    elif theme in _CDN_CSS:
        url = _CDN_CSS[theme].format(v=v.get(theme, ""))
        parts.append(f'<link rel="stylesheet" href="{url}">')

    parts.append(f'<link rel="stylesheet" href="{static("cf_ui/cf_ui_axes.css")}">')
    parts.append("<style>[x-cloak] { display: none !important; }</style>")

    # Value sets the app supplied itself are not in the static asset.
    custom = style_element(axis_value_sets())
    if custom:
        parts.append(custom)

    return mark_safe("\n".join(parts))


@register.simple_tag
def cf_ui_root_attrs() -> str:
    """Stamp all five axis attributes on the root element.

    One setting in (``CF_UI_COMPOSITION``), five attributes out::

        <html lang="en" {% cf_ui_root_attrs %}>
    """
    composition = getattr(settings, "CF_UI_COMPOSITION", None)
    return mark_safe(root_attrs(composition, value_sets=axis_value_sets()))


@register.simple_tag
def cf_ui_theme_path(component: str) -> str:
    """Resolve a component to its partial for the configured theme.

    Used by the public wrappers at ``cotton/cf/<name>.html``::

        {% cf_ui_theme_path "card" as cf_ui_partial %}{% include cf_ui_partial %}

    (Django rejects template variables that begin with an underscore, so the
    name is prefixed rather than marked private.)

    ``{% include %}`` inherits the caller's context, so the component's own
    props and ``{{ slot }}`` reach the partial without being re-declared.
    """
    return cotton_partial(component, getattr(settings, "CF_UI_THEME", None))


@register.simple_tag
def cf_ui_validate(component: str, **axes) -> str:
    """Reject an out-of-vocabulary primitive prop, loudly.

    Used by the primitive wrappers at ``cotton/cf/<name>.html``::

        {% cf_ui_validate "button" variant=variant size=size state=state %}

    The theme partials spell every class literally — they have to, or
    Tailwind's scanner never sees them — which means an unrecognised value
    matches no branch and renders an unstyled element. This turns that silence
    into a ``PrimitiveConfigError`` naming the value and the ones that would
    have worked.

    Returns the empty string; it is called for its exception.
    """
    return validate_primitive(component, **axes)


@register.simple_tag
def cf_ui_body(alpine: bool = True) -> str:
    if not alpine:
        return mark_safe("")

    v = _versions()
    cf_alpine_url = static("cf_ui/cf_ui_alpine.js")
    alpine_url = _ALPINE_CDN.format(v=v["alpinejs"])

    # cf_ui_alpine.js MUST load before Alpine so alpine:init listener registers first
    parts = [
        f'<script src="{cf_alpine_url}" defer></script>',
        f'<script src="{alpine_url}" defer></script>',
    ]
    return mark_safe("\n".join(parts))
