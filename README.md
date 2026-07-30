# component-framework-ui

> CSS framework UI kit for [`component-framework`](https://github.com/fsecada01/component-framework) — Bulma, Bootstrap, Foundation, Fomantic UI, DaisyUI.

[![CI](https://github.com/fsecada01/component-framework-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/fsecada01/component-framework-ui/actions/workflows/ci.yml)
[![Docs](https://github.com/fsecada01/component-framework-ui/actions/workflows/docs.yml/badge.svg)](https://fsecada01.github.io/component-framework-ui/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-blue.svg)]()

**📖 Full documentation: <https://fsecada01.github.io/component-framework-ui/>**

---

Fourteen ready-to-use components in two first-class template sets:

| Template set | Engine | Web frameworks |
|---|---|---|
| `jinja/` | Jinja2 / JinjaX | FastAPI, Litestar |
| `cotton/` | django-cotton | Django |

Component names are **theme-agnostic** — `<Cf:Card>` and `<c-cf.card>` render
whichever theme is active. Switching CSS frameworks means changing one config
line, not hundreds of templates.

## Install

```bash
pip install "cf-ui[django,bulma]"        # Django + Bulma
pip install "cf-ui[fastapi,daisy]"       # FastAPI + Tailwind/DaisyUI
pip install "cf-ui[litestar,bootstrap]"  # Litestar + Bootstrap 5
```

All template sets ship in every install. Theme selection is runtime config, not
install-time.

→ [Installation guide](https://fsecada01.github.io/component-framework-ui/installation/)

## Thirty-second look

```django
{# Django #}
{% load cf_ui %}
<c-cf.card header="Welcome">Card body content.</c-cf.card>
<c-cf.form-field name="email" label="Email" type="email" />
```

```python
# FastAPI
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui

catalog = Catalog()
install_cf_ui(catalog, theme="bulma")

html = catalog.render("Cf:Card", header="Welcome", _content="Card body.")
```

→ [Quickstart for all three frameworks](https://fsecada01.github.io/component-framework-ui/quickstart/)

## Themes

| Theme | Status |
|---|---|
| Bulma | ✅ |
| Tailwind + DaisyUI | ✅ — [guide](docs/daisyui.md) |
| Bootstrap 5 | ✅ — CSS only, no `bootstrap.bundle.js`; [decision record](docs/bootstrap.md) |
| Foundation 6 | ✅ — CSS only, no jQuery |
| Fomantic UI | ✅ — CSS only, no jQuery |

Switching is one line — `CF_UI_THEME = "daisy"` on Django, `theme="daisy"` on
FastAPI/Litestar — and needs no template edits in the consuming app. An
unimplemented theme name is rejected at startup rather than at first render.

## Documentation

| Page | What's in it |
|---|---|
| [Installation](https://fsecada01.github.io/component-framework-ui/installation/) | Extras, requirements, asset options |
| [Quickstart](https://fsecada01.github.io/component-framework-ui/quickstart/) | Django, FastAPI, and Litestar setups |
| [Getting started](https://fsecada01.github.io/component-framework-ui/getting-started/) | Themes, assets, composition axes, Alpine, escaping |
| [Use cases](https://fsecada01.github.io/component-framework-ui/use-cases/) | HTMX tables, modals, forms with errors |
| [Components](https://fsecada01.github.io/component-framework-ui/components/) | All fourteen, with every prop |
| [Escaping](https://fsecada01.github.io/component-framework-ui/escaping/) | Why cf-ui escapes its own output |
| [Theming](docs/theming.md) | Composition axes and custom value sets |
| [Tailwind plugin](docs/tailwind-plugin.md) | Build-time axis validation |
| [Accessibility](docs/accessibility.md) | Focus management, ARIA, keyboard behavior |

## Development

```bash
git clone https://github.com/fsecada01/component-framework-ui
cd component-framework-ui
uv pip install -e ".[dev]"
playwright install chromium

just test             # unit tests
just test-integration # integration tests
just test-e2e         # E2E Playwright tests (requires chromium)
just test-all         # everything
just lint             # ruff check
just format           # ruff format
just docs             # serve the docs site locally
```

## Requirements

- Python 3.11+
- `component-framework >= 0.4`
- Pydantic 2.0+ *(only mandatory runtime dependency)*

Optional extras:
- `[django]` — Django 4.2+, django-cotton 2.x
- `[fastapi]` — FastAPI 0.109+, JinjaX 0.41+
- `[litestar]` — Litestar 2.0+, Jinja2 3.1+

## License

MIT
