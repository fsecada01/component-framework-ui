# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

`component-framework-ui` (`cf-ui`) is a standalone PyPI package providing CSS framework component templates for [`component-framework`](https://github.com/fsecada01/component-framework). It ships two first-class template sets — Jinja2/JinjaX (FastAPI, Litestar) and django-cotton (Django) — for Bulma CSS, with stubs for Bootstrap, Foundation, Fomantic UI, and DaisyUI.

**Design principle:** `component-framework` stays renderer-agnostic. `cf-ui` is the opinionated UI layer. Component names are theme-agnostic (`<Cf:Card>`, `<c-cf.card>`) — switching CSS frameworks means changing `CF_UI_THEME` in one place.

## Commands

```bash
uv pip install -e ".[dev]"       # install with all dev deps
playwright install chromium       # install E2E browser

just test                         # unit tests only
just test-js                      # Tailwind plugin suite (node --test)
just axes                         # regenerate cf_ui_axes.css + cf_ui_axes.json
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
├── django.py                # AppConfig — validates CF_UI_THEME + CF_UI_COMPOSITION at startup
├── themes.py                # theme registry, cotton partial paths, Tailwind content globs
├── fastapi.py               # install_cf_ui(catalog, theme) — add_folder(prefix="Cf")
├── litestar.py              # install_cf_ui(config, theme) — appends to TemplateConfig.directory
├── templatetags/cf_ui.py    # Django simple_tags: cf_ui_head, cf_ui_body, get_item, make_list_1_to_n
├── templates/
│   ├── cf_ui/assets.jinja   # Jinja2 macros: cf_ui_head(), cf_ui_body()
│   ├── jinja/<theme>/       # 14 JinjaX component templates (*.jinja) per theme
│   ├── cotton/cf/           # 14 public wrappers — <c-cf.x>, props + dispatch only
│   └── cotton/_themes/<theme>/  # 14 theme partials (*.html), included by the wrappers
└── static/cf_ui/
    ├── cf_ui_alpine.js      # Alpine named components + $cf global store
    ├── cf_ui_axes.css       # GENERATED from axes.py
    ├── cf_ui_axes.json      # GENERATED from axes.py — read by the plugin below
    └── cf_ui_tailwind_plugin.mjs  # Tailwind plugin: build-time axis validation
```

Templates live **inside** the Python package so hatchling includes them automatically.

## Critical Gotchas

**JinjaX (`jinjax>=0.41`):**
- API is `catalog.add_folder(path, prefix="Cf")` — NOT `add_path()`
- Attributes do **not** interpolate: `header="{{ title }}"` reaches the component as literal braces, silently. Computed values need the colon binding, `:header="title"`. django-cotton is the opposite — `{{ }}` there is ordinary Django syntax. `tests/unit/test_docs_samples.py` fails the build on a braced `Cf:` attribute
- `Catalog(jinja_env=env)` does **not** convert `env` — it builds its own environment, copying extensions/globals across, and only writes `catalog` back into the one passed. To make a foreign environment (Litestar's) render component tags you must `env.add_extension(JinjaX)`, build the catalog over it, *and* bind `__prefix` as a global, or every tag raises `'__prefix' is undefined`. See `cf_ui/litestar.py`
- jinjax exports `Catalog`, **not** `ComponentCatalog` — the latter name does not exist and README documented it for two releases
- `Cf` is a JinjaX *prefix* and the prefix separator is `:` (jinjax's `PREFIX_SEP`; `DELIMITER` is `.` and is for subfolders) — so the tag is `<Cf:Card>` and the render name is `"Cf:Card"`. `<CfCard>` and `<Cf.Card>` both raise `ComponentNotFound`. `tests/unit/test_docs_samples.py` renders all three forms so the docs cannot drift back
- `class` is a Python reserved word in `{#def}` headers — use `extra_class` instead
- `content` kwarg is reserved by JinjaX (becomes the slot `CallerWrapper`) — call `catalog.render("Cf:Card", _content="body text")` for slot content; never use `content=` as a prop name
- Every cf-ui Jinja template escapes its own output via `{% autoescape true %}` (#36) — the block opens right after the `{#def}` header and closes at EOF; the installers never touch the environment's `autoescape`. A prop carrying real markup must be `markupsafe.Markup`. In `assets.jinja` the blocks live *inside* the macro bodies — a file-scope block stops the macros exporting
- `{#def}` defaults only work under JinjaX; plain Jinja2 treats `{#def}` as a comment — templates add `{% set x = x if x is defined else "" %}` guards for `StrictUndefined` compatibility

**django-cotton (2.x):**
- Use `<c-vars>` for variable declarations, NOT `<c-props>` — the rename landed in django-cotton **0.9.6**, not 2.x as this file long claimed. That is why the `[django]` extra floors at `>=2.0` (the tested series) and why `>=0.9` was a bug: it resolved 0.9.0–0.9.5, where the wrappers install and silently drop every prop (#47)
- `COTTON_DIR` (singular, string) sets the component root directory, not `COTTON_DIRS`
- Unit tests using `render_to_string` bypass the django-cotton compiler — only E2E tests exercise real Cotton compilation
- **The Django template language has no whitespace-control syntax.** Jinja's `{%- ... -%}` is a `TemplateSyntaxError` there (`Invalid block tag: '-'`), so a cotton partial that needs no stray whitespace has to keep the whole tag on one physical line
- **Django has no multi-line `{# #}` comment.** `{#` … `#}` is single-line only; open it on one line and close it on another and every line in between renders as literal text into the page. Use `{% comment %}…{% endcomment %}` for anything longer than one line
- `{% cf_ui_validate %}` (#52) is how a primitive wrapper rejects a bad prop. It returns `""`, so it must sit somewhere its output is *rendered* — inside `{% if %}` that never runs, or assigned via `as`, and the guard silently never fires
- Consumer Django projects must add `"libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"}` to `TEMPLATES[0]["OPTIONS"]` — the `cf_ui.django` app name prevents templatetag autodiscovery

**Django AppConfig:**
- Register as `"cf_ui.django.CfUiConfig"` (full class path), NOT `"cf_ui.django"` — `default_app_config` is removed in Django 4.2+

**Theme axes / Tailwind plugin:**
- `axes.py` is the single source of truth; `cf_ui_axes.css` **and** `cf_ui_axes.json`
  are build products of it. Edit `axes.py`, run `just axes`, commit both — drift
  tests fail otherwise
- The plugin holds no copy of the value sets, and a parity test compares its output
  against `render_axis_css` declaration by declaration. Never add value data to the
  `.mjs`
- The `.mjs` is vendored, so it may import **only** Node builtins — a bare
  `tailwindcss/plugin` import will not resolve from site-packages. It exports
  Tailwind's `{ handler, config }` shape by hand instead
- `node --test` runs as its own CI step because the pytest wrapper skips when node
  is absent, and a skip is not a pass

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
| JinjaX | `<Cf:Card>`, `<Cf:Modal>`, `<Cf:FormField>` |
| django-cotton | `<c-cf.card>`, `<c-cf.modal>`, `<c-cf.form-field>` |

The `Cf` prefix / `cf.` namespace prevents collision with consumer app components. Theme is controlled by `CF_UI_THEME` (Django) or `theme=` argument (FastAPI/Litestar) — never in component names.

## Adding a New Theme

1. Create `src/cf_ui/templates/jinja/{theme}/` and
   `src/cf_ui/templates/cotton/_themes/{theme}/`
2. Copy and adapt all 14 component templates, replacing Bulma-specific classes.
   The cotton partials carry **no** `<c-vars>` — that lives on the wrapper in
   `cotton/cf/`, which needs no edit for a new theme. Every Jinja template
   keeps its `{% autoescape true %}` block: it opens immediately **after** the
   `{#def}` header (wrapping the header breaks JinjaX prop detection) and
   closes at end of file. The drift guard in `tests/unit/test_autoescape.py`
   fails the build on a missing or misplaced block
3. Add `{theme}` to `THEMES` in `themes.py` — until then `resolve_theme` rejects
   it at startup
4. Add the theme's CDN URL to `_CDN_CSS` in `templatetags/cf_ui.py` and to
   `assets.jinja`
5. Add default version to `_DEFAULTS` in `templatetags/cf_ui.py`
6. Add a stub `pyproject.toml` extras entry (already present as empty `[]`)
7. Add unit tests in `tests/unit/jinja/` and `tests/unit/cotton/`; the
   parametrized tests in `tests/unit/test_theme_dispatch.py` pick the theme up
   automatically once step 3 lands

**Tailwind-based themes only:** write every variant class out in full
(`{% if type == 'danger' %}alert-error{% endif %}`) — Tailwind's scanner reads
source text, so `alert-{{ type }}` gets tree-shaken away silently. See
`tests/unit/test_tailwind_content.py` and `docs/daisyui.md`.
