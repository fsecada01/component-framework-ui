# Quickstart

Pick your web framework. Each path gets you to a page rendering a cf-ui
component with the theme's stylesheet attached.

Install first — see [Installation](installation.md).

## Django

### 1. Settings

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_cotton",
    "cf_ui.django.CfUiConfig",
]

CF_UI_THEME = "bulma"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"},
        },
    }
]
```

Two details that bite:

!!! danger "Register the AppConfig by its full class path"
    `"cf_ui.django.CfUiConfig"`, not `"cf_ui.django"`. Django 4.2 removed
    `default_app_config`, so the bare module path won't find the config class.

!!! danger "The `libraries` entry is not optional"
    cf-ui's app is named `cf_ui.django`, which stops Django's templatetag
    autodiscovery from finding `cf_ui/templatetags/`. Without the explicit
    `libraries` mapping, `{% load cf_ui %}` raises
    `TemplateSyntaxError: 'cf_ui' is not a registered tag library`.

`CfUiConfig` validates `CF_UI_THEME` (and `CF_UI_COMPOSITION`) at startup — a
typo fails the boot, not the first request.

### 2. Base template

```django
{# templates/base.html #}
{% load cf_ui %}
<!DOCTYPE html>
<html lang="en" {% cf_ui_root_attrs %}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {% cf_ui_head %}
</head>
<body>
  {% block content %}{% endblock %}
  {% cf_ui_body %}
</body>
</html>
```

`{% cf_ui_head %}` emits the theme stylesheet; `{% cf_ui_body %}` emits
`cf_ui_alpine.js` followed by the Alpine CDN, in that order — cf-ui's file
registers the components Alpine then initializes, so the order is load-bearing.

### 3. Use a component

```django
{# templates/home.html #}
{% extends "base.html" %}

{% block content %}
  <c-cf.card header="Welcome">
    Card body content here.
  </c-cf.card>

  <c-cf.notification message="Saved." type="success" />

  <c-cf.form-field name="email" label="Email" type="email"
                   value="{{ form.email.value|default:'' }}"
                   error="{{ form.email.errors.0|default:'' }}" />
{% endblock %}
```

Component names are `<c-cf.NAME>` where `NAME` is the kebab-case component
name — see [Components](components.md) for all fourteen.

## FastAPI

`install_cf_ui` registers cf-ui's templates on a JinjaX catalog under the `Cf`
prefix.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui

app = FastAPI()

catalog = Catalog()
install_cf_ui(catalog, theme="bulma")


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return catalog.render("Cf:Card", header="Welcome", _content="Card body.")
```

!!! danger "The class is `Catalog`"
    JinjaX exports `Catalog`. There is no `ComponentCatalog` — importing that
    name raises `ImportError`.

!!! note "`_content`, not `content`"
    `content` is reserved by JinjaX: as a keyword it becomes the slot wrapper,
    not a string. Pass slot content from Python as `_content=`. In a template
    the component's body fills the same slot, so `<Cf:Card>Body</Cf:Card>`
    needs no special casing.

### From your own templates

Add your template folder to the same catalog and render components with the
`Cf:` prefix:

```python
from pathlib import Path

catalog.add_folder(Path("templates"))
```

```jinja
{#def title="" #}
<Cf:Card :header="title">
  Card body content.
</Cf:Card>

<Cf:FormField name="email" label="Email" value="" extra_class="mb-4" />
```

!!! danger "Use `:prop=` to pass a value, not `prop="{{ }}"`"
    JinjaX does **not** interpolate `{{ … }}` inside an attribute — the braces
    arrive at the component as literal text, with no error. A plain
    `prop="text"` is a literal string; anything computed needs the colon
    binding: `:header="title"`, `:rows="6"`, `:options="plan_options"`.

!!! danger "The prefix separator is a colon"
    `<Cf:Card>`. Not `<CfCard>` and not `<Cf.Card>` — both raise
    `ComponentNotFound`. The same name works in
    `catalog.render("Cf:Card", ...)`.

### Assets

Mount cf-ui's static directory and pull the asset macros into your layout:

```python
from fastapi.staticfiles import StaticFiles

import cf_ui

app.mount(
    "/static/cf_ui",
    StaticFiles(directory=cf_ui.__path__[0] + "/static/cf_ui"),
    name="cf_ui_static",
)
```

```jinja
{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_body %}
{{ cf_ui_head(theme="bulma") }}
{{ cf_ui_body(theme="bulma", cf_alpine_url="/static/cf_ui/cf_ui_alpine.js") }}
```

## Litestar

`install_cf_ui` appends cf-ui's template directory to the config and chains an
engine callback that registers the theme-axis globals.

```python
from litestar import Litestar, get
from litestar.plugins.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig

from cf_ui.litestar import install_cf_ui

config = TemplateConfig(engine=JinjaTemplateEngine, directory="templates")
install_cf_ui(config, theme="bulma")


@get("/")
async def home() -> Template:
    return Template(template_name="home.html", context={"title": "Welcome"})


app = Litestar(route_handlers=[home], template_config=config)
```

!!! note "`JinjaTemplateEngine` moved in Litestar 2.22"
    It now lives at `litestar.plugins.jinja`. The old
    `litestar.contrib.jinja` path still works but warns, and goes away in
    Litestar 3.0.

Component tags work here exactly as they do on FastAPI. `install_cf_ui`
installs a JinjaX catalog onto Litestar's own Jinja2 environment, so ordinary
Litestar templates can use `<Cf:…>` directly:

```jinja
{# templates/home.html #}
{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_body %}
<!DOCTYPE html>
<html lang="en">
<head>{{ cf_ui_head(theme="bulma") }}</head>
<body>
  <Cf:Card :header="title">
    Card body content.
  </Cf:Card>

  <Cf:Notification message="Saved." type="success" />

  {{ cf_ui_body(theme="bulma") }}
</body>
</html>
```

!!! note "Litestar gained component rendering in 0.2.0"
    Before that, `<Cf:Card>` reached the browser as literal text and
    `{% from "cf_ui/assets.jinja" %}` raised `TemplateNotFound` — the
    installer registered neither a catalog nor the directory the macros live
    in. Both are fixed, and a live Litestar app now renders components in the
    integration suite.

## Next

- [Getting started](getting-started.md) — themes, axes, assets, and escaping in order.
- [Components](components.md) — every component and prop.
- [Use cases](use-cases.md) — worked examples with HTMX and Alpine.
