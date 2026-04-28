# component-framework-ui

> CSS framework UI kit for [`component-framework`](https://github.com/fsecada01/component-framework) — Bulma, Bootstrap, Foundation, Fomantic UI, DaisyUI.

[![CI](https://github.com/fsecada01/component-framework-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/fsecada01/component-framework-ui/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-blue.svg)]()

Provides ready-to-use Bulma component templates in two first-class template sets:

| Template set | Engine | Frameworks |
|---|---|---|
| `jinja/` | Jinja2 / JinjaX | FastAPI, Litestar |
| `cotton/` | django-cotton | Django |

Component names are **theme-agnostic** — `<CfCard>` and `<c-cf.card>` render the active theme. Switching CSS frameworks means changing one config line, not hundreds of templates.

---

## Installation

```bash
# Bulma (v0.1 — only supported theme)
pip install "cf-ui[bulma]"

# All themes (stubs for future Bootstrap, Foundation, Fomantic, DaisyUI)
pip install "cf-ui[all]"
```

All template sets ship in every install. Theme selection is runtime config, not install-time.

---

## Quick Start

### Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    "cf_ui.django.CfUiConfig",
]
CF_UI_THEME = "bulma"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {
        "libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"},
    },
}]
```

```django
{# base.html #}
{% load cf_ui %}
<!DOCTYPE html>
<html>
<head>
  {% cf_ui_head %}
</head>
<body>
  {% block content %}{% endblock %}
  {% cf_ui_body %}
</body>
</html>

{# any template #}
<c-cf.card>
  <c-slot name="header">My Title</c-slot>
  Card body content here.
</c-cf.card>

<c-cf.form-field name="email" label="Email" value="{{ form.email.value }}"
                 error="{{ form.email.errors.0 }}" type="email" />
```

### FastAPI + JinjaX

```python
from jinjax import ComponentCatalog
from cf_ui.fastapi import install_cf_ui

catalog = ComponentCatalog()
install_cf_ui(catalog, theme="bulma")
```

```html
{# any JinjaX template #}
<CfCard header="Title">
  Card body content.
</CfCard>

<CfFormField name="email" label="Email" value="" extra_class="mb-4" />
```

### Litestar

```python
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template import TemplateConfig
from cf_ui.litestar import install_cf_ui

config = TemplateConfig(engine=JinjaTemplateEngine, directory="templates")
install_cf_ui(config, theme="bulma")
```

---

## Components (v0.1 — Bulma)

### Forms

| Component | Key props |
|---|---|
| `CfFormField` / `<c-cf.form-field>` | `name`, `label`, `value`, `error`, `type`, `required`, `extra_class` |
| `CfSelect` / `<c-cf.select>` | `name`, `label`, `value`, `error`, `options` |
| `CfTextarea` / `<c-cf.textarea>` | `name`, `label`, `value`, `error`, `rows` |
| `CfCheckboxGroup` / `<c-cf.checkbox-group>` | `name`, `label`, `choices`, `selected`, `error` |

### Feedback

| Component | Key props / slots |
|---|---|
| `CfModal` / `<c-cf.modal>` | `id`, `extra_class`; slots: `header`, default body, `footer` |
| `CfNotification` / `<c-cf.notification>` | `message`, `type`, `dismissible` |
| `CfProgress` / `<c-cf.progress>` | `value`, `max`, `type`, `label` |

### Content

| Component | Key props / slots |
|---|---|
| `CfCard` / `<c-cf.card>` | `extra_class`; slots: `header`, default body, `footer` |
| `CfTable` / `<c-cf.table>` | `columns`, `rows`, `hx_target`, `hx_url` |
| `CfPagination` / `<c-cf.pagination>` | `page`, `total_pages`, `hx_target`, `hx_url` |
| `CfPanel` / `<c-cf.panel>` | `title`, `open`, `extra_class`; slot: default body |

### Navigation

| Component | Key props / slots |
|---|---|
| `CfNavbar` / `<c-cf.navbar>` | `extra_class`; slots: `brand`, `start`, `end` |
| `CfBreadcrumb` / `<c-cf.breadcrumb>` | `items` (list of `{label, url}`) |
| `CfTabs` / `<c-cf.tabs>` | `tabs` (list of `{id, url}`), `hx_target` |

All components accept an `extra_class` prop for consumer CSS overrides.

---

## CDN Asset Tags

`{% cf_ui_head %}` and `{% cf_ui_body %}` inject CDN links for the active theme + AlpineJS. CDN versions are pinned defaults, overridable:

```python
# settings.py
CF_UI_CDN_VERSIONS = {
    "bulma": "1.0.2",
    "alpinejs": "3.14.1",
}
```

Opt out of CDN entirely — just don't call the tags and load assets yourself.

Jinja2 equivalent:
```jinja
{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_body %}
{{ cf_ui_head(theme="bulma") }}
{{ cf_ui_body(theme="bulma", cf_alpine_url="/static/cf_ui/cf_ui_alpine.js") }}
```

---

## Alpine.js Integration

`{% cf_ui_body %}` loads `cf_ui_alpine.js` (before the Alpine CDN) which registers:

**Named components** — use `x-data="cfModal"` to bind from outside:
- `cfModal` — `open`, `toggle()`, `close()`, `initModal()`
- `cfNavbar` — `menuOpen`, `toggle()`
- `cfPanel` — `open`, `toggle()`
- `cfTabs` — `active`, `setActive(id)`

**`$cf` global store** — cross-component messaging from any template:
```html
<button @click="$store.cf.notify('Saved!', 'success')">Save</button>
<button @click="Alpine.store('cf').modal.open('confirm-dialog')">Delete</button>
```

Opt out entirely:
```django
{% cf_ui_body alpine=False %}
```

---

## Escape Hatch

If you need direct access to template directories for custom configuration:

```python
from cf_ui import JINJA_TEMPLATES_DIR, COTTON_TEMPLATES_DIR

# JINJA_TEMPLATES_DIR / "bulma"  →  Path to Jinja2 templates (theme-prefixed)
# COTTON_TEMPLATES_DIR / "cf"    →  Path to Cotton component templates
```

> **Cotton templates are theme-agnostic on disk.** They live at
> `cotton/cf/*.html` (not `cotton/<theme>/cf/*.html`) so cf-ui can sit
> alongside any consumer project's own `templates/cotton/<app>/...` tree
> without colliding on `COTTON_DIR`. The active CSS framework is selected
> via `CF_UI_THEME` (used by the asset tags) — switching themes in a
> future release will happen inside the templates, not via the directory
> layout.

---

## Planned Themes

| Theme | Status |
|---|---|
| Bulma | ✅ v0.1.0 |
| Bootstrap | 📋 Planned |
| Foundation | 📋 Planned |
| Fomantic UI | 📋 Planned |
| Tailwind + DaisyUI | 📋 Planned |

---

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
```

---

## Requirements

- Python 3.11+
- `component-framework >= 0.4`
- Pydantic 2.0+ *(only mandatory runtime dependency)*

Optional extras:
- `[django]` — Django 4.2+, django-cotton 2.x
- `[fastapi]` — FastAPI 0.109+, JinjaX 0.41+
- `[litestar]` — Litestar 2.0+, Jinja2 3.1+

---

## License

MIT
