# Changelog

## [0.1.1] — 2026-04-28

### Fixed
- **Consumer compatibility regression**: `CfUiConfig.ready()` no longer
  overrides `settings.COTTON_DIR`. The previous fix in 0.1.0 set
  `COTTON_DIR="cotton/bulma"` globally, which broke any consumer project
  whose own cotton templates lived at `templates/cotton/<their-app>/...`
  (every `<c-foo.bar>` lookup got rewritten to
  `cotton/bulma/foo/bar/index.html` and raised `TemplateDoesNotExist`).

### Changed
- cf-ui's cotton templates moved from `cotton/<theme>/cf/*.html` to
  `cotton/cf/*.html`. Theme variation will now happen inside the templates
  (or via `_themes/` partials) instead of at the directory level. With the
  default `COTTON_DIR="cotton"`, `<c-cf.foo>` continues to resolve and
  consumer cotton trees are no longer affected.

### Migration
- Most consumers: no change required. Removing any explicit
  `COTTON_DIR="cotton/bulma"` from `settings.py` (added as a workaround
  while 0.1.0 was broken) is recommended.
- If you imported `COTTON_TEMPLATES_DIR / "bulma"` directly via the escape
  hatch, switch to `COTTON_TEMPLATES_DIR / "cf"`.

## [0.1.0] — 2026-04-25

### Added
- Initial release: Bulma theme (Jinja2/JinjaX + django-cotton)
- 14 components: FormField, Select, Textarea, CheckboxGroup, Modal, Notification,
  Progress, Card, Table, Pagination, Panel, Navbar, Breadcrumb, Tabs
- Django AppConfig with auto-registration of COTTON_DIRS
- FastAPI `install_cf_ui()` with JinjaX `add_folder(prefix="Cf")` registration
- Litestar `install_cf_ui()` with Jinja2 template directory injection
- CDN asset tags: `{% cf_ui_head %}` / `{% cf_ui_body %}` (Django + Jinja2 macros)
- `cf_ui_alpine.js`: named Alpine components (cfModal, cfNavbar, cfPanel, cfTabs)
  and `$store.cf` global store (notify, modal.open/close via custom events)
- Three-tier test suite: unit (93 tests), integration (8 tests), E2E Playwright (17 tests, js_on + js_off)
- Stubs for Bootstrap, Foundation, Fomantic UI, DaisyUI themes

### Technical Notes
- django-cotton 2.x: uses `<c-vars>` (not `<c-props>`) for variable declarations
- JinjaX 0.41+: uses `add_folder()` (not `add_path()`), `class` is reserved — use `extra_class`
- Alpine modal control uses `cf-modal-open`/`cf-modal-close` custom events (not `_x_dataStack`)
