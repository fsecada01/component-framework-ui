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
| `box` | ● | | | | | |
| `prose` | | ● | | | | |

`label` and `icon` take no `variant` on purpose. A label's colour belongs to
the field it labels and an icon's to whatever contains it; giving either its
own would create two sources of truth for one colour.

`box` takes `variant` and nothing else — a container's size is its content's
business, and no shipped framework models a "state" for a plain box. `prose`
takes only `size`: a typographic reset has no colour of its own, and giving
it `variant` would mean colouring every nested element it wraps rather than
the one thing this primitive actually decides.

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
| `box` | `variant` is **inert** on Bulma — `.box` has no colour modifier at all |
| `prose` | `size` is **inert** on Bootstrap, Foundation, and Fomantic — their base typography already applies document-wide, so there is no reset step left for `size` to control |

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
| `attrs` | `{}` | Arbitrary extra HTML attributes — `data-*`, `hx-*`, Alpine bindings. See below |
| slot | — | The label |

### Attribute passthrough

`attrs` is a `dict[str, str]` of extra attributes rendered as literal
`key="value"` pairs on the root element, for attributes no named prop covers
— `data-event`, `hx-get`, `x-on:click`, `aria-controls`:

=== "JinjaX"

    ```jinja
    <Cf:Button :_attrs="{'data-event': 'submit', 'hx-post': '/orders'}">
      Save
    </Cf:Button>
    ```

    JinjaX reserves the prop name `attrs` for its own extra-kwargs collector
    and unconditionally overwrites whatever a component's `{#def}` declares
    for it — `:attrs="{...}"` compiles, runs, and silently discards the
    dict, with no error. `_attrs` (or `__attrs`) is JinjaX's own escape
    hatch for this collision; use it instead. This applies only to the
    JinjaX path — django-cotton has no equivalent reservation, so its own
    `attrs` prop below is unaffected. See #78.

=== "django-cotton"

    ```html
    <c-cf.button :attrs="{'data-event': 'submit', 'hx-post': '/orders'}">
      Save
    </c-cf.button>
    ```

Rendered by a single implementation, `cf_ui.primitives.render_attrs` — bound
as the Jinja global `cf_ui_render_attrs` and the Django `{% cf_ui_render_attrs %}`
tag — rather than inline per template, the way `cf_ui_validate` already
centralizes the axis vocabulary. It escapes every key and value itself
(`html.escape`), so it does not depend on the surrounding template's
autoescape state, and it validates the **key**, not just the value: an
attribute name may contain only letters, digits, `_`, `.`, `:` and `-`.
That closes a hole plain HTML-entity escaping cannot — a key containing a
space or `=` forges a brand-new attribute even when its value is fully
escaped, because entity escaping never touches either character. A key that
collides with a prop the component already renders (`type`, `class`,
`href`, …) is rejected outright rather than silently losing to HTML's
keep-the-first-duplicate rule — **on the django-cotton and unit-test paths.**
Under a real JinjaX `Catalog`, that guard only reliably fires for a
collision key that is *not* also one of the component's own declared prop
names (`class`, `role`, `aria-disabled`, `disabled` for `Button`). A key
that is both RESERVED_ATTRS-listed and a declared prop (`type`, `href` for
`Button`; `name` for the form controls) never reaches the guard at all —
JinjaX's own arg-filtering routes it straight into that prop before
`render_attrs` runs, so it silently becomes the prop's value instead (the
caller's real prop, if also passed, wins). This is a JinjaX-level gap, not
a cf-ui one; never pass one of a component's own prop names through
`attrs`/`_attrs` — pass it as that prop directly. See
[Escaping](escaping.md). Currently `Button`-only; the same shape is expected
to roll out to the rest of Tier 1 as separate follow-up work (#71, #72).

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

## `Cf:Box` / `<c-cf.box>`

| Prop | Default | Notes |
|---|---|---|
| `variant` | `"neutral"` | Inert on Bulma — see below |
| `extra_class` / `class` | `""` | |
| slot | — | Arbitrary content |

`box` is a plain bordered or elevated container: one element, no imposed
inner structure. It is named `box`, not `surface` — `box` is Bulma's actual
class name for this element, and `surface` is Material Design vocabulary
that none of the five shipped frameworks use.

```jinja
<Cf:Box variant="danger">
  Something needs attention.
</Cf:Box>
```

```html
<c-cf.box variant="danger">
  Something needs attention.
</c-cf.box>
```

Bootstrap has no box component, so cf-ui composes one from utilities —
`border rounded p-3`, with `variant` mapping to `border-primary` and so on.
`card` was considered and rejected: it imposes a header/body/footer structure
a plain box's caller cannot opt out of. Foundation renders `callout`, with
`variant` mapped onto its five colours (`primary secondary success warning
alert`); Foundation spells danger `alert` and ships no informational hue, so
`info` folds onto `secondary` — the same substitution `badge` already makes
on this theme. On daisy the border colour lives entirely in `variant`,
`neutral` included (`border-base-300`): splitting a default colour into
`base` and an override into `variant` would put two border-color utilities
of equal specificity on one element, leaving Tailwind's emission order,
rather than this map, to decide which one renders.

### Bulma: `variant` is inert

Bulma ships no colour modifier for `.box`. `has-background-*` classes exist,
but they set a saturated background without touching text colour — routing
`variant` through them would make a themed box unreadable rather than
themed. cf-ui leaves the axis inert on this theme instead of faking it: a
Bulma box looks the same regardless of `variant`.

### Fomantic: the hue trap

Fomantic renders a box as `ui segment` plus a hue — `blue grey green yellow
red teal`. This is the theme where the obvious implementation is wrong, and
worth saying plainly because it is the kind of trap this doc exists to
record.

`primary` and `secondary` are **not** colours on a Fomantic segment — they
are its *emphasis* variation. `.ui.primary.segment` renders a subdued
treatment, not a brand-coloured fill. Mapping `variant="primary"` onto the
literal word `primary` would compile, look plausible, and silently produce
the wrong result on the one theme where the variant name happens to match a
real Fomantic class. cf-ui maps `primary` to `blue` and `secondary` to
`grey` instead — real hues, not the words that look like they should work.

## `Cf:Prose` / `<c-cf.prose>`

| Prop | Default | Notes |
|---|---|---|
| `size` | `"normal"` | Inert on Bootstrap, Foundation, and Fomantic — see below |
| `extra_class` / `class` | `""` | |
| slot | — | Arbitrary rich content: headings, paragraphs, lists, tables |

`prose` is a typographic reset block: it styles nested `h1`–`h6`, `p`, `ul`,
and `table` without requiring a class on each one. It takes `size` and
nothing else, for the reason given above the axis table.

It is named `prose`, not `content`, for two concrete reasons. `content`
collides with Bulma's own `.content` class — the exact class this component
maps to on that theme — and `content` is already the prop name every Jinja
primitive uses for slot text, so the JinjaX spelling would have been a
`Content` component taking a `content` prop — self-contradictory. (Written
out rather than shown as a tag: `tests/unit/test_docs_samples.py` resolves
every `Cf:` tag in these docs against the real catalogue, so a component that
deliberately does not exist cannot be illustrated as one.)

```jinja
<Cf:Prose size="large">
  <h2>Release notes</h2>
  <p>Everything in this block gets typographic styling for free.</p>
</Cf:Prose>
```

```html
<c-cf.prose size="large">
  <h2>Release notes</h2>
  <p>Everything in this block gets typographic styling for free.</p>
</c-cf.prose>
```

On Bulma it maps to `.content`, with `is-small`/`is-large` for `size` — the
reference implementation the other four themes are measured against.

### Bootstrap and Foundation: no class, and that's correct

Both frameworks emit no class at all for `prose`, and `size` is inert on
both. That is not a gap. Bootstrap's Reboot and Foundation's base typography
style bare `h1`-`h6`, `p`, and `ul` document-wide already, so the reset this
component exists to scope is already in effect everywhere on the page —
there is nothing for a class to add.

### Fomantic: a real gap, and a different reason

Fomantic emits no class either, but not for the same reason as the two
above, and this one is a genuine limitation rather than a redundant no-op.

Fomantic does style bare `h1`-`h5` and `p` globally, so headings and
paragraphs inside a `Cf:Prose` block come out right with no wrapper class
needed. It ships **no bare `ul`, `ol`, or `table` rule at all** — that
styling lives on `.ui.list` and `.ui.table`, applied to the element itself
rather than inherited from an ancestor. A list or table inside a prose block
therefore renders with browser defaults, and no scoping class exists that
would fix it.

cf-ui does not paper over this by authoring its own Fomantic typography
reset — that would mean shipping component CSS this package has never
shipped, and guessing at a framework's type scale instead of using the
framework's own. If you need a styled list or table inside a Fomantic prose
block, reach for the framework's own element-level classes directly: use
[`<c-cf.table>`](components.md) for tables, and put `ui list` on `<ul>`/`<ol>`.

### daisyUI: requires `@tailwindcss/typography`

On daisy, `prose` maps to the `prose` class, with `prose-sm`/`prose-lg` for
`size` — but `prose` is not a daisyUI class and not a Tailwind core class.
It comes from `@tailwindcss/typography`, a separate plugin declared a
requirement for this one component on this one theme. See
[DaisyUI theme](daisyui.md) for how to add it.

Without the plugin, `prose` is simply an unrecognised class name: the block
renders unstyled, with no error and no warning. That is the same benign
class-valued failure mode `AXIS_KINDS` already tolerates for an empty axis
value — it just arrives here from a missing plugin instead of an empty prop.

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

`prose` is the other one, and the stakes are higher: its whole purpose is to
wrap caller-supplied HTML, often multiple elements of it, rather than one
`<i>` tag. The mechanism is identical — slot-based, still inside cf-ui's own
`{% autoescape true %}` block — but the rule above is not sufficient on its
own to say what's safe to put there. See
[Escaping: the `prose` contract](escaping.md#the-prose-contract) for the
explicit statement.

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

## The primitives layer is complete

Every primitive registered in `PRIMITIVES` — `button`, `badge`, `heading`,
`label`, `icon`, `box`, `prose` — ships templates on all five themes in both
engines. Tier 1 (`badge`, `heading`, `label`, `icon`) landed in #53; Tier 2
(`box`, `prose`), documented above, is #54. Tier 3 was `grid`, and the
decision on it is below: cf-ui does not ship one.

## Layout is out of scope

**cf-ui does not ship a grid, and will not.** Decided in #55; this section
is the reasoning, so it does not have to be re-litigated.

### Why not

The premise the ticket was written on turned out to be false. It assumed
four of the five themes ship a 12-column grid and only daisyUI is the odd
one out. Checked against upstream documentation, the frameworks do not
agree on the two things a shared grid vocabulary would have to fix:

| Theme | Columns | Breakpoint model | Tiers |
|---|---|---|---|
| Bootstrap 5.3 | 12 | min-width | (none) · sm 576 · md 768 · lg 992 · xl 1200 · xxl 1400 |
| Bulma 1.0 | 12 | `mobile` is **max**-width, the rest min-width | mobile <768 · tablet 769 · desktop 1024 · widescreen 1216 · fullhd 1408 |
| Foundation 6.7 | 12 | min-width | small 0 · medium 640 · large 1024 · xlarge 1200 · xxlarge 1440 |
| Fomantic 2.9 | **16** | min-width | mobile 320 · tablet 768 · computer 992 · large monitor 1200 · widescreen 1920 |
| Tailwind 3 (daisy) | 12 utilities | min-width | sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1536 |

Two facts in that table kill the abstraction on their own.

**Fomantic's grid is 16 columns.** Not a different spelling of the same
idea — a different idea. A column asking for a span of 6 would mean half
the row on four themes and three-eighths of it on Fomantic. There is no span
vocabulary that is correct on both, and the failure is silent: the page
still renders, just at the wrong width. Every other axis cf-ui absorbs
maps *n* names onto *n* spellings of one concept. This one does not have
one concept underneath it.

**Bulma's `mobile` is a max-width cap, not a rung on a min-width ladder.**
So a canonical breakpoint set is not merely a numbers problem where cf-ui
picks the least-wrong value. It is a shape problem: `at="mobile"` means
"from here up" on four themes and "below here" on Bulma, and a mapping
that inverts a condition is not a mapping.

The numbers themselves are also not as tidy as "everyone disagrees" would
suggest — Bootstrap's `md` and Tailwind's `md` are both 768px, and Bulma's
tablet lands one pixel away. That incidental overlap is worth stating
because it is the strongest thing the build case had, and it is not
enough: agreement at one tier out of five, between two of five themes,
does not make the ladders interchangeable.

daisyUI's asymmetry, which the ticket led with, is real but is the least
of it. daisyUI ships no grid at all and defers to Tailwind utilities, so a
daisy `grid` would emit `grid-cols-12` and `col-span-6` — utility classes,
not framework component classes, and inert for any consumer who installed
daisyUI's compiled CSS without a Tailwind build.

### Why not a reduced version either

The obvious retreat is a non-responsive grid: a fixed set of column counts,
no breakpoint axis. It covers most of the measured uses in the reference
repo and sidesteps the breakpoint disagreement entirely.

It is still the wrong thing to ship, for two reasons that point the same
way. A three-column layout that stays three columns on a phone is not a
simpler grid, it is a broken one — so nobody would use the reduced version
as-is; they would reach for the responsive escape hatch immediately, which
is the part that does not work. And Fomantic's 16 columns break the
reduced version just as thoroughly as the full one, because the column
count is not the responsive axis. Cutting responsiveness removes the
smaller problem and leaves the larger one.

The Tailwind literal-class constraint is the third strike rather than the
first: 12 spans × 5 breakpoints is 60 spelled-out branches per template,
duplicated in `primitives.py` for the parity test, for a component whose
semantics are wrong on one theme in five.

### What this costs, stated plainly

cf-ui's design principle is that switching CSS frameworks means changing
`CF_UI_THEME` in one place. **Layout is the exception.** A consumer who
writes `<div class="columns"><div class="column is-6">` has written Bulma
into their templates, and flipping `CF_UI_THEME` to `bootstrap` leaves
every component correct and every page's layout broken.

That is a real limit and cf-ui would rather name it than paper over it
with a component that is silently wrong on Fomantic.

### What to do instead

- **Write layout in the framework's own vocabulary.** It is the one place
  a direct dependency is cheaper than an adapter, because the adapter
  cannot be correct.
- **If you need theme-switchable layout, use CSS Grid or flexbox
  directly.** `display: grid; grid-template-columns: repeat(3, 1fr)` with
  a media query is framework-independent, needs no build step, and is
  about as much code as the component would have been at the call site.
- **If you are migrating to Tailwind or daisyUI, write Tailwind
  utilities.** That is what the reference-repo migration behind #52 does,
  and a cf-ui grid would have been pure indirection on the far side of it.

Layout being out of scope is a decision, not a gap. Please don't file it
as a bug.
