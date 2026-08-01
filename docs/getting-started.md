# Getting started

[Quickstart](quickstart.md) gets a page rendering. This page explains what you
just wired up, in the order the pieces matter.

## 1. Themes

`CF_UI_THEME` (Django) or `theme=` (FastAPI/Litestar) picks the CSS framework.
Five ship:

| Theme | Value | Notes |
|---|---|---|
| Bulma | `"bulma"` | |
| Tailwind + DaisyUI | `"daisy"` | Needs a Tailwind content glob — see [DaisyUI](daisyui.md) |
| Bootstrap 5 | `"bootstrap"` | CSS only, no `bootstrap.bundle.js` — see [Bootstrap](bootstrap.md) |
| Foundation 6 | `"foundation"` | CSS only, no jQuery |
| Fomantic UI | `"fomantic"` | CSS only, no jQuery |

Switching is one line and needs no template edits, because component names
never mention the theme. An unregistered theme name is **rejected at startup**
— `CfUiConfig` validates it when Django boots, and `install_cf_ui` validates
it when you call it. You find out at boot, not at first render.

### Why the CSS-only stance

Bootstrap, Foundation, and Fomantic all ship JavaScript that owns modal, tab,
and accordion state. `cf_ui_alpine.js` already owns that state. Loading both
gives the modal two owners, and `Alpine.store('cf').modal.open(id)` would then
mean something different under one theme than under the others.

cf-ui uses each framework's classes and markup structure and wires behavior
through Alpine, so the CDN stylesheet is all a consuming app needs — for
Bulma, Bootstrap, Foundation, and Fomantic. **DaisyUI is the exception**: it
is a Tailwind plugin, so its CDN stylesheet is components only, with none of
the utility classes (`flex`, `w-full`, `gap-4`, …) the daisy templates use for
layout. `{% cf_ui_head %}` covers the gap by also emitting Tailwind's Play
CDN script, but that is a browser-side compile step, not a production
substitute for a real Tailwind build — see [DaisyUI](daisyui.md) before you
ship it.
[Bootstrap](bootstrap.md) is the full decision record — which of Bootstrap's
twelve JS components cf-ui replaces, what to do about the eight it does not,
and what changes at Bootstrap 6.

## 2. Components

Fourteen components, same prop names on every theme. The two syntaxes:

```jinja
<Cf:Card header="Title">Body</Cf:Card>
```

```django
<c-cf.card header="Title">Body</c-cf.card>
```

The `Cf` prefix and `cf.` namespace exist to stop collisions with your own
components. See [Components](components.md) for every prop.

!!! note "Cotton components are theme-agnostic on disk too"
    The public wrappers live at `cotton/cf/*.html`, not
    `cotton/<theme>/cf/*.html`, so cf-ui can sit alongside your own
    `templates/cotton/<app>/...` tree without fighting over `COTTON_DIR`. Each
    wrapper declares its props and includes a partial from
    `cotton/_themes/<theme>/` chosen by `CF_UI_THEME`. Render `<c-cf.card>`;
    never reach into `_themes/` yourself.

## 3. Assets

`{% cf_ui_head %}` emits the theme stylesheet. `{% cf_ui_body %}` emits
`cf_ui_alpine.js` and then the Alpine CDN.

That order is load-bearing: both tags use `defer`, so DOM order determines
execution order, and cf-ui's file must register its components before Alpine
initializes them.

!!! warning "DaisyUI is not like the other four themes here"
    For Bulma, Bootstrap, Foundation, and Fomantic, `{% cf_ui_head %}` emits
    one self-contained stylesheet and that is the whole story. DaisyUI
    compiles through Tailwind, so its CDN stylesheet alone has no utility
    classes — `{% cf_ui_head %}` also emits Tailwind's Play CDN script for it,
    controlled by `CF_UI_DAISY_CDN` (`"play"` by default, `"off"` for a real
    Tailwind build). See [DaisyUI](daisyui.md) before choosing which one you
    ship.

CDN versions are pinned defaults, overridable:

```python
# settings.py
CF_UI_CDN_VERSIONS = {
    "bulma": "1.0.2",
    "alpinejs": "3.14.1",
}
```

Opt out of Alpine:

```django
{% cf_ui_body alpine=False %}
```

Opt out of the CDN entirely by not calling the tags and loading assets
yourself. The Jinja2 equivalents are macros:

```jinja
{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_body %}
{{ cf_ui_head(theme="bulma") }}
{{ cf_ui_body(theme="bulma", cf_alpine_url="/static/cf_ui/cf_ui_alpine.js") }}
```

## 4. Composition axes

`CF_UI_THEME` picks the CSS framework. Five orthogonal **axes** decide what the
app looks like *within* it — each keyed on a data attribute carrying a closed
set of named values:

| Axis | Attribute | Shipped values |
|---|---|---|
| Accent | `data-accent` | `slate`, `azure`, `jade` |
| Surface | `data-surface` | `plain`, `muted` |
| Form | `data-form` | `sharp`, `soft`, `round` |
| Density | `data-density` | `compact`, `regular`, `roomy` |
| Type | `data-type` | `system`, `humanist`, `mono` |

One setting emits all five attributes:

```python
# settings.py
CF_UI_COMPOSITION = "editorial"   # or {"accent": "jade", "density": "compact"}
```

```django
<html lang="en" {% cf_ui_root_attrs %}>
```

```python
# FastAPI / Litestar
install_cf_ui(catalog, theme="bulma", composition="editorial")
```

Apps supply their own value sets via `CF_UI_AXIS_VALUES` (`value_sets=` for
Jinja apps) — cf-ui ships the machinery and one neutral default set, not a
brand.

`data-theme` remains the light/dark switch and is **not** an axis. Light and
dark are declared independently, never derived by inversion.

!!! warning "Every accent × surface × mode combination must pass WCAG AA"
    The default value set is held to that in CI. If you supply your own, hold
    it to the same bar — [Theming](theming.md) shows how.

### Build-time validation

Closed value sets are only a promise until something enforces them.
`data-accent="hotpink"` raises no error on its own; it produces an element with
no accent. cf-ui ships a Tailwind plugin that **fails the build** on an unknown
axis value, generates the axis CSS and its `@media (color-gamut: p3)` layer
from the same definition, and can warn with WCAG numbers for every
accent × surface × mode.

```css
@import "tailwindcss";
@plugin "../.venv/lib/python3.12/site-packages/cf_ui/static/cf_ui/cf_ui_tailwind_plugin.mjs";
```

The plugin is vendored in the wheel and deliberately **not** published to npm —
a separate npm version could disagree with the installed package about what a
valid value is, which is the exact failure it exists to prevent. See
[Tailwind plugin](tailwind-plugin.md).

## 5. Interactivity

`cf_ui_alpine.js` registers named Alpine components you can bind from outside:

- `cfModal` — `open`, `show()`, `toggle()`, `close()`, `initModal()`
- `cfNavbar` — `menuOpen`, `toggle()`
- `cfPanel` — `open`, `toggle()`, `initPanel()`
- `cfTabs` — `active`, `setActive(id)`, `initTabs()`, `onKeydown(e)`

Plus a `$cf` global store for cross-component messaging:

```html
<button @click="$store.cf.notify('Saved!', 'success')">Save</button>
<button @click="Alpine.store('cf').modal.open('confirm-dialog')">Delete</button>
```

!!! note "`$store` only exists inside Alpine expressions"
    From ordinary page JavaScript — or a Playwright `page.evaluate()` — use
    `Alpine.store('cf')`. The `$store` shorthand is scoped to Alpine component
    expressions.

This file is also where the interactive components' accessibility lives: modal
focus trapping and restoration, `Escape` to close, the tabs roving tabindex. A
theme partial supplies classes and ARIA state and never implements behavior, so
a new theme inherits all of it for free. See
[Accessibility](accessibility.md).

## 6. Escaping

cf-ui's templates escape their own output, unconditionally. A prop that carries
real markup must be `markupsafe.Markup`; there is no opt-out flag, and template
shadowing is the deliberate override path.

This is short to state and worth understanding before you debug your first
"why is my HTML showing as text" — [Escaping](escaping.md).

## Next

[Use cases](use-cases.md) puts these together: HTMX-driven tables, modal
confirmations, and server-rendered forms with validation errors.
