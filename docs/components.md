# Components

Identical prop names across every theme. Names are
theme-agnostic — the same tag renders Bulma, Bootstrap, Foundation, Fomantic,
or DaisyUI depending on `CF_UI_THEME` / `theme=`.

| Engine | Syntax | Python |
|---|---|---|
| JinjaX | `<Cf:Card>` | `catalog.render("Cf:Card", ...)` |
| django-cotton | `<c-cf.card>` | — |

!!! danger "JinjaX uses a colon"
    `<Cf:Card>` is the only form that resolves. `<CfCard>` and `<Cf.Card>`
    both raise `ComponentNotFound`, because `Cf` is a JinjaX *prefix* and the
    prefix separator is `:`.

Every component accepts `extra_class` for consumer CSS overrides. Form
components additionally accept `input_class` (and `CheckboxGroup`,
`control_class`) so you can style the control without restyling the wrapper.

## Primitives

Small, high-frequency elements whose `variant`/`size`/`state` values come from
closed vocabularies. See [Primitives](primitives.md) for the shared contract,
how they compose, and the disabled-link rule.

### `Cf:Button` / `<c-cf.button>`

| Prop | Default | Notes |
|---|---|---|
| `variant` | `"neutral"` | `primary` `secondary` `success` `warning` `danger` `info` `neutral` |
| `size` | `"normal"` | `small` `normal` `large` |
| `state` | `"normal"` | `normal` `loading` `disabled` |
| `href` | `""` | Non-empty renders an `<a>` instead of a `<button>` |
| `type` | `"button"` | `button` `submit` `reset`. `<button>` form only |
| `full_width` | `false` | |
| `extra_class` | `""` | |

An out-of-vocabulary value raises `PrimitiveConfigError` rather than rendering
an unstyled element.

### `Cf:Badge` / `<c-cf.badge>`

| Prop | Default | Notes |
|---|---|---|
| `variant` | `"neutral"` | |
| `size` | `"normal"` | Inert on Bootstrap and Foundation |
| `extra_class` | `""` | |
| `attrs` | `{}` | Extra HTML attributes — see [Attribute passthrough](primitives.md#attribute-passthrough) |

### `Cf:Heading` / `<c-cf.heading>`

| Prop | Default | Notes |
|---|---|---|
| `level` | `"2"` | `1`–`6`. Picks the tag; semantics only. Cannot be empty |
| `size` | `"normal"` | Visual size, independent of `level` |
| `emphasis` | `"normal"` | `normal` `subtle` |
| `extra_class` | `""` | |

### `Cf:Label` / `<c-cf.label>`

| Prop | Default | Notes |
|---|---|---|
| `size` | `"normal"` | No `small` step on Foundation |
| `for_id` | `""` | Becomes `for`. Spelling it `for` raises — `for` is a Python keyword |
| `required` | `false` | Renders an indicator announced as "required" |
| `extra_class` | `""` | |

### `Cf:Icon` / `<c-cf.icon>`

| Prop | Default | Notes |
|---|---|---|
| `size` | `"normal"` | Inert on Foundation |
| `label` | `""` | Empty ⇒ `aria-hidden`. Non-empty ⇒ `role="img"` + that name |
| `extra_class` | `""` | |
| `attrs` | `{}` | Extra HTML attributes — see [Attribute passthrough](primitives.md#attribute-passthrough) |

cf-ui ships no icons — put your own `<i>` or `<svg>` in the slot.

## Forms

### `Cf:FormField` / `<c-cf.form-field>`

A labelled input with error display.

| Prop | Default | Notes |
|---|---|---|
| `name` | *required* | Input `name` and `id` |
| `label` | *required* | Label text |
| `value` | `""` | Current value |
| `error` | `""` | Renders the error state when non-empty |
| `type` | `"text"` | Any HTML input type |
| `required` | `false` | Sets the `required` attribute |
| `extra_class` | `""` | On the field wrapper |
| `input_class` | `""` | On the `<input>` itself |

### `Cf:Select` / `<c-cf.select>`

| Prop | Default | Notes |
|---|---|---|
| `name` | *required* | |
| `label` | *required* | |
| `value` | `""` | Selected option value |
| `error` | `""` | |
| `options` | `[]` | List of `{value, label}` mappings |
| `extra_class` / `input_class` | `""` | |

### `Cf:Textarea` / `<c-cf.textarea>`

| Prop | Default | Notes |
|---|---|---|
| `name` | *required* | |
| `label` | *required* | |
| `value` | `""` | |
| `error` | `""` | |
| `rows` | `4` | |
| `extra_class` / `input_class` | `""` | |

### `Cf:CheckboxGroup` / `<c-cf.checkbox-group>`

| Prop | Default | Notes |
|---|---|---|
| `name` | *required* | Shared `name` for the group |
| `label` | *required* | Group legend |
| `choices` | `[]` | List of `{value, label}` mappings |
| `selected` | `[]` | List of checked values |
| `error` | `""` | |
| `extra_class` / `control_class` | `""` | |
| `attrs` | `{}` | Extra HTML attributes, on the **wrapper** — not a per-choice `<input>`. See [Attribute passthrough](primitives.md#attribute-passthrough) |

## Feedback

### `Cf:Modal` / `<c-cf.modal>`

| Prop | Default | Notes |
|---|---|---|
| `id` | `"modal"` | Target for `Alpine.store('cf').modal.open(id)` |
| `header` | `""` | |
| `content` | `""` | Body — the slot in template position |
| `footer` | `""` | |
| `label` | `"Dialog"` | Accessible name (`aria-label`) |
| `extra_class` | `""` | |

Focus trapping, focus restoration, and `Escape`-to-close live in
`cf_ui_alpine.js`, not in the theme partial — see
[Accessibility](accessibility.md).

### `Cf:Notification` / `<c-cf.notification>`

| Prop | Default | Notes |
|---|---|---|
| `content` | `""` | Body — the slot in template position; wins over `message` |
| `message` | `""` | Scalar alternative to the body, for a plain string |
| `type` | `"info"` | `info`, `success`, `warning`, `danger` |
| `dismissible` | `true` | Renders a close button |
| `extra_class` | `""` | |

Supply one or the other. A body passed as slot content is already-rendered
markup and is not escaped again; `message` is caller-supplied text and is.

### `Cf:Progress` / `<c-cf.progress>`

| Prop | Default | Notes |
|---|---|---|
| `value` | `0` | |
| `max` | `100` | |
| `type` | `"primary"` | Theme colour role |
| `label` | `""` | Accessible label |
| `extra_class` | `""` | |

## Content

### `Cf:Card` / `<c-cf.card>`

| Prop | Default | Notes |
|---|---|---|
| `content` | `""` | Body — the slot in template position |
| `header` | `""` | |
| `footer` | `""` | |
| `extra_class` | `""` | |

### `Cf:Table` / `<c-cf.table>`

| Prop | Default | Notes |
|---|---|---|
| `columns` | `[]` | List of column keys/labels |
| `rows` | `[]` | List of row mappings |
| `hx_target` | `""` | HTMX target for sort/paging links |
| `hx_url` | `""` | HTMX endpoint |
| `extra_class` | `""` | |

### `Cf:Pagination` / `<c-cf.pagination>`

| Prop | Default | Notes |
|---|---|---|
| `page` | `1` | Current page, 1-indexed |
| `total_pages` | `1` | |
| `hx_target` / `hx_url` | `""` | HTMX wiring |
| `extra_class` | `""` | |

### `Cf:Panel` / `<c-cf.panel>`

| Prop | Default | Notes |
|---|---|---|
| `title` | *required* | |
| `id` | `"panel"` | |
| `content` | `""` | Body — the slot in template position |
| `open` | `false` | Initial expanded state |
| `extra_class` | `""` | |

## Navigation

### `Cf:Navbar` / `<c-cf.navbar>`

| Prop | Default | Notes |
|---|---|---|
| `brand` | `""` | |
| `start` | `""` | Leading nav items |
| `end` | `""` | Trailing nav items |
| `extra_class` | `""` | |

### `Cf:Breadcrumb` / `<c-cf.breadcrumb>`

| Prop | Default | Notes |
|---|---|---|
| `items` | `[]` | List of `{label, url}` mappings |
| `extra_class` | `""` | |

### `Cf:Tabs` / `<c-cf.tabs>`

| Prop | Default | Notes |
|---|---|---|
| `tabs` | `[]` | List of `{id, url}` mappings |
| `hx_target` | `"tab-content"` | HTMX target for panel swaps |
| `active` | `""` | Active tab id |
| `content` | `""` | Panel body — the slot in template position |
| `extra_class` | `""` | |

Roving tabindex and arrow-key navigation come from `cf_ui_alpine.js`.

## Passing markup into a prop

cf-ui templates escape their own output, so a prop carrying real HTML must say
so explicitly with `markupsafe.Markup`:

```python
from markupsafe import Markup

catalog.render("Cf:Card", header="Report", _content=Markup("<b>bold</b>"))
```

Full rationale in [Escaping](escaping.md).
