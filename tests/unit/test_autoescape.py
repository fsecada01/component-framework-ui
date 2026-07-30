"""Both installers leave an autoescaping environment behind (#36).

``cf_ui/fastapi.py`` and ``cf_ui/litestar.py`` reach the Jinja environment by
different routes — one holds the catalog directly, the other only ever sees the
engine through a callback Litestar invokes later — so "autoescape is on" has to
be asserted separately for each. The integration tier proves the FastAPI path
end to end against a real catalog; this file covers the wiring, and is the only
place the Litestar path is exercised at all.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from jinja2 import Environment

# --- FastAPI / JinjaX -------------------------------------------------------


def test_fastapi_installer_turns_autoescape_on() -> None:
    from jinjax import Catalog

    from cf_ui.fastapi import install_cf_ui

    catalog = Catalog()
    assert not catalog.jinja_env.autoescape

    install_cf_ui(catalog, theme="bulma")
    assert catalog.jinja_env.autoescape is True


def test_fastapi_installer_escape_hatch_leaves_it_off() -> None:
    from jinjax import Catalog

    from cf_ui.fastapi import install_cf_ui

    catalog = Catalog()
    install_cf_ui(catalog, theme="bulma", cf_ui_autoescape=False)
    assert not catalog.jinja_env.autoescape


def test_fastapi_installer_still_registers_the_axis_globals() -> None:
    """Regression guard: the new line must not displace the existing one."""
    from jinjax import Catalog

    from cf_ui.fastapi import install_cf_ui

    catalog = Catalog()
    install_cf_ui(catalog, theme="bulma")

    assert "cf_ui_axis_attrs" in catalog.jinja_env.globals
    assert "cf_ui_axis_style" in catalog.jinja_env.globals


# --- Litestar ---------------------------------------------------------------


def _fresh_config() -> MagicMock:
    """A TemplateConfig double with no callback of its own.

    ``engine_callback`` is set to ``None`` explicitly: a bare ``MagicMock``
    attribute is callable, so the installer would treat it as a previous
    callback and invoke it, which is not the case under test here.
    """
    config = MagicMock()
    config.directory = []
    config.engine_callback = None
    return config


def test_litestar_installer_turns_autoescape_on() -> None:
    from cf_ui.litestar import install_cf_ui

    config = _fresh_config()
    install_cf_ui(config, theme="bulma")

    env = Environment()
    assert not env.autoescape
    config.engine_callback(SimpleNamespace(engine=env))

    assert env.autoescape is True


def test_litestar_installer_escape_hatch_leaves_it_off() -> None:
    from cf_ui.litestar import install_cf_ui

    config = _fresh_config()
    install_cf_ui(config, theme="bulma", cf_ui_autoescape=False)

    env = Environment()
    config.engine_callback(SimpleNamespace(engine=env))

    assert not env.autoescape


def test_litestar_installer_still_chains_a_previous_callback() -> None:
    """The callback chaining predates this change and must survive it."""
    from cf_ui.litestar import install_cf_ui

    seen: list[object] = []
    config = MagicMock()
    config.directory = []
    config.engine_callback = seen.append

    install_cf_ui(config, theme="bulma")
    engine = SimpleNamespace(engine=Environment())
    config.engine_callback(engine)

    assert seen == [engine]
    assert engine.engine.autoescape is True


def test_litestar_installer_still_registers_the_axis_globals() -> None:
    from cf_ui.litestar import install_cf_ui

    config = _fresh_config()
    install_cf_ui(config, theme="bulma")

    env = Environment()
    config.engine_callback(SimpleNamespace(engine=env))

    assert "cf_ui_axis_attrs" in env.globals


def test_litestar_installer_handles_an_engine_without_a_nested_environment() -> None:
    """``getattr(engine, "engine", engine)`` — the existing fallback path."""
    from cf_ui.litestar import install_cf_ui

    config = _fresh_config()
    install_cf_ui(config, theme="bulma")

    env = Environment()
    config.engine_callback(env)

    assert env.autoescape is True


# --- The unit tier stops being a proxy --------------------------------------


def test_the_shared_unit_environment_matches_what_the_installer_ships() -> None:
    """AC2. The unit fixtures must not be friendlier than the shipped config.

    Two of them were, in a way that read as deliberate:
    ``select_autoescape(["html"])`` keys off the *file extension*, and cf-ui's
    Jinja templates are ``.jinja``, so it resolved to ``False``. A fixture that
    looks like it enables escaping and does not is worse than one that plainly
    does not, because every assertion under it reads as proof of something it
    never tested. The helper now derives the setting from a real installed
    catalog, so the two cannot drift again.
    """
    from tests.jinja_env import installed_autoescape, make_env

    env = make_env(__import__("cf_ui").JINJA_TEMPLATES_DIR / "bulma")

    assert installed_autoescape() is True
    assert env.autoescape is True


@pytest.mark.parametrize("extension_list", [["html"], ["html", "htm", "xml"]])
def test_select_autoescape_would_not_have_covered_dot_jinja(extension_list: list[str]) -> None:
    """Pins the specific trap, so nobody reintroduces it as a "cleanup".

    This is not testing Jinja2 for its own sake — it is recording why the two
    fixtures were wrong, in executable form, next to the fix.
    """
    from jinja2 import select_autoescape

    assert select_autoescape(extension_list)("Tabs.jinja") is False
