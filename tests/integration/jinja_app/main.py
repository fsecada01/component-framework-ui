from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinjax import Catalog

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.fastapi import install_cf_ui

_CF_UI_STATIC_DIR = JINJA_TEMPLATES_DIR.parent.parent / "static" / "cf_ui"

_THEME_CSS = {
    "bulma": "https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css",
    "daisy": "https://cdn.jsdelivr.net/npm/daisyui@4.7.2/dist/full.min.css",
    "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
}

# DaisyUI ships component classes but no Tailwind utilities. The components use
# utilities for layout and responsive behavior (`hidden`, `lg:flex`), so without
# a Tailwind build those classes resolve to nothing and the E2E tier cannot see
# whether a toggle actually changes anything. The play CDN is a real in-browser
# Tailwind JIT, which makes the gallery representative of a consuming app.
_THEME_EXTRA_HEAD = {
    "bulma": "",
    "daisy": '<script src="https://cdn.tailwindcss.com"></script>',
    # Bootstrap ships prebuilt CSS and cf-ui deliberately loads none of its
    # JavaScript — Alpine owns modal, tab and panel state in every theme.
    "bootstrap": "",
}


def make_app(theme: str = "bulma") -> FastAPI:
    """Build a JinjaX gallery app for one theme.

    Parameterized by theme so the E2E tier can run the same pages under both
    Bulma and DaisyUI — the component names and props are identical, which is
    the property being tested.
    """
    catalog = Catalog()
    install_cf_ui(catalog, theme=theme)

    app = FastAPI()
    app.mount("/static/cf_ui", StaticFiles(directory=str(_CF_UI_STATIC_DIR)), name="cf_ui_static")

    @app.get("/form-field", response_class=HTMLResponse)
    async def form_field():
        return catalog.render(
            "Cf:FormField",
            name="email",
            label="Email",
            value="",
            error="",
            type="email",
            required=False,
            extra_class="",
        )

    @app.get("/modal", response_class=HTMLResponse)
    async def modal():
        return catalog.render("Cf:Modal", id="test-modal", extra_class="")

    @app.get("/card", response_class=HTMLResponse)
    async def card():
        return catalog.render(
            "Cf:Card",
            _content="Card body",
            header="Card Title",
            footer="",
            extra_class="",
        )

    @app.get("/navbar", response_class=HTMLResponse)
    async def navbar():
        return catalog.render("Cf:Navbar", brand="", start="", end="", extra_class="")

    @app.get("/tabs", response_class=HTMLResponse)
    async def tabs():
        return catalog.render(
            "Cf:Tabs",
            tabs=[{"id": "one", "url": "/tab/one/"}, {"id": "two", "url": "/tab/two/"}],
            hx_target="tab-content",
            active="one",
            extra_class="",
        )

    @app.get("/gallery", response_class=HTMLResponse)
    async def gallery():
        # A header (so aria-labelledby has a target) and a focusable footer
        # control (so the focus trap has more than one stop to wrap between).
        modal_html = catalog.render(
            "Cf:Modal",
            id="e2e-modal",
            header="E2E Dialog",
            footer='<button type="button" id="modal-ok">OK</button>',
            extra_class="",
        )
        notification_html = catalog.render(
            "Cf:Notification", message="Hello!", type="info", dismissible=True, extra_class=""
        )
        navbar_html = catalog.render("Cf:Navbar", brand="Brand", start="", end="", extra_class="")
        panel_html = catalog.render(
            "Cf:Panel",
            id="e2e-panel",
            title="Accordion",
            _content="Hidden content",
            open=False,
            extra_class="",
        )
        # The no-JS case for `open`: this one must be readable with Alpine off.
        panel_open_html = catalog.render(
            "Cf:Panel",
            id="e2e-panel-open",
            title="Already open",
            _content="Visible content",
            open=True,
            extra_class="",
        )
        tabs_html = catalog.render(
            "Cf:Tabs",
            tabs=[{"id": "tab1", "url": "/tab/one/"}, {"id": "tab2", "url": "/tab/two/"}],
            hx_target="tab-content",
            active="tab1",
            _content="Initial content",
            extra_class="",
        )
        return f"""<!DOCTYPE html>
<html>
<head>
  {_THEME_EXTRA_HEAD[theme]}
  <link rel="stylesheet" href="{_THEME_CSS[theme]}">
  <style>[x-cloak] {{ display: none !important; }}</style>
</head>
<body>
  <section class="section">
    {navbar_html}
    <button id="open-modal" x-data @click="$store.cf.modal.open('e2e-modal')">Open Modal</button>
    {modal_html}
    {notification_html}
    {panel_html}
    {panel_open_html}
    {tabs_html}
  </section>
  <script src="/static/cf_ui/cf_ui_alpine.js" defer></script>
  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js" defer></script>
</body>
</html>"""

    return app


app = make_app("bulma")
