"""The Bootstrap pin is a tripwire, not just a default (#33).

cf-ui ships the `bootstrap` theme as CSS only, with Alpine driving every
interactive component. That decision is correct for Bootstrap 5 and is recorded
in `docs/bootstrap.md`. Bootstrap 6 changes the premises it rests on, and
nothing in the repo would otherwise notice.

So the pin itself is the hook. `_DEFAULTS["bootstrap"]` is the one place the
major version is stated, and the test below fails the moment it leaves the `5.x`
line — with a message that *is* the checklist of what to re-evaluate. This is
the pattern #17 established for Tailwind: pin the thing and let a break on bump
be the signal, rather than trusting anyone to remember to look.

A promise to monitor a dependency does not survive; a red test does.
"""

from pathlib import Path

from cf_ui.templatetags.cf_ui import _CDN_CSS, _DEFAULTS

DOCS = Path(__file__).parent.parent.parent / "docs" / "bootstrap.md"

#: Everything the v6 rework has to answer. Verified against `v6-dev` when #33
#: was written, not inferred from release notes — several secondary sources
#: claim v6 already moved to native `<dialog>` citing twbs#41751, which is
#: closed and was never merged.
V6_CHECKLIST = """\
Bootstrap has moved off the 5.x line. Re-read docs/bootstrap.md before changing
this pin, and re-evaluate all four of these:

  1. Class renames. v6 replaces `_modal.scss` with `_dialog.scss` and defines
     `.dialog`, `.dialog-header`, `.dialog-body`, `.dialog-footer`,
     `.dialog-title` and siblings — no `.modal*` selector survives. cf-ui's
     bootstrap modal templates carry 8 `modal-*` references each, so they break
     on the CSS alone, whatever is decided about JS.
  2. `showModal()` vs `role="dialog"`. v6's `dialog.ts` is built on
     `HTMLDialogElement.showModal()`. #19 decided cf-ui keeps a `<div
     role="dialog">` so `cfModal` does not branch per theme; the v6 rework is
     when that trade is worth re-pricing.
  3. The CSS-only stance. v6 is *expanding* its JS surface — combobox,
     datepicker, otp-input, chips, strength, drawer, menu, range — so the gap
     between what Bootstrap does in JS and what cf-ui wraps grows, not shrinks.
  4. Whether a per-theme behaviour driver is warranted by then. Recorded in
     docs/bootstrap.md as considered-and-deferred, on the grounds that no
     consumer has reported needing it. That may have changed.
"""


def test_the_bootstrap_pin_is_still_on_the_5_line():
    major = _DEFAULTS["bootstrap"].split(".")[0]
    assert major == "5", V6_CHECKLIST


def test_the_decision_record_exists():
    """The tripwire's message points at this file; it has to be there."""
    assert DOCS.is_file(), "docs/bootstrap.md is the decision this pin guards"


def test_the_decision_record_states_the_js_stance():
    """A reader has to be able to answer "may I add Bootstrap's JS?" from it."""
    text = DOCS.read_text(encoding="utf-8")
    assert "bootstrap.bundle" in text, "does not name the bundle it declines to ship"
    assert "data-bs-" in text, "does not warn about the attribute API"
    assert "Bootstrap 6" in text, "does not tell the reader what changes at v6"


def test_the_theme_still_resolves_to_a_pinned_css_url():
    """A pin nothing reads is not a pin."""
    url = _CDN_CSS["bootstrap"].format(v=_DEFAULTS["bootstrap"])
    assert _DEFAULTS["bootstrap"] in url
    assert url.endswith("bootstrap.min.css")
    assert ".bundle." not in url, "cf-ui does not ship Bootstrap's JS — see docs/bootstrap.md"
