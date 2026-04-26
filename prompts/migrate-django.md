# cf-ui Django Migration Guide

You are a migration agent. Your job is to migrate a Django project to use `cf-ui` components. Follow the phases below in order. Do not skip Phase 1 — the project context it surfaces determines everything that follows.

---

## Phase 1: Understand the project

Before writing a single line of code, read the project's own documentation and explore its templates.

**Step 1 — Read `CLAUDE.md`** (or `README.md` if no CLAUDE.md exists). Extract:
- Framework versions (Django, django-cotton, Alpine.js if any)
- CSS setup — is Bulma loaded from CDN or compiled from source SCSS?
- Any existing component patterns mentioned
- Test commands

**Step 2 — Explore existing templates.** Find all template directories and read a representative sample:
- The base layout template (look for `base.html`, `layouts/base.html`, `cotton/layouts/base.html`)
- Any existing cotton component templates (directories named `cotton/`)
- How CSS and JS assets are currently loaded (look for `<link>` and `<script>` tags or asset snippets)
- Forms — how are they rendered? (crispy forms, manual fields, cotton components?)
- Any existing notification, modal, card, table, or navbar patterns

**Step 3 — Identify Alpine.js status.** Is Alpine already loaded? Is there vanilla JS doing what Alpine would handle (e.g., navbar burger toggles, modal open/close)?

**Step 4 — Check `component-framework` version.** cf-ui depends on `component-framework>=0.4`. Run:
```bash
pip show component-framework
```
If not installed or below 0.4, install from GitHub:
```bash
pip install "git+https://github.com/fsecada01/component-framework.git"
```

After Phase 1, write a short summary of what you found before proceeding.

---

## Phase 2: Assess migration candidates

Based on what you discovered, categorise the existing templates:

**Good candidates for cf-ui** — generic Bulma UI patterns that cf-ui already covers:
- Inline notification divs (`<div class="notification is-...">`)
- Django messages framework snippets
- Modals (especially any using legacy Semantic UI or bare Bulma `<div class="modal">`)
- Progress bars (`<progress class="progress ...">`)
- Paginated list views
- Tables with sorting or pagination
- Panels / collapsible sections
- Navbar burger toggle (if using vanilla JS)

**Leave alone** — project-specific components with custom styling or logic:
- Components using custom CSS class naming (e.g., BEM `.project-*` classes)
- Components driven by a design system with its own tokens and overrides
- Forms rendered by crispy-forms or a form library (replacing these requires reworking field rendering, not just markup)
- Any component that is already a well-maintained cotton component doing something cf-ui doesn't cover

Write a prioritised list of candidates before proceeding. Confirm with the user if anything is unclear.

---

## Phase 3: Apply settings changes

These steps apply to every Django project. Confirm each before moving to migration.

**1. Install cf-ui:**
```bash
pip install "cf-ui[bulma]"
# Add to requirements.txt / pyproject.toml as appropriate
```

**2. Add to `INSTALLED_APPS`:**
```python
"cf_ui.django.CfUiConfig",  # use the full class path, not just "cf_ui.django"
```

**3. Set theme:**
```python
CF_UI_THEME = "bulma"
```

**4. Register the template tag library** (required — autodiscovery doesn't work because the app name is `cf_ui.django`):
```python
TEMPLATES = [{
    ...
    "OPTIONS": {
        "libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"},
    },
}]
```

**5. Asset loading — read the project's CSS setup first:**

- **If Bulma is loaded from CDN** (a bare `<link href="...bulma...cdn...">` in the base template): replace it with `{% cf_ui_head %}`, which outputs the Bulma CDN link plus the `[x-cloak]` style.
- **If Bulma is compiled from source SCSS** with custom variables or brand overrides: do **not** call `{% cf_ui_head %}` — it would load a second, conflicting stylesheet. Only call `{% cf_ui_body %}` for Alpine.
- **In both cases**, add `{% cf_ui_body %}` before `</body>` in the base template to load `cf_ui_alpine.js` + Alpine CDN.

```django
{# In the base template #}
{% load cf_ui %}
...
{% cf_ui_body %}  {# loads cf_ui_alpine.js + Alpine CDN #}
</body>
```

**6. Verify Alpine is loading.** Open the app in a browser and confirm `window.Alpine` is defined in the console before proceeding with interactive components.

---

## Phase 4: Migrate components

Work through your prioritised list one component at a time. For each:

1. Read the existing template in full
2. Identify the equivalent cf-ui component from the reference below
3. Write the replacement, preserving all data bindings, HTMX attributes, and CSS modifiers
4. Run the test suite
5. Visually verify in a browser
6. Commit

---

## cf-ui component reference

### Critical gotchas

| Gotcha | Detail |
|---|---|
| `extra_class` not `class` | All cf-ui components use `extra_class` for the root element — `class` is reserved in JinjaX `{#def}` headers |
| `input_class` for inner elements | FormField, Select, Textarea accept `input_class` for the `<input>`/`<select>`/`<textarea>` element; CheckboxGroup accepts `control_class` for the `<div class="control">` |
| `<c-vars>` not `<c-props>` | django-cotton 2.x renamed the declaration tag — cf-ui uses `<c-vars>` throughout |
| Alpine required for interactive components | Modal, Notification (dismissible), Panel, Navbar burger, Tabs all need Alpine. Confirm `{% cf_ui_body %}` is in the base template before migrating these |
| Modal control via Alpine store | Trigger a modal from outside: `Alpine.store('cf').modal.open('modal-id')`. Works only after Alpine has initialised |

### Notification

```html
{# Before — common patterns #}
<div class="notification is-danger is-light">{{ error }}</div>
<div class="notification is-info">{{ message }}</div>

{# After #}
<c-cf.notification message="{{ error }}" type="danger" dismissible="false" />
<c-cf.notification message="{{ message }}" type="info" dismissible="true" />
```

Supported types: `info`, `success`, `warning`, `danger`. `dismissible="true"` adds an Alpine-driven close button.

### Modal

```html
{# After #}
<c-cf.modal id="my-modal">
    <c-slot name="header">Dialog Title</c-slot>
    Modal body content here.
    <c-slot name="footer">
        <button class="button" @click="close()">Cancel</button>
        <button class="button is-primary" @click="close()">Confirm</button>
    </c-slot>
</c-cf.modal>

{# Trigger from anywhere once Alpine is loaded #}
<button @click="Alpine.store('cf').modal.open('my-modal')">Open</button>
```

### Progress

```html
{# Before #}
<progress class="progress is-primary" value="60" max="100">60%</progress>

{# After #}
<c-cf.progress value="60" max="100" type="primary" />
<c-cf.progress value="{{ pct }}" max="1" type="{{ bar_type }}" label="Resume Fit" extra_class="is-small" />
```

### Card

```html
{# After #}
<c-cf.card>
    <c-slot name="header">Card Title</c-slot>
    Card body content.
    <c-slot name="footer">
        <a class="button is-primary is-small">Action</a>
    </c-slot>
</c-cf.card>
```

### Table

```html
{# After — columns is a list of {key, label} dicts; rows is a list of dicts #}
<c-cf.table columns="{{ columns }}" rows="{{ rows }}"
             hx_url="{% url 'my-list-view' %}" hx_target="#list-container" />
```

### Pagination

```html
{# After #}
<c-cf.pagination page="{{ page_obj.number }}"
                 total_pages="{{ page_obj.paginator.num_pages }}"
                 hx_url="{% url 'my-list-view' %}"
                 hx_target="#list-container" />
```

`hx_url` and `hx_target` are optional. Without them, links render without `hx-get` attributes (plain `<a>` tags with no HTMX).

### Panel (collapsible)

```html
{# After #}
<c-cf.panel title="Advanced Filters" open="false">
    Filter content here.
</c-cf.panel>
```

### Form fields

Use only when rendering fields manually (not via crispy-forms or a form library). If the project uses crispy-forms, leave it — replacing crispy with cf-ui form fields requires reworking every form's rendering logic, which is outside the scope of a cf-ui migration.

```html
{# After — manual field rendering #}
<c-cf.form-field name="email" label="Email"
                 value="{{ form.email.value|default:'' }}"
                 error="{{ form.email.errors.0|default:'' }}"
                 type="email" />
```

### Navbar burger

Migrate only if the project uses vanilla JS to toggle the burger. If already using Alpine or another reactive approach, leave it.

```html
{# After — add x-data="cfNavbar" to the <nav> element #}
<nav class="navbar" x-data="cfNavbar">
    <div class="navbar-brand">
        ...
        <a class="navbar-burger" @click="toggle()" :class="{ 'is-active': menuOpen }">
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
        </a>
    </div>
    <div class="navbar-menu" :class="{ 'is-active': menuOpen }">
        ...
    </div>
</nav>
```

Remove any vanilla JS that was doing the same toggle.

---

## Verification checklist

Run after completing all migrations:

- [ ] Django test suite passes
- [ ] No JavaScript console errors on page load
- [ ] `window.Alpine` is defined in browser console
- [ ] Notifications render correctly and dismiss (if dismissible)
- [ ] Modal opens via `Alpine.store('cf').modal.open(id)` and closes via the delete button
- [ ] Pagination links fire correctly (HTMX swap or full page reload as intended)
- [ ] Navbar burger toggles the menu on mobile viewport
- [ ] No duplicate Bulma stylesheets loaded (check Network tab)
