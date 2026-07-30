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
    cf_ui_autoescape: bool = True,
) -> None:
    """Register cf-ui Jinja2 templates with a Litestar TemplateConfig.

    Appends the theme template directory to config.directory, and chains an
    ``engine_callback`` that registers the axis globals the ``assets.jinja``
    macros delegate to. Any callback the app already set still runs.

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
        cf_ui_autoescape: Turn Jinja2 autoescaping on for the engine's
            environment **if it is currently off**. Defaults to ``True``.
            Litestar's ``JinjaTemplateEngine`` does not enable it, so without
            this every ``{{ … }}`` in a cf-ui template emits raw output and a
            request-controlled value carrying a double quote can close its
            attribute and open one of its own (#36). An environment that
            already autoescapes — including one configured with a
            ``select_autoescape`` callable — is left exactly as it is. Applied
            in the same ``engine_callback`` as the axis globals, because that is
            the only point at which this installer sees the environment.

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
        # Only when it is off — see the FastAPI installer for why a truthy
        # setting (notably a `select_autoescape` callable) is the caller's.
        if cf_ui_autoescape and not environment.autoescape:
            environment.autoescape = True
            # Same compile-time caching hazard as the JinjaX path, one layer
            # down: `Environment.cache` holds templates compiled under the old
            # setting. Litestar builds the engine before serving, so this is
            # belt-and-braces rather than a known ordering — but the attribute
            # is public and the cost is a dict clear.
            if environment.cache is not None:
                environment.cache.clear()
        environment.globals.update(axis_globals)

    config.engine_callback = _register_axis_globals
