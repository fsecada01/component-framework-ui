# DaisyUI theme

DaisyUI is the one theme in cf-ui that is not just "a different class
vocabulary." It sits on Tailwind, so the consuming app compiles its own CSS
instead of linking a finished stylesheet. That changes two things — what
Tailwind has to scan, and what Tailwind's preflight does to whatever styling
you already had.

## Switching to it

```python
# settings.py  (Django)
CF_UI_THEME = "daisy"
```

```python
# FastAPI
from cf_ui.fastapi import install_cf_ui
install_cf_ui(catalog, theme="daisy")

# Litestar
from cf_ui.litestar import install_cf_ui
install_cf_ui(template_config, theme="daisy")
```

That is the whole change. Component names do not move: `<c-cf.card>` and
`<CfCard>` mean the same thing under every theme, and no template in the
consuming app needs an edit. An unimplemented theme name is rejected at
startup (`ImproperlyConfigured` on Django, `ThemeError` elsewhere) rather than
surfacing later as a confusing `TemplateDoesNotExist`.

### How the switch works

The two template sets dispatch differently, and the asymmetry is deliberate.

**Jinja2/JinjaX** switches by directory — `install_cf_ui` registers
`templates/jinja/<theme>/` with the catalog, so `<CfCard>` resolves to
whichever theme was installed.

**django-cotton** cannot do that. `<c-cf.card>` resolves through
django-cotton's single global `COTTON_DIR` prefix, and cf-ui deliberately
does not touch `COTTON_DIR` — an earlier release did, and it broke every
consumer whose own components lived at `cotton/<their-app>/*.html`. So the
public component stays at the fixed path `cotton/cf/<name>.html` and its
entire body is a dispatch:

```django
<c-vars header="" footer="" class="" />
{% load cf_ui %}{% cf_ui_theme_path "card" as cf_ui_partial %}{% include cf_ui_partial %}
```

The theme markup lives in `cotton/_themes/<theme>/<name>.html`. `{% include %}`
inherits the caller's context, so props and `{{ slot }}` reach the partial
without being redeclared — `<c-vars>` stays in exactly one place per
component. The leading underscore marks the directory private: render
`<c-cf.card>`, never `<c-_themes.daisy.card>`.

> **Requires** `"libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"}` in
> `TEMPLATES[0]["OPTIONS"]`. This was already required for `{% cf_ui_head %}`;
> under the dispatch it is also required for components to render at all,
> because each wrapper does `{% load cf_ui %}`. The `cf_ui.django` app label
> prevents templatetag autodiscovery, so there is no way around declaring it.

## Tailwind content glob — read this one

Tailwind removes every class it does not find while scanning your source. Your
own templates are covered by your existing config; **cf-ui's templates live in
site-packages and are not**. Miss them and the page renders with correct markup
and no styling at all — no error, no warning.

Add cf-ui's installed template directory to the content sources:

```js
// tailwind.config.js  (Tailwind v3)
module.exports = {
  content: [
    "./templates/**/*.html",
    "../.venv/lib/python3.12/site-packages/cf_ui/templates/**/*.{html,jinja}",
  ],
};
```

```css
/* app.css  (Tailwind v4) */
@import "tailwindcss";
@plugin "daisyui";
@source "../.venv/lib/python3.12/site-packages/cf_ui/templates/**/*.{html,jinja}";
```

The path depends on your interpreter and platform, so do not hand-write it.
Ask the package:

```bash
python -m cf_ui.themes
```

```python
from cf_ui.themes import tailwind_content_globs
tailwind_content_globs()
# ['.../site-packages/cf_ui/templates/**/*.html',
#  '.../site-packages/cf_ui/templates/**/*.jinja']
```

`tests/unit/test_tailwind_content.py` fails if those globs stop reaching every
shipped template, and this document is checked against the same constant, so
the two cannot drift apart.

### The second way classes get shaken out

Tailwind's scanner reads source text; it does not render templates. A class
assembled at render time is therefore invisible to it:

```django
{# Never do this — Tailwind never sees "alert-error" #}
<div class="alert alert-{{ type }}">
```

Every variant class in the DaisyUI templates is written out in full instead:

```django
<div class="alert {% if type == 'danger' %}alert-error{% elif type == 'success' %}alert-success{% else %}alert-info{% endif %}">
```

This is also why the prop vocabulary did not change between themes. `type="danger"`
still works; DaisyUI has no `alert-danger`, so the templates map it onto
`alert-error` internally. A test scans every DaisyUI template for class tokens
split across a template construct and fails on any it finds.

## Coexistence with an existing framework

Tailwind's preflight resets margins, font sizes, list styles, and form control
appearance globally. Dropping it into an app that Bulma (or Bootstrap) still
styles will visibly damage the pages you have not migrated yet.

While both frameworks are live, disable preflight:

```js
// tailwind.config.js (v3)
module.exports = { corePlugins: { preflight: false } };
```

```css
/* app.css (v4) — import the layers you want, omit the reset */
@layer theme, components, utilities;
@import "tailwindcss/theme.css" layer(theme);
@import "tailwindcss/utilities.css" layer(utilities);
@plugin "daisyui";
```

DaisyUI's own component classes do not depend on preflight, so cf-ui's
components render correctly without it. Re-enable it once the previous
framework's stylesheet is gone.

## What stays the same

The Alpine behaviors are theme-independent and unchanged: `cfModal`,
`cfNavbar`, `cfPanel`, `cfTabs`, and the `$cf` store all work identically
under DaisyUI. Only the classes the bindings toggle differ — Bulma's
`is-active` becomes DaisyUI's `modal-open` on the modal, and `tab-active` on
the tabs. Page code that calls `Alpine.store('cf').modal.open('id')` needs no
change.

The [theme composition axes](theming.md) are also unaffected. They are keyed
on `data-*` attributes and CSS custom properties, independent of which CSS
framework is loaded.
