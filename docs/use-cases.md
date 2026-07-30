# Use cases

Worked examples. Each shows the component wiring, not a full application.

## A server-rendered form with validation errors

Every form component takes `error` and renders the theme's error state when it
is non-empty. Pass the first error from your form object and you are done —
there is no separate "invalid" flag to keep in sync.

=== "Django"

    ```django
    <form method="post">
      {% csrf_token %}

      <c-cf.form-field name="email" label="Email" type="email" required="True"
                       value="{{ form.email.value|default:'' }}"
                       error="{{ form.email.errors.0|default:'' }}" />

      <c-cf.select name="plan" label="Plan"
                   value="{{ form.plan.value|default:'' }}"
                   error="{{ form.plan.errors.0|default:'' }}"
                   :options="plan_options" />

      <c-cf.textarea name="notes" label="Notes" rows="6"
                     value="{{ form.notes.value|default:'' }}"
                     error="{{ form.notes.errors.0|default:'' }}" />

      <c-cf.checkbox-group name="topics" label="Interests"
                           :choices="topic_choices"
                           :selected="form.topics.value"
                           error="{{ form.topics.errors.0|default:'' }}" />

      <button type="submit" class="button is-primary">Save</button>
    </form>
    ```

    Cotton's `:` prefix passes a Python object rather than a string — use it
    for `options`, `choices`, and `selected`, which are lists of mappings.

=== "FastAPI / JinjaX"

    ```jinja
    {#def form_values={}, errors={} #}
    <form method="post">
      <Cf:FormField name="email" label="Email" type="email" required="{{ True }}"
                    value="{{ form_values.get('email', '') }}"
                    error="{{ errors.get('email', '') }}" />

      <Cf:Select name="plan" label="Plan"
                 value="{{ form_values.get('plan', '') }}"
                 error="{{ errors.get('plan', '') }}"
                 :options="plan_options" />

      <Cf:Textarea name="notes" label="Notes" rows="{{ 6 }}"
                   value="{{ form_values.get('notes', '') }}"
                   error="{{ errors.get('notes', '') }}" />

      <button type="submit" class="button is-primary">Save</button>
    </form>
    ```

The option and choice shapes:

```python
plan_options = [
    {"value": "free", "label": "Free"},
    {"value": "pro", "label": "Pro"},
]
topic_choices = [
    {"value": "python", "label": "Python"},
    {"value": "css", "label": "CSS"},
]
```

## An HTMX-driven table with pagination

`Cf:Table` and `Cf:Pagination` both take `hx_target` and `hx_url`, so sorting
and paging swap the same region without a page reload.

=== "Django"

    ```django
    <div id="results">
      <c-cf.table :columns="columns" :rows="rows"
                  hx_target="#results" hx_url="{% url 'jobs:list' %}" />

      <c-cf.pagination page="{{ page.number }}"
                       total_pages="{{ page.paginator.num_pages }}"
                       hx_target="#results" hx_url="{% url 'jobs:list' %}" />
    </div>
    ```

=== "FastAPI / JinjaX"

    ```jinja
    {#def columns=[], rows=[], page=1, total_pages=1 #}
    <div id="results">
      <Cf:Table :columns="columns" :rows="rows"
                hx_target="#results" hx_url="/jobs/" />

      <Cf:Pagination :page="page" :total_pages="total_pages"
                     hx_target="#results" hx_url="/jobs/" />
    </div>
    ```

The view returns the same partial for both the full page and the HTMX request;
HTMX replaces `#results` with the response. `columns` is a list of column
keys/labels and `rows` a list of mappings keyed by those columns:

```python
columns = ["title", "company", "posted"]
rows = [
    {"title": "Backend Engineer", "company": "Acme", "posted": "2026-07-14"},
    {"title": "Platform Engineer", "company": "Globex", "posted": "2026-07-20"},
]
```

## A confirmation modal

Declare the modal once, then open it from anywhere by id.

=== "Django"

    ```django
    <c-cf.modal id="confirm-delete" header="Delete this record?"
                label="Confirm deletion">
      This cannot be undone.
      <c-slot name="footer">
        <button class="button is-danger"
                hx-delete="{% url 'jobs:delete' job.pk %}"
                hx-target="#results">Delete</button>
      </c-slot>
    </c-cf.modal>

    <button @click="Alpine.store('cf').modal.open('confirm-delete')">
      Delete
    </button>
    ```

=== "FastAPI / JinjaX"

    ```jinja
    {#def job_id=0 #}
    <Cf:Modal id="confirm-delete" header="Delete this record?"
              label="Confirm deletion"
              footer="{{ footer_markup }}">
      This cannot be undone.
    </Cf:Modal>

    <button @click="Alpine.store('cf').modal.open('confirm-delete')">
      Delete
    </button>
    ```

Focus moves into the dialog on open, is trapped while it is open, and returns
to the trigger on close. `Escape` closes. None of that is per-theme —
it lives in `cf_ui_alpine.js`, so it behaves identically under Bootstrap and
Bulma. See [Accessibility](accessibility.md).

!!! note "Modal control is by custom event, not Alpine internals"
    `Alpine.store('cf').modal.open(id)` dispatches `cf-modal-open` to the
    element with that id. Do not reach for `_x_dataStack` — it is a private
    Alpine API and cf-ui deliberately does not depend on it.

## Toast notifications from anywhere

```html
<button @click="$store.cf.notify('Profile saved.', 'success')">Save</button>
```

`type` accepts `info`, `success`, `warning`, `danger` — the same values
`Cf:Notification` takes, so a server-rendered notification and a
JavaScript-triggered one look identical.

For a server-rendered one:

```django
{% for message in messages %}
  <c-cf.notification message="{{ message }}" type="{{ message.tags }}" />
{% endfor %}
```

## Tabs that load their panels over HTMX

```django
<c-cf.tabs :tabs="tabs" active="overview" hx_target="tab-content" />
<div id="tab-content">
  {% include "jobs/_overview.html" %}
</div>
```

```python
tabs = [
    {"id": "overview", "url": "/jobs/1/overview/"},
    {"id": "history", "url": "/jobs/1/history/"},
]
```

Arrow keys move between tabs with a roving tabindex; the active tab carries
`aria-selected`. Panels are fetched on demand and swapped into `hx_target`.

## Passing real markup into a prop

Props are escaped. When the value genuinely is markup, mark it:

=== "Python / JinjaX"

    ```python
    from markupsafe import Markup

    catalog.render(
        "Cf:Notification",
        message=Markup('Saved. <a href="/undo/">Undo</a>'),
        type="success",
    )
    ```

=== "Django"

    ```python
    from django.utils.safestring import mark_safe

    context = {"message": mark_safe('Saved. <a href="/undo/">Undo</a>')}
    ```

A plain string renders the tags as visible text. That is the safe default
working, not a bug — [Escaping](escaping.md) explains why there is no flag to
turn it off, and how to shadow a template when you need one component to
behave differently.

## Switching themes

Change one line and redeploy:

```python
CF_UI_THEME = "bootstrap"   # was "bulma"
```

No template in your application changes, because no template names a theme.
What *does* change is the stylesheet `{% cf_ui_head %}` emits and the classes
the partials produce.

Two things to check when you switch:

- **Utility classes you wrote yourself.** `class="button is-primary"` is
  Bulma's spelling. cf-ui's components adapt; your own markup does not.
- **Tailwind content globs**, if you are moving to or from `daisy` — see
  [DaisyUI](daisyui.md).
