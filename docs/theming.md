# Theming — composition axes

`CF_UI_THEME` answers *which CSS framework*. The composition axes answer the
orthogonal question: **within that framework, what does this app look like?**

Five independent axes, each keyed on a data attribute:

| Axis | Attribute | Controls | Shipped values |
|---|---|---|---|
| Accent | `data-accent` | Primary color and its content/strong pairs | `slate`, `azure`, `jade` |
| Surface | `data-surface` | Ground, lifted panel, body text | `plain`, `muted` |
| Form | `data-form` | Radius, border strategy, depth | `sharp`, `soft`, `round` |
| Density | `data-density` | Spacing base unit, line height, control height | `compact`, `regular`, `roomy` |
| Type | `data-type` | Display/body/mono stacks, scale ratio | `system`, `humanist`, `mono` |

`data-theme` stays the light/dark mode switch and is **not** an axis — mode and
identity are separate concerns.

Each axis carries a **closed set** of named values. Apps pick one value per
axis; they do not supply raw colors. That constraint is the point:
unconstrained theming variables produce inconsistent, often inaccessible
results, and the closed set is what makes contrast a package-level guarantee
instead of a per-app afterthought.

The shipped set is deliberately neutral. It exists so the package works out of
the box and so there is a reference implementation of a well-formed axis value
— not as a brand. Bring your own (see [Custom value sets](#custom-value-sets)).

---

## Named compositions

One setting resolves to all five axes.

| Composition | accent | surface | form | density | type |
|---|---|---|---|---|---|
| `default` | slate | plain | soft | regular | system |
| `editorial` | jade | muted | sharp | roomy | humanist |
| `console` | azure | plain | sharp | compact | mono |

---

## Django

```python
# settings.py
CF_UI_COMPOSITION = "editorial"  # or a per-axis mapping:
CF_UI_COMPOSITION = {"accent": "jade"}  # unnamed axes fall back to `default`
```

```django
{% load cf_ui %}
<!DOCTYPE html>
<html lang="en" {% cf_ui_root_attrs %}>
<head>{% cf_ui_head %}</head>
```

`{% cf_ui_head %}` links the axis stylesheet alongside the theme CSS.
`{% cf_ui_root_attrs %}` stamps all five attributes — **one setting, five
attributes**, so axis values are never scattered through your templates.

An invalid composition raises `ImproperlyConfigured` at startup, not at first
render.

## FastAPI / JinjaX

```python
from cf_ui.fastapi import install_cf_ui

install_cf_ui(catalog, theme="bulma", composition="editorial")
```

## Litestar

```python
from cf_ui.litestar import install_cf_ui

install_cf_ui(config, theme="bulma", composition="editorial")
```

Both installers register the `cf_ui_axis_attrs` / `cf_ui_axis_style` Jinja
globals that the `assets.jinja` macros delegate to:

```jinja
{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_root_attrs %}
<html lang="en" {{ cf_ui_root_attrs() }}>
<head>{{ cf_ui_head(theme="bulma") }}</head>
```

Litestar's installer *chains* onto any `engine_callback` you already set — it
does not replace it.

---

## Custom value sets

```python
# settings.py  (Django)
CF_UI_AXIS_VALUES = {
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
CF_UI_AXIS_VALUES_MODE = "extend"  # default; "replace" drops the shipped
# values for each axis you supply
CF_UI_COMPOSITION = {"accent": "brand"}
```

FastAPI/Litestar take the same data as `value_sets=` / `value_sets_mode=`.

Custom values are not in the shipped stylesheet, so their CSS is emitted inline
by `{% cf_ui_head %}` (Django) and by the `cf_ui_head()` macro (Jinja).

> **`replace` mode is strict on purpose.** It drops the shipped values for that
> axis, so a composition still naming one — including the `default`
> composition's — raises rather than silently falling back.

---

## The contrast requirement

**Every accent × surface × mode combination must pass WCAG AA before a value
set ships.** This is a hard requirement for the shipped set and the standard
any custom set is expected to meet.

Gated pairs:

| Foreground | Background | Minimum |
|---|---|---|
| `--cf-text` | `--cf-ground` | 4.5 (AA body text) |
| `--cf-text` | `--cf-lifted` | 4.5 |
| `--cf-text-muted` | `--cf-ground` | 4.5 |
| `--cf-accent-content` | `--cf-accent` | 4.5 |
| `--cf-accent-strong` | `--cf-ground` | 4.5 |
| `--cf-accent-strong` | `--cf-lifted` | 4.5 |
| `--cf-accent` | `--cf-ground` | 3.0 (AA non-text UI) |

`--cf-border` is deliberately ungated: in the shipped set it is decorative, not
a meaningful UI boundary. If your value set uses it as one, gate it yourself.

Check your own set before shipping it:

```python
from cf_ui.axes import contrast_failures, merge_value_sets

sets = merge_value_sets(CF_UI_AXIS_VALUES)
for accent in sets["accent"]:
    for surface in sets["surface"]:
        for mode in ("light", "dark"):
            failures = contrast_failures(sets, accent, surface, mode)
            assert not failures, f"{accent}/{surface}/{mode}: {failures}"
```

The shipped set is held to exactly this check in `tests/unit/test_axes.py`.

> The Tailwind plugin (#7) surfaces this at build time as well, via
> `contrastReport: true`. It **warns** rather than failing the build: an unknown
> axis value is always a mistake, but a ratio below AA may be a deliberate
> choice in a value set cf-ui did not ship, and making it fatal would mean this
> package decides when your app may compile. See
> [the plugin docs](tailwind-plugin.md#what-fails-the-build-and-what-only-warns).

### Why `--cf-accent-strong` exists

An accent chosen to work as a control fill often cannot serve as small text on
a light ground. `--cf-accent-strong` is the darkened companion for that case.
It is a property of the accent alone, not of the accent/surface pair — one
value per accent keeps the axes genuinely independent.

---

## Light and dark are declared independently

Every mode-keyed value declares `light` and `dark` in full. Neither is derived
from the other by inversion — **an inverted palette is a second theme nobody
designed.** The generated CSS reflects this:

```css
[data-accent="azure"] { --cf-accent: #0369a1; ... }             /* light */
[data-theme="dark"][data-accent="azure"] { --cf-accent: #38bdf8; ... }
```

Light is the *unqualified* declaration, so `data-theme` is only needed to opt
into dark. A value set missing either mode is rejected.

---

## Wide-gamut color

Base declarations are sRGB hex — that is what the contrast gate is computed
against. Extended chroma is layered on at the end of the stylesheet:

```css
@media (color-gamut: p3) {
  [data-accent="azure"] { --cf-accent: oklch(50.0% 0.137 242.7); }
}
```

The gate is **display gamut**, not `@supports (color: oklch(...))` — every
current browser parses that syntax, so the `@supports` form is a no-op. The p3
variants hold lightness constant and raise only chroma, so the sRGB contrast
guarantee carries over.

Near-neutral accents (`slate`) ship no p3 block; there is no wide-gamut chroma
to recover.

### The lightness invariant is enforced, not assumed

"Holds lightness constant" used to be a convention maintained by hand. It is now
a gate: `p3_lightness_failures()` converts each sRGB base declaration to OKLab
and compares its lightness against the `oklch()` override, and a unit test fails
CI if any override drifts by more than **0.5 percentage points**.

That tolerance is set from the shipped data — the overrides are authored to one
decimal place, which puts them within 0.05pp of their base, so 0.5pp leaves an
order of magnitude of headroom while still catching any drift large enough to
change the contrast result.

```python
from cf_ui.axes import p3_lightness_failures, DEFAULT_VALUE_SETS

p3_lightness_failures(DEFAULT_VALUE_SETS)  # [] — shippable
```

The same check runs in the Tailwind plugin as `p3LightnessFailures()`, with
byte-identical messages; a parity test compares the two. Because the sRGB
contrast gate cannot measure `oklch()` directly, this invariant is what carries
the WCAG result over to wide-gamut displays — without it, a p3 override could
ship below AA with every test green, invisible to anyone reviewing on an sRGB
display.

---

## Tailwind interop

Where tokens have a Tailwind v4 equivalent, the generated CSS emits an alias so
a Tailwind-based theme picks the axes up without per-component work:

| cf-ui token | Tailwind v4 |
|---|---|
| `--cf-accent` | `--color-primary` |
| `--cf-accent-content` | `--color-primary-content` |
| `--cf-accent-strong` | `--color-primary-strong` |

The aliases are inert when no Tailwind is present.

### `--spacing` is not aliased

`--cf-spacing` is emitted, but it is **not** wired to Tailwind's `--spacing`.

`--color-primary` is a name cf-ui effectively owns in a Tailwind context.
`--spacing` is the root of Tailwind v4's *entire* spacing scale — `p-4`, `gap-2`,
`m-8` and every other spacing utility derive from it. Aliasing it meant
`data-density="compact"` silently rescaled the whole consuming app by ±20%,
scoped to an attribute the app set for cf-ui's benefit. A Bulma consumer who
also ran Tailwind got that as pure collateral damage.

Apps that *want* density to drive the Tailwind scale opt in with one line:

```css
@theme {
  --spacing: var(--cf-spacing);
}
```

> **Changed in 0.2.0.** This alias used to be emitted for every theme. If you
> were relying on it, add the rule above.

---

## Regenerating the stylesheet

`src/cf_ui/static/cf_ui/cf_ui_axes.css` is **generated** from
`src/cf_ui/axes.py`, which is the single source of truth:

```bash
python -m cf_ui.axes
```

A unit test fails if the checked-in file drifts from the generator's output.
