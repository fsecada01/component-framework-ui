from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinjax import Catalog
from markupsafe import Markup

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.fastapi import install_cf_ui

_TEMPLATES_ROOT = JINJA_TEMPLATES_DIR.parent  # .../cf_ui/templates
_CF_UI_STATIC_DIR = _TEMPLATES_ROOT.parent / "static" / "cf_ui"

# The gallery's `<head>` is built through the real `cf_ui_head` macro rather
# than a hand-maintained CDN URL table — see #56. It used to hand-roll its
# own `_THEME_CSS` dict plus a `_THEME_EXTRA_HEAD["daisy"]` patch that
# injected the Tailwind Play CDN script cf_ui_head itself failed to emit,
# which meant this E2E tier was never exercising the shipped tag, only a
# workaround for it. Routing through the actual macro is what makes deleting
# that patch a real regression guard instead of a hope.
_assets_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_ROOT)),
    autoescape=select_autoescape(["html", "jinja"]),
)
_assets_module = _assets_env.get_template("cf_ui/assets.jinja").make_module()


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
            # Wrapped since #36: cf-ui templates escape their own output now,
            # so a prop carrying real markup has to say so. Without this the
            # button renders as text and the focus-trap and backdrop E2E tests
            # lose the control they reach for — which is the migration this
            # release asks of consumers, demonstrated on cf-ui's own gallery.
            # The cotton gallery never needed it: Django has always
            # autoescaped, so it passes plain text here.
            footer=Markup('<button type="button" id="modal-ok">OK</button>'),
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
        head_html = _assets_module.cf_ui_head(
            theme=theme, cf_axes_url="/static/cf_ui/cf_ui_axes.css"
        )
        return f"""<!DOCTYPE html>
<html>
<head>
  {head_html}
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
