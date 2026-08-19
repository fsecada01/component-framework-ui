from collections.abc import Callable
from pathlib import Path

import pytest
from jinja2 import Environment

from cf_ui.primitives import build_primitive_globals
from tests.jinja_env import make_env

BULMA_DIR = (
    Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "jinja" / "bulma"
)


@pytest.fixture
def env() -> Environment:
    """Jinja2 Environment pointed at the Bulma template directory.

    Built by ``make_env`` so it matches what ``install_cf_ui`` ships. This
    previously passed ``select_autoescape(["html"])``, which keys off the file
    extension and so resolved to ``False`` for ``.jinja`` — the fixture read as
    though it escaped and did not (#36).
    """
    e = make_env(BULMA_DIR)
    e.globals.update(build_primitive_globals())
    return e


@pytest.fixture
def render(env: Environment) -> Callable[..., str]:
    """Return a helper: render(template_name, **ctx) -> str."""

    def _render(template_name: str, **ctx: object) -> str:
        return env.get_template(template_name).render(**ctx)

    return _render
