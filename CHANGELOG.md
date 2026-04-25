# Changelog

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
