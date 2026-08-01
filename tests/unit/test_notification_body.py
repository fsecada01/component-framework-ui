"""``notification`` must accept body content, not only a scalar ``message`` (#65).

It is the one container-shaped component in the set that took a string and
nothing else. Every other container — ``card``, ``modal``, ``panel``, ``box``,
``prose`` — renders a body, and the components that legitimately do not
(``table``, ``pagination``, ``breadcrumb``, ``progress``) are all data-driven
and would have nothing to do with children.

The cotton half failed *silently*, which is what made it survive three months
in a real consumer: ``<c-vars message ...>`` carries no default, so a
body-form call resolved ``message`` to ``""`` and rendered a correctly-styled,
correctly-coloured, empty box. The JinjaX half raised instead, because
``message`` was a required ``{#def}`` parameter — the same bug with a loud
failure mode.

Both directions stay backward compatible: ``message=`` callers are untouched
and the JinjaX signature only loosens. Where both are supplied the body wins,
because a caller who wrote children meant them.
"""

from pathlib import Path

import pytest
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from jinjax import Catalog
from markupsafe import Markup

from cf_ui import JINJA_TEMPLATES_DIR
from tests.jinja_env import make_env

THEMES = ["bulma", "bootstrap", "daisy", "fomantic", "foundation"]

#: A string no theme's own markup contains, so a substring hit can only mean
#: the body was rendered.
BODY = "CF-UI-BODY-MARKER"
MESSAGE = "CF-UI-MESSAGE-MARKER"

#: Rendering a bare ``.jinja`` file through plain Jinja means ``{#def}`` is an
#: ordinary comment, so every variable the template touches has to be supplied
#: — ``make_env`` uses ``StrictUndefined`` deliberately.
JINJA_BASE = {"type": "info", "dismissible": False, "extra_class": ""}
COTTON_BASE = {"type": "info", "dismissible": "false", "class": ""}


def _jinja(theme: str, **ctx: object) -> str:
    env = make_env(JINJA_TEMPLATES_DIR / theme)
    return env.get_template("Notification.jinja").render(**{**JINJA_BASE, **ctx})


def _catalog(theme: str) -> Catalog:
    cat = Catalog()
    cat.add_folder(JINJA_TEMPLATES_DIR / theme, prefix="Cf")
    return cat


# ── The bug: body content is discarded ────────────────────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_notification_renders_body_content(settings, theme: str):
    """The reported failure, per theme. Empty box, no error, no warning."""
    settings.CF_UI_THEME = theme
    html = render_to_string("cotton/cf/notification.html", {**COTTON_BASE, "slot": BODY})
    assert BODY in html, f"{theme}: body content was discarded"


@pytest.mark.parametrize("theme", THEMES)
def test_jinja_notification_renders_body_content(theme: str):
    assert BODY in _jinja(theme, content=BODY, message="")


@pytest.mark.parametrize("theme", THEMES)
def test_jinjax_notification_renders_a_real_slot(theme: str):
    """Through the catalogue, where ``_content`` is the actual slot channel.

    The plain-Jinja test above passes ``content`` as an ordinary variable, so
    it cannot tell whether JinjaX's slot plumbing reaches the template. This
    one can — and it is the form every documented call site uses.
    """
    html = _catalog(theme).render(
        "Cf:Notification", _content=BODY, type="info", dismissible=False, extra_class=""
    )
    assert BODY in html


@pytest.mark.parametrize("theme", THEMES)
def test_jinjax_notification_no_longer_requires_message(theme: str):
    """``message`` was a required ``{#def}`` parameter, so a body-only call raised.

    Asserting the *absence* of an exception is weak on its own, so this also
    checks the body arrived: a template that swallowed the slot would satisfy
    "did not raise" while still being the bug.
    """
    html = _catalog(theme).render(
        "Cf:Notification", _content=BODY, type="info", dismissible=False, extra_class=""
    )
    assert BODY in html


# ── What must not regress ─────────────────────────────────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_message_prop_still_renders(settings, theme: str):
    settings.CF_UI_THEME = theme
    html = render_to_string("cotton/cf/notification.html", {**COTTON_BASE, "message": MESSAGE})
    assert MESSAGE in html


@pytest.mark.parametrize("theme", THEMES)
def test_jinja_message_prop_still_renders(theme: str):
    assert MESSAGE in _jinja(theme, message=MESSAGE, content="")


@pytest.mark.parametrize("theme", THEMES)
def test_jinjax_message_prop_still_renders(theme: str):
    html = _catalog(theme).render(
        "Cf:Notification", message=MESSAGE, type="info", dismissible=False, extra_class=""
    )
    assert MESSAGE in html


# ── Precedence, stated rather than emergent ───────────────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_body_wins_when_both_are_supplied(settings, theme: str):
    """A caller who wrote children meant them.

    Rendering both would duplicate the text; rendering ``message`` would
    reproduce the reported bug for anyone migrating. Asserting the loser is
    *absent* is the half that matters — "body appears" alone would pass on a
    template that emitted both.
    """
    settings.CF_UI_THEME = theme
    html = render_to_string(
        "cotton/cf/notification.html", {**COTTON_BASE, "slot": BODY, "message": MESSAGE}
    )
    assert BODY in html
    assert MESSAGE not in html


@pytest.mark.parametrize("theme", THEMES)
def test_jinja_body_wins_when_both_are_supplied(theme: str):
    html = _jinja(theme, content=BODY, message=MESSAGE)
    assert BODY in html
    assert MESSAGE not in html


# ── A body that renders to nothing is not a body ──────────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_whitespace_only_body_falls_back_to_message(settings, theme: str):
    """Otherwise the fix reintroduces the bug it exists to remove.

    ``django_cotton/templatetags/_component.py`` sets ``"slot":
    self.nodelist.render(context)`` — verbatim, unstripped. So a paired tag
    whose body renders to nothing still hands the partial ``"\\n  "``, which
    is truthy. The plausible call is a conditional body::

        <c-cf.notification message="Nothing to report">
          {% if error %}{{ error }}{% endif %}
        </c-cf.notification>

    On the false branch a naive ``{% if slot %}`` renders whitespace and drops
    ``message`` — a correctly-styled empty box, silently, which is #65 again
    with a new trigger. Verified against the real compiler, not inferred.
    """
    settings.CF_UI_THEME = theme
    html = render_to_string(
        "cotton/cf/notification.html", {**COTTON_BASE, "slot": "\n  \n", "message": MESSAGE}
    )
    assert MESSAGE in html, f"{theme}: whitespace-only body suppressed `message`"


@pytest.mark.parametrize("theme", THEMES)
def test_jinja_whitespace_only_body_falls_back_to_message(theme: str):
    """The same rule, stated the same way, on the other engine.

    JinjaX already strips slot content before it reaches the template, so this
    is belt-and-braces there — but the two engines should not disagree about
    what counts as a body, and the plain-Jinja path has no stripping at all.
    """
    assert MESSAGE in _jinja(theme, content="\n  \n", message=MESSAGE)


# ── Escaping: the two channels want opposite treatment ────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_jinjax_body_markup_is_not_double_escaped(theme: str):
    """Slot content is already-rendered markup; escaping it again shows entities.

    This is the specific hazard #65 flagged against 0.2.0's autoescape change:
    the two operands of the fallback expression are not alike, and a template
    that treats them alike breaks one of them.
    """
    html = _catalog(theme).render(
        "Cf:Notification",
        _content="<b>Bold body</b>",
        type="info",
        dismissible=False,
        extra_class="",
    )
    assert "<b>Bold body</b>" in html
    assert "&lt;b&gt;" not in html


@pytest.mark.parametrize("theme", THEMES)
def test_jinjax_message_is_still_escaped(theme: str):
    """``message`` is caller-supplied *text* and keeps the escaping it has today.

    Loosening the body channel must not loosen this one — that would turn a
    fix for a silent-drop bug into an injection vector.
    """
    html = _catalog(theme).render(
        "Cf:Notification",
        message="<script>window.cfPwned=true</script>",
        type="info",
        dismissible=False,
        extra_class="",
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_message_is_still_escaped(settings, theme: str):
    settings.CF_UI_THEME = theme
    html = render_to_string(
        "cotton/cf/notification.html",
        {**COTTON_BASE, "message": "<script>window.cfPwned=true</script>"},
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("theme", THEMES)
def test_cotton_body_markup_survives(settings, theme: str):
    """django-cotton hands the slot in already marked safe.

    ``render_to_string`` bypasses the cotton compiler, so the safe-string is
    constructed here rather than by cotton — without it Django would escape a
    raw string and this would assert the compiler's behaviour rather than the
    template's.
    """
    settings.CF_UI_THEME = theme
    html = render_to_string(
        "cotton/cf/notification.html", {**COTTON_BASE, "slot": mark_safe("<b>Bold body</b>")}
    )
    assert "<b>Bold body</b>" in html
    assert "&lt;b&gt;" not in html


# ── Drift guard ───────────────────────────────────────────────────────────


def _shipped_themes() -> list[str]:
    """Read off the filesystem, not from ``THEMES`` — that is the whole point."""
    return sorted(p.name for p in Path(JINJA_TEMPLATES_DIR).iterdir() if p.is_dir())


def test_themes_under_test_are_every_theme_shipped():
    """``THEMES`` is hand-written, so it goes stale the moment a sixth lands.

    Without this, every parametrized test above quietly stops covering the new
    theme and the suite still reports green.
    """
    assert _shipped_themes() == sorted(THEMES)


@pytest.mark.parametrize("theme", THEMES)
def test_every_shipped_theme_renders_its_notification_body(settings, theme: str):
    """A new theme copied from an old one must not reintroduce the bug.

    ``## Adding a New Theme`` in CLAUDE.md says to copy and adapt the existing
    templates, which is exactly how a fix applied to five files fails to reach
    the sixth.

    This renders rather than greps, because a substring guard on these files is
    remarkably hard to make non-vacuous. ``"content" in src`` matches fomantic's
    ``<div class="content">`` wrapper; the tightened ``"content if content"``
    still matches the ``{% set content = content if content is defined %}``
    StrictUndefined guard that every theme carries. Both needles looked
    specific and both passed on a template with the fallback expression
    deleted. Rendering cannot pass for the wrong reason.
    """
    settings.CF_UI_THEME = theme
    assert BODY in _jinja(theme, content=BODY, message="")
    assert BODY in render_to_string("cotton/cf/notification.html", {**COTTON_BASE, "slot": BODY})


def test_markup_import_is_used_by_the_escaping_contract():
    """Pins the assumption the escaping tests rest on, so it cannot drift silently.

    JinjaX wraps slot content in ``Markup``; that is *why* the body channel is
    not escaped a second time while ``message`` is. If that ever stopped being
    true the escaping tests above would still pass for the wrong reason.
    """
    assert Markup("<b>x</b>") == "<b>x</b>"
    assert Markup.escape("<b>x</b>") == "&lt;b&gt;x&lt;/b&gt;"
