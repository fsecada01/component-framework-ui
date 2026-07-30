"""The hostile tab id does not execute in a real browser (#32).

This is the tier that actually proves the fix. The unit tier can only assert
that the rendered attribute holds no splice point; it cannot show what the
browser does with one, because the whole mechanism depends on two things
pytest does not have — an HTML parser that decodes entity escapes while
building the DOM, and Alpine's expression evaluator reading the decoded value
back out.

The page is assembled here rather than served by the demo app on purpose: the
demo app should not grow a route whose job is to render a payload. The
templates, `cf_ui_alpine.js`, and the pinned Alpine build are the real ones.

Two assertions, and both are load-bearing:

* the payload did not run, and
* the bindings *did* evaluate — a fix that made Alpine throw on the expression
  would satisfy the first assertion while leaving the widget dead.
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

PACKAGE_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui"
JINJA_DIR = PACKAGE_DIR / "templates" / "jinja"
ALPINE_LOCAL = PACKAGE_DIR / "static" / "cf_ui" / "cf_ui_alpine.js"

#: Kept in step with `_DEFAULTS["alpinejs"]` in templatetags/cf_ui.py and the
#: `cf_ui_body` macro — testing against a different Alpine than the package
#: ships would be testing the wrong evaluator.
ALPINE_CDN = "https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"

THEMES = ["bulma", "daisy"]

#: Closes the string literal, runs, and reopens it, so the surrounding
#: expression still parses and Alpine reports no error. See the same constant
#: in tests/unit/test_alpine_expression_safety.py.
HOSTILE_ID = "');window.cfPwned=true;('"

PAGE = """<!doctype html>
<html>
<head>
<script>{alpine_local}</script>
<script src="{alpine_cdn}" defer></script>
</head>
<body>
{component}
</body>
</html>
"""


def _build_page(theme: str, tmp_path: Path) -> Path:
    env = Environment(
        loader=FileSystemLoader(JINJA_DIR / theme),
        autoescape=select_autoescape(["html", "jinja"]),
        undefined=StrictUndefined,
    )
    component = env.get_template("Tabs.jinja").render(
        tabs=[{"id": HOSTILE_ID, "url": "/x/"}, {"id": "safe", "url": "/safe/"}],
        hx_target="tc",
        active=HOSTILE_ID,
        content="",
        extra_class="",
    )
    assert "cfPwned" in component, "the hostile id never rendered — nothing to test"

    page = tmp_path / f"injection_{theme}.html"
    page.write_text(
        PAGE.format(
            alpine_local=ALPINE_LOCAL.read_text(encoding="utf-8"),
            alpine_cdn=ALPINE_CDN,
            component=component,
        ),
        encoding="utf-8",
    )
    return page


@pytest.mark.parametrize("theme", THEMES)
def test_a_hostile_tab_id_does_not_execute(page, tmp_path, theme):
    page.goto(_build_page(theme, tmp_path).as_uri())
    page.wait_for_function("() => window.Alpine !== undefined", timeout=15000)

    # The bindings have to have been evaluated before "it did not run" means
    # anything. aria-selected is computed by Alpine from the tab id it read out
    # of the data attribute, so a true here is proof the expression ran and
    # resolved the hostile id as a plain string.
    page.wait_for_function(
        "() => document.querySelector('[role=tab]').getAttribute('aria-selected') === 'true'",
        timeout=5000,
    )
    first_tab = page.locator('[role="tab"]').first
    assert first_tab.get_attribute("data-cf-tab") == HOSTILE_ID

    assert page.evaluate("() => window.cfPwned === true") is False, (
        "the tab id executed as JavaScript — it reached an Alpine expression as source"
    )
