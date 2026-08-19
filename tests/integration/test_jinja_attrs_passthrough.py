"""``attrs`` passthrough on the JinjaX path, against a real catalog (#78).

JinjaX reserves the prop name ``attrs`` for its own extra-kwargs collector
(``jinjax/catalog.py``, ``ARGS_ATTRS = "attrs"``) and unconditionally
overwrites whatever a component's own ``{#def}`` declares for it, on every
render. ``docs/primitives.md`` documented ``:attrs="{...}"`` as the JinjaX
usage — that syntax silently no-ops under a real ``Catalog``, with no error,
because the caller's dict never reaches ``cf_ui.primitives.render_attrs`` at
all. The unit tier's Jinja2-``Environment``-only tests
(``test_attrs_passthrough.py`` et al.) never caught this: without a real
``Catalog``, ``{#def}`` is a plain comment and every prop — ``attrs``
included — arrives as an ordinary template variable, bypassing JinjaX's
``ARGS_ATTRS`` collision entirely. Only a real ``Catalog`` reproduces it,
which is why these tests live at the integration tier, mirroring
``test_jinja_autoescape.py``.

``_attrs=``/``__attrs=`` is JinjaX's own escape hatch for this
(``kw.pop("_attrs", kw.pop("__attrs", None))``) and is the syntax
``docs/primitives.md`` documents now. Its keys get merged flat into the
call's kwargs before JinjaX splits declared props from undeclared extras, so
a key that also happens to be one of the component's own declared prop names
(``type``/``href`` for ``Button``; ``name`` for the form controls) never
reaches ``render_attrs``'s ``RESERVED_ATTRS`` guard — it silently becomes
that prop's value instead (the caller's real prop, if also passed, wins).
The guard only reliably fires for reserved names that are *not* also
declared props (``class``, ``role``, ``aria-disabled``, ``disabled`` for
``Button``). Both halves are pinned below so a future JinjaX version change
is caught, not assumed away.
"""

import pytest
from jinjax import Catalog

from cf_ui.fastapi import install_cf_ui
from cf_ui.primitives import PrimitiveConfigError

#: A double quote, a live event handler, and a dangling attribute to swallow
#: the closing quote the template supplies — mirrors test_jinja_autoescape.py.
HOSTILE = '" onmouseover="window.cfPwned=true" x="'


@pytest.fixture
def catalog() -> Catalog:
    cat = Catalog()
    install_cf_ui(cat, theme="bulma")
    return cat


def test_bare_extra_kwargs_pass_through(catalog: Catalog) -> None:
    """The working, undocumented-until-now pattern: unpack a dict of literal
    HTML attribute names (hyphens included) as ``**kwargs``."""
    html = catalog.render(
        "Cf:Button", _content="Save", **{"data-event": "submit", "hx-post": "/orders"}
    )
    assert 'data-event="submit"' in html
    assert 'hx-post="/orders"' in html


def test_attrs_dict_via_the_underscore_attrs_kwarg_passes_through(catalog: Catalog) -> None:
    """The documented fix for #78: ``_attrs={...}``, not ``attrs={...}``."""
    html = catalog.render(
        "Cf:Button",
        _content="Save",
        _attrs={"data-event": "submit", "hx-post": "/orders"},
    )
    assert 'data-event="submit"' in html
    assert 'hx-post="/orders"' in html


def test_plain_attrs_kwarg_is_silently_discarded_by_jinjax(catalog: Catalog) -> None:
    """Pins the bug #78 exists to warn about, not a desired behavior.

    ``docs/primitives.md`` must never show ``attrs=``/``:attrs="..."`` for
    JinjaX usage — the two tests above show the syntax that actually works.
    """
    html = catalog.render("Cf:Button", _content="Save", attrs={"data-event": "submit"})
    assert "data-event" not in html


def test_attrs_collision_with_a_reserved_undeclared_name_still_raises(catalog: Catalog) -> None:
    """``class`` is RESERVED_ATTRS-listed for button but not a declared prop
    (``extra_class`` is), so it never intercepts before ``render_attrs`` runs."""
    with pytest.raises(PrimitiveConfigError):
        catalog.render("Cf:Button", _content="Save", _attrs={"class": "override"})


def test_attrs_collision_with_a_declared_prop_name_is_not_caught_by_the_guard(
    catalog: Catalog,
) -> None:
    """A JinjaX-level gap, not a cf-ui one — documented in this file's module
    docstring and in ``docs/primitives.md``.

    ``type`` is both RESERVED_ATTRS-listed and one of Button's own ``{#def}``
    props. JinjaX's own arg-filtering routes an ``_attrs={"type": ...}``
    collision straight into the ``type`` prop before ``render_attrs`` ever
    sees it, so ``PrimitiveConfigError`` never fires here — the caller's
    real ``type=`` prop silently wins instead.
    """
    html = catalog.render("Cf:Button", _content="Save", type="submit", _attrs={"type": "reset"})
    assert 'type="submit"' in html
    assert 'type="reset"' not in html


def test_hostile_attrs_value_is_still_escaped(catalog: Catalog) -> None:
    html = catalog.render("Cf:Button", _content="Save", _attrs={"data-x": HOSTILE})
    assert 'onmouseover="window.cfPwned=true"' not in html
