from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

_CDN_CSS = {
    "bulma": "https://cdn.jsdelivr.net/npm/bulma@{v}/css/bulma.min.css",
    "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@{v}/dist/css/bootstrap.min.css",
    "foundation": "https://cdn.jsdelivr.net/npm/foundation-sites@{v}/dist/css/foundation.min.css",
    "fomantic": "https://cdn.jsdelivr.net/npm/fomantic-ui@{v}/dist/semantic.min.css",
    "daisy": "https://cdn.jsdelivr.net/npm/daisyui@{v}/dist/full.min.css",
}
_ALPINE_CDN = "https://cdn.jsdelivr.net/npm/alpinejs@{v}/dist/cdn.min.js"
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


@register.simple_tag
def cf_ui_head() -> str:
    theme = getattr(settings, "CF_UI_THEME", "bulma")
    v = _versions()
    parts = []

    if theme in _CDN_CSS:
        url = _CDN_CSS[theme].format(v=v.get(theme, ""))
        parts.append(f'<link rel="stylesheet" href="{url}">')

    parts.append("<style>[x-cloak] { display: none !important; }</style>")
    return mark_safe("\n".join(parts))


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
