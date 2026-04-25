from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinjax import Catalog

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.fastapi import install_cf_ui

_CF_UI_STATIC_DIR = JINJA_TEMPLATES_DIR.parent.parent / "static" / "cf_ui"

catalog = Catalog()
install_cf_ui(catalog, theme="bulma")

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
        extra_class="",
    )


@app.get("/gallery", response_class=HTMLResponse)
async def gallery():
    modal_html = catalog.render("Cf:Modal", id="e2e-modal", extra_class="")
    notification_html = catalog.render(
        "Cf:Notification", message="Hello!", type="info", dismissible=True, extra_class=""
    )
    navbar_html = catalog.render("Cf:Navbar", brand="Brand", start="", end="", extra_class="")
    panel_html = catalog.render(
        "Cf:Panel", title="Accordion", _content="Hidden content", open=False, extra_class=""
    )
    tabs_html = catalog.render(
        "Cf:Tabs",
        tabs=[{"id": "tab1", "url": "/tab/one/"}, {"id": "tab2", "url": "/tab/two/"}],
        hx_target="tab-content",
        _content="Initial content",
        extra_class="",
    )
    return f"""<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css">
  <style>[x-cloak] {{ display: none !important; }}</style>
</head>
<body>
  <section class="section">
    {navbar_html}
    <button id="open-modal">Open Modal</button>
    {modal_html}
    {notification_html}
    {panel_html}
    {tabs_html}
  </section>
  <script src="/static/cf_ui/cf_ui_alpine.js" defer></script>
  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js" defer></script>
</body>
</html>"""
