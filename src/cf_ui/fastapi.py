from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR


def install_cf_ui(catalog: Any, theme: str = "bulma") -> None:
    """Register cf-ui Jinja2 templates with a JinjaX ComponentCatalog.

    Args:
        catalog: JinjaX ComponentCatalog instance.
        theme: CSS framework theme name. Defaults to "bulma".
    """
    template_dir = JINJA_TEMPLATES_DIR / theme
    catalog.add_path(template_dir, prefix="Cf")
