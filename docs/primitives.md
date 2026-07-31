# Primitives

The 14 components cf-ui shipped through 0.2.0 are all **structural** — card,
modal, navbar, table. Primitives are the layer underneath: the small,
high-frequency elements that structural components are built out of and that
consuming apps otherwise hand-write everywhere.

They differ from structural components in one way that shapes everything
below: a primitive is used hundreds of times per app, so its prop contract has
to be settled once, for the whole set, before any of it is implemented. A
button that spells its colours `variant` while a badge spells them `type` is a
worse API than either choice on its own.

## The shared vocabularies

Four axes, each a **closed set**, declared in
[`cf_ui/primitives.py`](https://github.com/fsecada01/component-framework-ui/blob/master/src/cf_ui/primitives.py).
An unknown value raises `PrimitiveConfigError` naming the values that would
have worked — it does not fall through to an unstyled element.

| Axis | Values |
|---|---|
| `variant` | `primary` `secondary` `success` `warning` `danger` `info` `neutral` |
| `size` | `small` `normal` `large` |
| `state` | `normal` `loading` `disabled` |
| `level` | `1`–`6` |

Seven variants, not "whatever the framework ships". All five frameworks can
express all seven, though two collapse a pair onto one class — Foundation has
no informational button colour, so `info` renders as `secondary` rather than
cf-ui inventing a class Foundation's own CSS does not define. A vocabulary cut
down to the poorest framework would make the richer ones useless; one built for
the richest would make `info` mean nothing in Foundation.

`normal` is always the framework's default and always maps to *no class*. That
is a real entry in the map, not a gap — the completeness test treats a missing
key as the failure, so the two cannot be confused.

## Which primitive takes which axis

| Primitive | `variant` | `size` | `state` | `level` | Status |
|---|:-:|:-:|:-:|:-:|---|
| `button` | ● | ● | ● | | **Shipped** |
| `badge` | ● | ● | | | Contract settled |
| `heading` | | ● | | ● | Contract settled |
| `label` | | ● | | | Contract settled |
| `icon` | | ● | | | Contract settled |

`label` and `icon` take no `variant` on purpose. A label's colour belongs to
the field it labels and an icon's to whatever contains it; giving either its
own would create two sources of truth for one colour.

`heading` separates `level` from `size` because they answer different
questions — `level` is the document outline (`<h1>`…`<h6>`, which screen
readers navigate by) and `size` is how big it looks. Coupling them forces a
choice between a correct outline and a correct visual hierarchy.

## How they compose

Primitives nest through the **slot**, never through props:

=== "JinjaX"

    ```jinja
    <Cf:Button variant="primary" size="small">
      <i class="fas fa-plus"></i>
      Add item
    </Cf:Button>
    ```

=== "django-cotton"

    ```html
    <c-cf.button variant="primary" size="small">
      <i class="fas fa-plus"></i>
      Add item
    </c-cf.button>
    ```

There is deliberately no `icon="fa-plus"` prop on `Cf:Button`. An icon prop
would have to accept either a class name or raw markup: the first ties cf-ui to
one icon vendor, and the second is an unescaped-markup prop on the single most
frequently used component in the package. The slot has neither problem.

Once the `icon` primitive lands it occupies that same slot position, adding
sizing and alignment around the glyph — it does not change how the two nest.
That is the whole reason the contract is settled for the set before any of it
is built.

## `Cf:Button` / `<c-cf.button>`

| Prop | Default | Notes |
|---|---|---|
| `variant` | `"neutral"` | See the vocabulary above |
| `size` | `"normal"` | |
| `state` | `"normal"` | `loading` renders the framework's spinner; `disabled` is described below |
| `href` | `""` | Non-empty renders an `<a>`; empty renders a `<button>` |
| `type` | `"button"` | Only applies to the `<button>` form |
| `full_width` | `false` | |
| `extra_class` / `class` | `""` | `extra_class` in JinjaX, `class` in cotton — `class` is a Python reserved word |
| slot | — | The label |

### Disabled links

`state="disabled"` with an `href` renders an `<a>` **without an `href`
attribute**, carrying `role="link"` and `aria-disabled="true"`.

An `<a>` cannot be disabled. Leaving the `href` on and styling it grey
produces a control that is still focusable, still activatable by Enter, and
still followed on middle-click — disabled to sighted mouse users only.
Dropping the attribute is what actually removes it from the tab order, and
`aria-disabled` is what tells assistive technology why.

If you need a disabled control that is genuinely inert, prefer omitting `href`
so it renders a real `<button disabled>`.

## Escaping

The contract in [Escaping](escaping.md) applies unchanged: every cf-ui Jinja
template wraps its body in `{% autoescape true %}`, so a hostile prop is
escaped whatever the surrounding environment does, and a prop carrying real
markup must be `markupsafe.Markup`.

Primitives take **no markup props at all**. Everything that can carry markup
arrives through the slot, where it is the caller's own template output and
governed by the caller's own escaping policy:

| Surface | Escaped by cf-ui | Notes |
|---|---|---|
| `variant`, `size`, `state`, `level` | n/a | Validated against a closed set before they reach the template |
| `href`, `type`, `extra_class` | Yes | Ordinary attribute values |
| slot content | Caller's policy | Where an icon's `<svg>` or `<i>` goes |

`icon` is the one primitive whose slot is *expected* to hold markup, and it is
still the slot rather than a prop — so passing a `Markup` value is a visible,
per-call decision at the call site rather than a package default.

When Tier 2 lands, `prose`/`content` will be the one component that exists to
wrap caller-supplied HTML. It will need its own explicit statement here; the
rule above is not sufficient for it.

## Why the classes are written out longhand

Open a theme partial and you will find every class spelled literally:

```jinja
class="btn{% if variant == 'primary' %} btn-primary{% elif variant == 'danger' %} btn-error{% endif %}"
```

rather than the obvious `btn-{{ variant }}`. This is required, not stylistic.
daisyUI compiles through Tailwind, whose scanner reads source **text** — a
class name assembled at render time is never seen, so it is removed from the
build. No error, no warning, an unstyled page as the only symptom. Emitting the
class from Python has exactly the same effect, which is why
`cf_ui.primitives.classes_for()` exists for tests and consumers but is not used
by the shipped templates.

The cost is that the vocabulary lives in two places: `primitives.py` and ten
template files. `tests/unit/test_primitives.py` binds them in both directions —
every class in the map must appear literally in the templates, and every class
in the templates must be in the map or in a short, explicit list of layout
utilities. Neither copy can move alone.

That duplication is also why every primitive template calls the guard once:

```jinja
{{ cf_ui_validate("button", variant=variant, size=size, state=state) }}
```

A literal `{% if %}` chain has no `else`. Handed `variant="purple"` it matches
nothing and renders a correct-looking element with no colour. The guard turns
that silence into an exception at the call site.

!!! note "The guard needs the installer"

    `cf_ui_validate` is bound by `install_cf_ui` (FastAPI and Litestar) and by
    the `cf_ui` template library (Django), alongside the axis globals. A
    primitive rendered on a bare `Catalog()` with no installer raises
    `'cf_ui_validate' is undefined` — the same requirement
    `cf_ui_root_attrs()` already has.

## Regenerating

`primitives.py` is the single source of truth;
`static/cf_ui/cf_ui_primitives.json` is a build product of it — the
machine-readable export of the vocabularies and class maps, mirroring
`cf_ui_axes.json`. Edit the module, then:

```bash
just primitives
```

and commit both. A drift test fails the build otherwise.

## Not yet implemented

`badge`, `heading`, `label`, and `icon` have settled contracts above but no
templates yet — they are registered in `PRIMITIVES` and deliberately **not** in
`themes.COMPONENTS`, so referring to one raises a clear `ThemeError` rather
than a `TemplateDoesNotExist` at first render.

Tier 2 (`box`/`surface`, `prose`/`content`) and Tier 3 (`grid`) are tracked
separately. `grid` in particular is not a settled question: Bootstrap, Bulma,
Foundation, and Fomantic all ship 12-column systems with different
vocabularies, while daisyUI ships none and defers to Tailwind utilities — so a
daisy `grid` would emit raw utility classes while the other four emit framework
classes. That is a genuine asymmetry rather than a thin adapter, and it is
being decided on its own rather than inside this layer.
