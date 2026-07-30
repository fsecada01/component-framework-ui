from collections.abc import Mapping
from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.axes import build_axis_globals


def install_cf_ui(
    config: Any,
    theme: str = "bulma",
    composition: str | Mapping[str, str] | None = None,
    value_sets: Mapping[str, Mapping[str, Any]] | None = None,
    value_sets_mode: str = "extend",
) -> None:
    """Register cf-ui Jinja2 templates with a Litestar TemplateConfig.

    Appends the theme template directory to config.directory, and chains an
    ``engine_callback`` that registers the axis globals the ``assets.jinja``
    macros delegate to. Any callback the app already set still runs.

    The callback never touches the environment's ``autoescape`` setting.
    cf-ui's templates carry their own ``{% autoescape true %}`` blocks (#36) —
    they escape their output whatever the app's engine is configured to do,
    which matters here in particular: on this path cf-ui's ``.jinja`` files are
    loaded as ordinary Jinja2 templates, and Litestar's ``JinjaTemplateEngine``
    does not enable autoescaping.

    .. warning::
        Litestar's ``TemplateConfig`` is frozen after construction. Call this
        function **before** passing the config to ``Litestar()``, or pass the
        path directly via ``TemplateConfig(directory=[..., JINJA_TEMPLATES_DIR / theme])``.
        Calling this on a config that is already attached to a running app will
        raise ``FrozenInstanceError``.

    Args:
        config: Litestar TemplateConfig instance (must not be frozen yet).
        theme: CSS framework theme name. Defaults to "bulma".
        composition: A named composition, a partial ``{axis: value}`` mapping,
            or ``None`` for the default composition.
        value_sets: The app's own axis value sets, if any.
        value_sets_mode: ``"extend"`` (default) or ``"replace"``.

    Raises:
        AxisConfigError: if the composition or value sets are invalid. This is
            raised eagerly at install time rather than at first render.
    """
    template_dir = JINJA_TEMPLATES_DIR / theme

    if isinstance(config.directory, list):
        config.directory.append(template_dir)
    else:
        config.directory = [config.directory, template_dir]

    axis_globals = build_axis_globals(composition, value_sets, value_sets_mode)
    previous = getattr(config, "engine_callback", None)

    def _register_axis_globals(engine: Any) -> None:
        if callable(previous):
            previous(engine)
        # JinjaTemplateEngine exposes the Jinja2 Environment as .engine
        environment = getattr(engine, "engine", engine)
        environment.globals.update(axis_globals)

    config.engine_callback = _register_axis_globals
