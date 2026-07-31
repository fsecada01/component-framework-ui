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

Six axes, each a **closed set**, declared in
[`cf_ui/primitives.py`](https://github.com/fsecada01/component-framework-ui/blob/master/src/cf_ui/primitives.py).
An unknown value raises `PrimitiveConfigError` naming the values that would
have worked — it does not fall through to an unstyled element.

| Axis | Values | Becomes |
|---|---|---|
| `variant` | `primary` `secondary` `success` `warning` `danger` `info` `neutral` | a class |
| `size` | `small` `normal` `large` | a class |
| `state` | `normal` `loading` `disabled` | a class |
| `emphasis` | `normal` `subtle` | a class |
| `level` | `1`–`6` | the **tag** |
| `type` | `button` `submit` `reset` | an **attribute** |

Seven variants, not "whatever the framework ships". All five frameworks can
express all seven, though two collapse a pair onto one class — Foundation has
no informational button colour, so `info` renders as `secondary` rather than
cf-ui inventing a class Foundation's own CSS does not define. A vocabulary cut
down to the poorest framework would make the richer ones useless; one built for
the richest would make `info` mean nothing in Foundation.

`normal` is the **middle step**, not "whatever the framework does with no
class". Usually those coincide and it maps to no class at all — a real entry in
the map, not a gap, since the completeness test treats a *missing* key as the
failure.

Two things follow from that, and both are visible to consumers:

**Sometimes `normal` needs a class.** Bulma's `.tag` defaults to its smallest
step, so a normal badge maps to `is-medium` in order to line up with a normal
button. The shared vocabulary is the whole point — `size="normal"` has to mean
one thing across primitives, or sharing it buys nothing.

**Sometimes `size` does nothing.** Bootstrap and Foundation ship no badge size
classes, so all three values map to no class and a Bootstrap badge renders
identically at every size. cf-ui does not fake this with font-size utilities:
Bootstrap's `fs-*` scale bottoms out *larger* than a default badge, so it
cannot express "small" and would be a wrong-direction lie. Switching
`CF_UI_THEME` can therefore change whether `size` has any effect on a given
primitive.

## What an axis value becomes, and why it matters

The third column of that table is not decoration. It is the one fact that
decides two separate things.

**Whether the axis has a per-theme class map.** Class-valued axes do. `level`
and `type` do not, because there is nothing to map — the value *is* the tag
name, or the attribute value.

**Whether an empty value is allowed.** For a class-valued axis it is: the class
is simply not emitted, and you get a valid element that is merely unstyled.
That tolerance is load-bearing rather than lax — Django resolves a missing
context variable to `""`, and every cotton wrapper forwards its props
unconditionally, so a guard that rejected empty values would reject ordinary
renders.

For `level` and `type` an empty value is *not* benign, so it raises:

```
<c-cf.heading :level="section.depth">   # depth is None

PrimitiveConfigError: heading needs a level — it becomes the element's tag,
so an empty one renders malformed markup rather than unstyled markup.
Pass one of: 1, 2, 3, 4, 5, 6
```

Without that check the render succeeds and emits `<h class="title">Section</h>`.
`<h>` is not an element. Browsers parse it as an unknown inline, and it still
picks up the `title` class — so it *looks* like a heading while being absent
from the document outline and unreachable by screen-reader heading navigation.
It is the exact silent failure the guard exists to convert into an exception,
in the one axis where an empty value degrades to malformed rather than
unstyled.

`type` is the same shape with a sharper edge. HTML's missing-value default for
an **invalid** `<button type>` is `submit` — so `type="sumbit"` does not render
an inert button, it renders one that submits the enclosing form. cf-ui defaults
to `button` precisely to avoid that, and an open set would have let a typo undo
it silently.

## Colour is not a channel on its own

A `danger` badge and a `success` badge differ only by hue. If the badge's own
text does not carry the meaning, that is a
[WCAG 1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)
failure, and it is not one cf-ui can fix from inside the component:

```html
<!-- Fails: "4" means nothing without the colour -->
<c-cf.badge variant="danger">4</c-cf.badge>

<!-- Passes: the text carries it -->
<c-cf.badge variant="danger">4 failed</c-cf.badge>
```

The variant sets the colour. Making the meaning legible without it is the
caller's obligation.

## Which primitive takes which axis

| Primitive | `variant` | `size` | `state` | `emphasis` | `level` | `type` |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `button` | ● | ● | ● | | | ● |
| `badge` | ● | ● | | | | |
| `heading` | | ● | | ● | ● | |
| `label` | | ● | | | | |
| `icon` | | ● | | | | |

`label` and `icon` take no `variant` on purpose. A label's colour belongs to
the field it labels and an icon's to whatever contains it; giving either its
own would create two sources of truth for one colour.

`heading` separates `level` from `size` because they answer different
questions — `level` is the document outline (`<h1>`…`<h6>`, which screen
readers navigate by) and `size` is how big it looks. Coupling them forces a
choice between a correct outline and a correct visual hierarchy.

`emphasis` started life as a `subtitle=True` boolean and was promoted, because
in Bulma `title` and `subtitle` are *alternatives* rather than additive. As a
boolean outside the class map it made `classes_for()` report `"title is-4"`
for a call that actually rendered `subtitle is-4` — and, worse, its daisyUI
class (`opacity-60`) was invisible to `cf_ui_primitives.json`, so a Tailwind
build would have tree-shaken it away. A prop that decides which classes are
emitted belongs in the map, where the parity test can see it.

## The axes are not all equally useful on every theme

This is the honest cost of one vocabulary across five frameworks, and it is
worth knowing before you reach for an axis:

| Primitive | Where an axis does less than you'd expect |
|---|---|
| `badge` | `size` is **inert** on Bootstrap and Foundation — neither ships badge size modifiers |
| `icon` | `size` is **inert** on Foundation, which has no icon wrapper and no font-size scale. On Bootstrap the scale is mixed: `small` is em-relative and composes inside a `btn-sm`, `large` is absolute and does not |
| `label` | `size` has no `small` step on Foundation |
| `button` | `info` renders as `secondary` on Foundation, which ships five button colours and no informational one |

cf-ui does not paper over these with utilities that reach the wrong values.
Bootstrap's `fs-*` scale, for instance, bottoms out *larger* than a default
badge, so using it for `size="small"` would be a wrong-direction lie rather
than a fallback.

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
| `type` | `"button"` | `button` `submit` `reset`. Only applies to the `<button>` form |
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

## `Cf:Badge` / `<c-cf.badge>`

| Prop | Default | Notes |
|---|---|---|
| `variant` | `"neutral"` | |
| `size` | `"normal"` | Inert on Bootstrap and Foundation |
| `extra_class` / `class` | `""` | |
| slot | — | The badge text |

Renders a `<span>` on every theme, with no `role` and no ARIA. `role="status"`
would make it a live region announced on every re-render, which is wrong for
a static badge — its slot text is its accessible name.

There is no `pill` prop. It is idiomatic in Bootstrap and Bulma and absent
from daisyUI, Foundation and Fomantic, so it would be inert on three of five;
reach for `class="rounded-pill"` instead.

## `Cf:Heading` / `<c-cf.heading>`

| Prop | Default | Notes |
|---|---|---|
| `level` | `"2"` | `1`–`6`. Renders `<h1>`…`<h6>`. Semantics only; cannot be empty |
| `size` | `"normal"` | Visual size, independent of `level` |
| `emphasis` | `"normal"` | `subtle` for a de-emphasised heading |
| `extra_class` / `class` | `""` | |
| slot | — | The heading text |

```html
<!-- An h2 in the outline that looks small -->
<c-cf.heading level="3" size="small">Section</c-cf.heading>
```

## `Cf:Label` / `<c-cf.label>`

| Prop | Default | Notes |
|---|---|---|
| `size` | `"normal"` | No `small` step on Foundation |
| `for_id` | `""` | Becomes the `for` attribute. **Not** `for` — see below |
| `required` | `false` | Renders an indicator announced as "required" |
| `extra_class` / `class` | `""` | |
| slot | — | The label text |

!!! warning "The attribute is `for_id`, not `for`"

    `for` is a Python reserved word, so JinjaX cannot express it. django-cotton
    *can*, which is the hazard: `<c-cf.label for="email">` would render valid
    HTML with no `for` attribute at all and a silently broken label/control
    association.

    `for` is therefore a **declared alias** — `primitives.ALIASES` maps it to
    `for_id`, the wrapper forwards it into the guard, and it raises naming the
    prop that works:

    ```
    PrimitiveConfigError: label takes no 'for' — use 'for_id'.
    ```

### What the alias table does and does not catch

`ALIASES` covers props whose natural **HTML spelling** differs from cf-ui's —
the name a caller will reach for first. Today that is one entry, and adding a
theme or a primitive does not change it.

It does **not** catch arbitrary misspellings. `<c-cf.icon labl="Delete item">`
still renders a decorative icon with the accessible name silently dropped,
because django-cotton discards any attribute a component does not declare —
for every cotton component in every project, not just cf-ui's. That is a
property of the template engine, not something a wrapper can close from the
inside. Treat cf-ui's prop names as exact.

The JinjaX side behaves the same way for a different reason: an undeclared
attribute lands in `attrs`, which cf-ui's templates do not render.

The required indicator is a single `<span role="img" aria-label="required">*</span>`
rather than a hidden-glyph-plus-visually-hidden-text pair, because Fomantic
2.9.3 ships no visually-hidden utility — that approach would have given four
themes one accessibility mechanism and the fifth another. Fomantic's own
`.required::after` is deliberately not used: generated content disappears under
print and high-contrast stylesheets, and its announcement is inconsistent.

## `Cf:Icon` / `<c-cf.icon>`

| Prop | Default | Notes |
|---|---|---|
| `size` | `"normal"` | Inert on Foundation; mixed scale on Bootstrap |
| `label` | `""` | Empty ⇒ decorative. Non-empty ⇒ the accessible name |
| `extra_class` / `class` | `""` | |
| slot | — | Your `<i>`, `<svg>`, or `<span>` |

The accessibility decision is most of what this component buys you, and it is
the part hand-written icon markup usually gets wrong:

```html
<!-- Decorative: skipped by screen readers entirely -->
<c-cf.icon><i class="fas fa-star"></i></c-cf.icon>
<span aria-hidden="true">…</span>

<!-- Meaningful: announced as "Delete item", and not descended into -->
<c-cf.icon label="Delete item"><i class="fas fa-trash"></i></c-cf.icon>
<span role="img" aria-label="Delete item">…</span>
```

The two are mutually exclusive by construction, so a labelled icon can never
also be `aria-hidden`. `role="img"` matters as much as the label: it makes the
wrapper a leaf for assistive technology, so the caller's meaningless glyph
markup is not descended into.

cf-ui ships no icons and depends on no icon set. Bootstrap assumes Bootstrap
Icons, Bulma assumes Font Awesome, daisyUI assumes nothing — there is no
class-level abstraction spanning all five, and adopting one would make a UI kit
choose its consumers' icon vendor.

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
