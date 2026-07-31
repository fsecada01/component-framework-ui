# Installation

## Requirements

- Python 3.11+
- `component-framework >= 0.4`
- Pydantic 2.0+ — the only mandatory runtime dependency

Everything else is an extra, selected by the web framework you use and the CSS
framework you render.

## Install

```bash
pip install "cf-ui[bulma]"
```

The theme extras are markers, not payloads — **every template set ships in
every install**. `cf-ui[bulma]` and `cf-ui[bootstrap]` install identical
files; the extra records intent, and theme selection happens at runtime.

| Extra | Pulls in |
|---|---|
| `[bulma]` `[bootstrap]` `[foundation]` `[fomantic]` `[daisy]` | nothing — theme markers |
| `[django]` | Django 4.2+, django-cotton 2.0+ |
| `[fastapi]` | FastAPI 0.109+, JinjaX 0.41+, uvicorn, python-multipart |
| `[litestar]` | Litestar 2.0+, Jinja2 3.1+, JinjaX 0.41+ |
| `[all]` | every theme marker plus all three web-framework extras |

You want at least one web-framework extra, because that is where the real
dependencies live:

```bash
pip install "cf-ui[django,bulma]"        # Django + Bulma
pip install "cf-ui[fastapi,daisy]"       # FastAPI + Tailwind/DaisyUI
pip install "cf-ui[litestar,bootstrap]"  # Litestar + Bootstrap 5
```

With `uv`:

```bash
uv add "cf-ui[django,bulma]"
```

## CSS and JS assets

cf-ui renders markup; the CSS framework itself is loaded separately. Two
options:

**CDN, via the asset tags.** `{% cf_ui_head %}` and `{% cf_ui_body %}` inject
pinned CDN links for the active theme plus Alpine.js. See
[Quickstart](quickstart.md) for placement and
[Getting started](getting-started.md#3-assets) for the version-pinning knob.

**Self-hosted.** Don't call the tags; load the framework yourself. cf-ui has no
opinion about where the stylesheet comes from — only that the class names it
emits are the ones that stylesheet defines.

!!! warning "DaisyUI needs one extra step"
    DaisyUI compiles through Tailwind, so Tailwind's content scanner has to
    reach cf-ui's templates inside `site-packages` — otherwise every class is
    tree-shaken away, leaving correct markup with no styling and no error.
    Get the glob from the package rather than hand-writing it:

    ```bash
    python -m cf_ui.themes
    ```

    [DaisyUI](daisyui.md) covers that in full, along with the Tailwind plugin
    that fails your build on an unknown theme-axis value.

## Verify the install

```python
import cf_ui

print(cf_ui.__version__)
print(cf_ui.JINJA_TEMPLATES_DIR)
print(cf_ui.COTTON_TEMPLATES_DIR)
```

Both directories live inside the installed package. If they don't exist, the
wheel was built without its template data and no amount of configuration will
help.

## Development install

```bash
git clone https://github.com/fsecada01/component-framework-ui
cd component-framework-ui
uv pip install -e ".[dev]"
playwright install chromium
```

```bash
just test              # unit tests
just test-integration  # real HTTP, no browser
just test-e2e          # Playwright, needs chromium
just test-all          # everything
just lint              # ruff check
just docs              # serve this site at localhost:8000
```
