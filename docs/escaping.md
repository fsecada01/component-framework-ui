# Escaping

**cf-ui templates escape their own output.** Every one of the shipped Jinja
component templates wraps its body in `{% autoescape true %}`, so a hostile
prop is escaped whatever the surrounding environment is configured to do.

```jinja
{#def content="", header="", footer="", extra_class="" #}
{% autoescape true %}
...
{% endautoescape %}
```

This holds on a bare `Catalog()` — whose environment does **not** autoescape —
and it holds for a consumer who calls `catalog.add_folder(...)` directly and
never calls `install_cf_ui` at all.

## What this means for you

**You get escaping by default and cannot lose it by misconfiguring Jinja.**
Your own templates keep whatever escaping policy you set; cf-ui's are escaped
regardless.

**A prop carrying real markup must be `Markup`.** This is the intended and only
per-value override:

```python
from markupsafe import Markup

catalog.render("Cf:Card", header="Report", _content=Markup("<b>bold</b>"))
```

Pass a plain string and the tags render as visible text — that is the safe
default doing its job, not a bug.

In Django, the same rule applies through the template layer: values are
escaped unless marked safe (`mark_safe`, or a `SafeString` from a form widget).

**There is no opt-out flag.** No setting, no installer keyword, no environment
variable turns cf-ui's escaping off. An escape hatch was prototyped during #36
and removed — a global switch that silently disables escaping across every
component is exactly the shape of thing that gets flipped once during
debugging and never flipped back.

## Overriding a whole template

If you genuinely need a component to emit unescaped output, replace the
template rather than disabling the mechanism. JinjaX resolves folders in
registration order, so a folder added **before** cf-ui's shadows it:

```python
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui

catalog = Catalog()
catalog.add_folder("my_templates/cf", prefix="Cf")   # (1)!
install_cf_ui(catalog, theme="bulma")                # (2)!
```

1. Registered first — your `Card.jinja` wins.
2. cf-ui's copies fill in every component you did not override.

This is deliberate: the override is per-component, visible in your repository,
and reviewable as a diff. A boolean in a settings file is none of those.

## Why it works this way

The obvious implementation — have `install_cf_ui` set `autoescape=True` on the
catalog's environment — was tried and failed three separate ways. The history
is worth knowing because each failure looks reasonable in isolation:

**Setting it unconditionally destroyed the caller's policy.** An app that
passed `select_autoescape(...)` had it silently overwritten by a plain `True`,
changing escaping behavior for the app's own templates.

**Guarding it ("only set it when escaping is off") reopened the hole.**
`select_autoescape` keys off the file *extension*, and cf-ui's templates are
`.jinja`. The idiomatic `select_autoescape(["html"])` therefore answers
`False` for every cf-ui template while reading as truthy at the environment
level — so the guard deferred to it and cf-ui rendered unescaped. This is
still pinned as an executable note in the test suite:

```python
from jinja2 import select_autoescape

assert select_autoescape(["html"])("Tabs.jinja") is False
```

**Both versions were order-dependent.** Jinja reads `autoescape` at *compile*
time and JinjaX caches compiled components. A component rendered before
`install_cf_ui` ran stayed compiled with the old setting, so whether escaping
applied depended on call order.

Every one of those defects came from the same root choice: making escaping a
property of a shared, mutable `Environment` that cf-ui does not own. Moving the
invariant into the files cf-ui *does* own removes the entire class.

Consequently:

!!! note "The installers never touch `autoescape`"
    `install_cf_ui` leaves the environment's escaping setting exactly as it
    found it, `select_autoescape` callables included. Your app's escaping
    policy is your app's.

## Assets macros

`cf_ui/assets.jinja` carries the same guarantee, with one structural
difference: the `{% autoescape true %}` blocks live *inside* each macro body
rather than at file scope. A file-scope block stops the macros being exported
and breaks every `{% from "cf_ui/assets.jinja" import ... %}` downstream.

The axis attributes emitted by `cf_ui_root_attrs()` are `Markup` by
construction, so they survive; a hostile URL argument passed to
`cf_ui_head()` or `cf_ui_body()` is escaped.

## Verifying it yourself

The unfriendliest configuration a consumer can produce — no installer,
escaping explicitly off:

```python
from jinjax import Catalog

from cf_ui import JINJA_TEMPLATES_DIR

catalog = Catalog()
catalog.add_folder(JINJA_TEMPLATES_DIR / "bulma", prefix="Cf")
assert not catalog.jinja_env.autoescape

html = catalog.render("Cf:Card", header='" onmouseover="alert(1)" x="')
assert 'onmouseover="alert(1)"' not in html
```

The repository enforces this three ways: a source-level drift guard over all
70 templates (so a new theme cannot ship without the block), a per-theme
behavioural render with escaping off, and installer tests asserting both
`False` and a `select_autoescape` callable survive untouched.
