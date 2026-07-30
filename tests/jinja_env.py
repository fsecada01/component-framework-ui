"""One Jinja ``Environment`` builder for the whole suite, derived from the
installer rather than restated by hand (#36).

Before this, each tier built its own environment and passed
``autoescape=select_autoescape([...])``. That call keys off the *file
extension*, and cf-ui's Jinja templates are ``.jinja`` — so the two fixtures
that listed only ``["html"]`` resolved to ``False`` and quietly tested nothing
about escaping, while reading exactly like fixtures that did. The three added
by #35 listed ``["html", "jinja"]`` and escaped correctly, which meant the
suite disagreed with itself about what the shipped configuration was.

Neither hand-written form is right, because neither is *connected* to what
``install_cf_ui`` actually does. :func:`installed_autoescape` asks a real
installed catalog, so a change to the installer moves the whole suite with it
and a fixture can never again be friendlier than the shipped default.
"""

from __future__ import annotations

from functools import lru_cache
from os import PathLike

from jinja2 import Environment, FileSystemLoader, StrictUndefined


@lru_cache(maxsize=1)
def installed_autoescape() -> bool:
    """Return the ``autoescape`` value ``install_cf_ui`` leaves on a catalog.

    Built once per session: constructing a ``Catalog`` and registering the
    axis globals is cheap but not free, and the answer cannot change within a
    run.
    """
    from jinjax import Catalog

    from cf_ui.fastapi import install_cf_ui

    catalog = Catalog()
    install_cf_ui(catalog, theme="bulma")
    autoescape = catalog.jinja_env.autoescape
    # Jinja accepts a callable here; the installer sets a plain bool, but read
    # it defensively so a caller-supplied selector cannot crash the fixtures.
    return bool(autoescape("Tabs.jinja")) if callable(autoescape) else bool(autoescape)


def make_env(directory: str | PathLike[str]) -> Environment:
    """A ``FileSystemLoader`` environment matching the shipped configuration."""
    return Environment(
        loader=FileSystemLoader(directory),
        autoescape=installed_autoescape(),
        undefined=StrictUndefined,
    )
