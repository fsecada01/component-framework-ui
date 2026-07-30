# cf-ui

CSS framework component templates for
[`component-framework`](https://github.com/fsecada01/component-framework) —
Bulma, Bootstrap 5, Foundation 6, Fomantic UI, and Tailwind + DaisyUI.

cf-ui ships fourteen components in two first-class template sets:

| Template set | Engine | Web frameworks |
|---|---|---|
| `jinja/` | Jinja2 / JinjaX | FastAPI, Litestar |
| `cotton/` | django-cotton | Django |

## The one idea

**Component names are theme-agnostic.** `<Cf:Card>` and `<c-cf.card>` render
whichever theme is active. Switching CSS frameworks is one config line, not a
sweep through hundreds of templates:

```python
CF_UI_THEME = "bootstrap"   # was "bulma"
```

Every template set ships in every install — theme selection is runtime config,
never install-time. An unimplemented theme name is rejected at startup rather
than at first render.

## Where to go

<div class="grid cards" markdown>

- **[Installation](installation.md)** — extras, requirements, what each one pulls in.
- **[Quickstart](quickstart.md)** — a rendering page in Django, FastAPI, or Litestar.
- **[Getting started](getting-started.md)** — the concepts behind the quickstart, in order.
- **[Use cases](use-cases.md)** — HTMX tables, modal confirmations, server-rendered forms.
- **[Components](components.md)** — all fourteen, with every prop.
- **[Escaping](escaping.md)** — why cf-ui escapes its own output, and how to pass real markup.

</div>

## What cf-ui does not do

- **It does not own your CSS.** cf-ui emits the theme's own class names and
  markup structure. Restyling is the framework's job, not cf-ui's.
- **It does not load framework JavaScript.** Bootstrap, Foundation, and Fomantic
  ship CSS only here; behavior runs through Alpine so one state owner is in
  charge under every theme. See [Bootstrap](bootstrap.md) for the decision
  record.
- **It does not stay renderer-agnostic.** That is `component-framework`'s job.
  cf-ui is deliberately the opinionated UI layer on top of it.

## Status

Beta. The component set and prop names are stable; see the repository
`CHANGELOG.md` for what changed between releases, including the two breaking
changes in 0.2.0.
