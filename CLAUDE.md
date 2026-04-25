# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

`component-framework-ui` (`cf-ui`) is a standalone PyPI package providing CSS framework component templates for [`component-framework`](https://github.com/fsecada01/component-framework). It ships two first-class template sets — Jinja2/JinjaX (FastAPI, Litestar) and django-cotton (Django) — for Bulma CSS, with stubs for Bootstrap, Foundation, Fomantic UI, and DaisyUI.

**Design principle:** `component-framework` stays renderer-agnostic. `cf-ui` is the opinionated UI layer. Component names are theme-agnostic (`CfCard`, `<c-cf.card>`) — switching CSS frameworks means changing `CF_UI_THEME` in one place.

## Commands

```bash
uv pip install -e ".[dev]"       # install with all dev deps
playwright install chromium       # install E2E browser

just test                         # unit tests only
just test-integration             # integration tests (real HTTP)
just test-e2e                     # E2E Playwright (requires chromium)
just test-all                     # full suite
just lint                         # ruff check
just lint-fix                     # ruff check --fix
just format                       # ruff format
just check                        # lint + unit tests
just build                        # hatch build wheel

pytest tests/unit/ -v                          # unit tests
pytest tests/unit/jinja/test_forms.py -v       # single test file
pytest tests/e2e/ --browser chromium -v        # E2E tests
```

## Architecture

```
src/cf_ui/
├── __init__.py              # exports JINJA_TEMPLATES_DIR, COTTON_TEMPLATES_DIR, __version__
├── _version.py
├── django.py                # AppConfig — AppConfig auto-registers COTTON_DIRS at startup
├── fastapi.py               # install_cf_ui(catalog, theme) — add_folder(prefix="Cf")
├── litestar.py              # install_cf_ui(config, theme) — appends to TemplateConfig.directory
├── templatetags/cf_ui.py    # Django simple_tags: cf_ui_head, cf_ui_body, get_item, make_list_1_to_n
├── templates/
│   ├── cf_ui/assets.jinja   # Jinja2 macros: cf_ui_head(), cf_ui_body()
│   ├── jinja/bulma/         # 14 JinjaX component templates (*.jinja)
│   └── cotton/bulma/cf/     # 14 django-cotton component templates (*.html)
└── static/cf_ui/
    └── cf_ui_alpine.js      # Alpine named components + $cf global store
```

Templates live **inside** the Python package so hatchling includes them automatically.

## Critical Gotchas

**JinjaX (`jinjax>=0.41`):**
- API is `catalog.add_folder(path, prefix="Cf")` — NOT `add_path()`
- `class` is a Python reserved word in `{#def}` headers — use `extra_class` instead
- `content` kwarg is reserved by JinjaX (becomes the slot `CallerWrapper`) — call `catalog.render("CfCard", _content="body text")` for slot content; never use `content=` as a prop name
- `{#def}` defaults only work under JinjaX; plain Jinja2 treats `{#def}` as a comment — templates add `{% set x = x if x is defined else "" %}` guards for `StrictUndefined` compatibility

**django-cotton (2.x):**
- Use `<c-vars>` for variable declarations, NOT `<c-props>` — `<c-props>` was renamed in 2.x
- `COTTON_DIR` (singular, string) sets the component root directory, not `COTTON_DIRS`
- Unit tests using `render_to_string` bypass the django-cotton compiler — only E2E tests exercise real Cotton compilation
- Consumer Django projects must add `"libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"}` to `TEMPLATES[0]["OPTIONS"]` — the `cf_ui.django` app name prevents templatetag autodiscovery

**Django AppConfig:**
- Register as `"cf_ui.django.CfUiConfig"` (full class path), NOT `"cf_ui.django"` — `default_app_config` is removed in Django 4.2+

**Alpine.js:**
- `cf_ui_alpine.js` must load BEFORE the Alpine CDN (both use `defer` — DOM order guarantees execution sequence)
- Modal control uses `cf-modal-open` / `cf-modal-close` custom events dispatched to the element by ID — NOT `_x_dataStack` (private API)
- From a page, call `Alpine.store('cf').modal.open('modal-id')` — the `$store` shorthand is only available inside Alpine component expressions, not `page.evaluate()`

## Testing Strategy

Three tiers:

1. **Unit** (`tests/unit/`) — Jinja2 `Environment` (no browser) + `render_to_string` (no browser). Fast, no server needed. Does NOT exercise the django-cotton compiler.
2. **Integration** (`tests/integration/`) — FastAPI `TestClient` + Django test `Client`. Real HTTP, no browser.
3. **E2E** (`tests/e2e/`) — Playwright against live servers. Django E2E server runs as a subprocess with isolated settings to avoid Django singleton conflicts. Parameterized over `["js_on", "js_off"]`.

The Cotton unit tests pass even when cotton is not in INSTALLED_APPS (variables injected as raw context). Only E2E actually exercises `<c-vars>` compilation. Keep this in mind when debugging Cotton rendering issues.

## Component Naming Convention

| Template engine | Component syntax |
|---|---|
| JinjaX | `<CfCard>`, `<CfModal>`, `<CfFormField>` |
| django-cotton | `<c-cf.card>`, `<c-cf.modal>`, `<c-cf.form-field>` |

The `Cf` prefix / `cf.` namespace prevents collision with consumer app components. Theme is controlled by `CF_UI_THEME` (Django) or `theme=` argument (FastAPI/Litestar) — never in component names.

## Adding a New Theme

1. Create `src/cf_ui/templates/jinja/{theme}/` and `src/cf_ui/templates/cotton/{theme}/cf/`
2. Copy and adapt all 14 component templates, replacing Bulma-specific classes
3. Add the theme's CDN URL to `_CDN_CSS` in `templatetags/cf_ui.py` and to `assets.jinja`
4. Add default version to `_DEFAULTS` in `templatetags/cf_ui.py`
5. Add a stub `pyproject.toml` extras entry (already present as empty `[]`)
6. Add unit tests in `tests/unit/jinja/` and `tests/unit/cotton/`
