from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, Undefined, select_autoescape

BULMA_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src" / "cf_ui" / "templates" / "jinja" / "bulma"
)


@pytest.fixture
def env() -> Environment:
    """Jinja2 Environment pointed at the Bulma template directory."""
    return Environment(
        loader=FileSystemLoader(str(BULMA_DIR)),
        autoescape=select_autoescape(["html"]),
        undefined=Undefined,
    )


@pytest.fixture
def render(env: Environment):
    """Return a helper: render(template_name, **ctx) -> str."""
    def _render(name: str, **ctx: object) -> str:
        return env.get_template(name).render(**ctx)
    return _render
