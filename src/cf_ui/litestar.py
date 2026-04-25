from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR


def install_cf_ui(config: Any, theme: str = "bulma") -> None:
    """Register cf-ui Jinja2 templates with a Litestar TemplateConfig.

    Appends the theme template directory to config.directory.

    .. warning::
        Litestar's ``TemplateConfig`` is frozen after construction. Call this
        function **before** passing the config to ``Litestar()``, or pass the
        path directly via ``TemplateConfig(directory=[..., JINJA_TEMPLATES_DIR / theme])``.
        Calling this on a config that is already attached to a running app will
        raise ``FrozenInstanceError``.

    Args:
        config: Litestar TemplateConfig instance (must not be frozen yet).
        theme: CSS framework theme name. Defaults to "bulma".
    """
    template_dir = JINJA_TEMPLATES_DIR / theme

    if isinstance(config.directory, list):
        config.directory.append(template_dir)
    else:
        config.directory = [config.directory, template_dir]
