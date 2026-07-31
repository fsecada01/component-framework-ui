"""Litestar renders cf-ui components over real HTTP (#42).

Before this file, Litestar's only coverage was ``MagicMock`` unit tests
asserting that ``install_cf_ui`` appended a path and set a callback. A mock
cannot render, so both halves of the integration were broken in a way no test
could see:

* ``<Cf:Card>`` reached the browser as **literal text** — no exception, no
  output. ``Catalog(jinja_env=env)`` builds its own environment rather than
  converting the one it is given, so Litestar's environment never learned the
  component tag.
* ``{% from "cf_ui/assets.jinja" import ... %}`` raised ``TemplateNotFound``,
  because the installer put only ``templates/jinja/<theme>`` on the search
  path while the macros live at ``templates/cf_ui/``.

Both were documented as working. These tests run a real Litestar app through
its real template engine, which is the only thing that would have caught it.
"""

import pytest

litestar = pytest.importorskip("litestar")

from litestar import get  # noqa: E402
from litestar.plugins.jinja import JinjaTemplateEngine  # noqa: E402
from litestar.response import Template  # noqa: E402
from litestar.template.config import TemplateConfig  # noqa: E402
from litestar.testing import create_test_client  # noqa: E402

from cf_ui.litestar import install_cf_ui  # noqa: E402

HOSTILE = '" onmouseover="window.cfPwned=true" x="'


def _app_client(tmp_path, page: str, **context):
    """A live Litestar app rendering ``page`` through the real Jinja engine."""
    (tmp_path / "page.html").write_text(page, encoding="utf-8")

    config = TemplateConfig(engine=JinjaTemplateEngine, directory=[tmp_path])
    install_cf_ui(config, theme="bulma")

    @get("/")
    async def home() -> Template:
        return Template(template_name="page.html", context=dict(context))

    return create_test_client(route_handlers=[home], template_config=config)


def test_a_component_tag_renders(tmp_path):
    """The defect: this used to return the tag as text, with a 200 status."""
    with _app_client(
        tmp_path, '<h1>{{ title }}</h1><Cf:Card header="Card title">Body text</Cf:Card>'
    ) as client:
        html = client.get("/").text

    assert "<Cf:Card" not in html, "the component tag was emitted as literal text"
    assert 'class="card' in html
    assert "Card title" in html
    assert "Body text" in html


def test_a_self_closing_component_tag_renders(tmp_path):
    with _app_client(tmp_path, '<Cf:Notification message="Saved." type="success" />') as client:
        html = client.get("/").text

    assert "<Cf:Notification" not in html
    assert "Saved." in html
    assert "notification" in html


def test_the_assets_macros_resolve(tmp_path):
    """``TemplateNotFound`` before #42 — the macros are a sibling of jinja/."""
    page = (
        '{% from "cf_ui/assets.jinja" import cf_ui_head, cf_ui_body %}'
        "{{ cf_ui_head(theme='bulma') }}|{{ cf_ui_body(theme='bulma') }}"
    )
    with _app_client(tmp_path, page) as client:
        response = client.get("/")

    assert response.status_code == 200
    head, body = response.text.split("|")
    assert "bulma" in head and "stylesheet" in head
    assert "cf_ui_alpine.js" in body or "alpine" in body.lower()


def test_a_hostile_prop_is_escaped_on_the_litestar_path(tmp_path):
    """#36 has to hold here too, and Litestar does not enable autoescaping.

    This is the configuration the in-template blocks exist for: the component
    renders through an environment whose ``autoescape`` cf-ui never touched.

    Note the ``:header=`` binding. In JinjaX ``header="{{ evil }}"`` does *not*
    interpolate — the braces arrive at the component as literal text — so the
    obvious spelling would have made this test pass while proving nothing.
    """
    with _app_client(tmp_path, '<Cf:Card :header="evil">body</Cf:Card>', evil=HOSTILE) as client:
        html = client.get("/").text

    assert 'onmouseover="window.cfPwned=true"' not in html
    assert "&#34;" in html or "&quot;" in html


def test_the_axis_globals_are_registered(tmp_path):
    with _app_client(tmp_path, "<html {{ cf_ui_axis_attrs() }}>") as client:
        html = client.get("/").text

    assert 'data-accent="' in html
    assert "&#34;" not in html, "the axis attrs must stay Markup, not be escaped"


def test_a_theme_other_than_the_default_renders(tmp_path):
    """Guards against the theme argument being ignored on this path."""
    (tmp_path / "page.html").write_text('<Cf:Card header="T">b</Cf:Card>', encoding="utf-8")

    config = TemplateConfig(engine=JinjaTemplateEngine, directory=[tmp_path])
    install_cf_ui(config, theme="bootstrap")

    @get("/")
    async def home() -> Template:
        return Template(template_name="page.html")

    with create_test_client(route_handlers=[home], template_config=config) as client:
        html = client.get("/").text

    # Bootstrap's card markup, not Bulma's card-header-title.
    assert "card-header" in html
    assert "card-header-title" not in html
