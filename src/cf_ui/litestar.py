from collections.abc import Mapping
from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.axes import build_axis_globals

try:  # pragma: no cover - exercised by test_litestar_args_prefix_matches_jinjax
    from jinjax.utils import ARGS_PREFIX
except ImportError:  # pragma: no cover
    # JinjaX rewrites `<Cf:Card>` into `catalog.irender("Cf:Card",
    # __prefix=__prefix, ...)`. The name is a jinjax internal, so it is read
    # from jinjax when available and pinned by a test that fails on a rename.
    ARGS_PREFIX = "__prefix"


def _install_catalog(environment: Any, template_dir: Any) -> Any:
    """Give a plain Jinja2 ``Environment`` the ability to render cf-ui components.

    Litestar renders through its own ``Environment``, not through a JinjaX
    ``Catalog``, and ``Catalog(jinja_env=env)`` does **not** convert that
    environment: it builds its own, copying extensions/globals/filters across,
    and only writes ``catalog`` back into the one it was handed. So the
    component tag needs three things wired onto Litestar's environment
    directly:

    1. the ``JinjaX`` extension, which rewrites ``<Cf:Card>`` into a
       ``catalog.irender(...)`` call;
    2. a ``Catalog`` built over this environment, which supplies the
       ``catalog`` global that call resolves against;
    3. ``__prefix``, which the rewritten call passes through. JinjaX binds it
       per-component while rendering *inside* a component, so a page template
       rendered by Litestar has no binding and raises ``'__prefix' is
       undefined``. The empty string is the correct value for a page: it means
       "no enclosing component prefix".

    Without all three, ``<Cf:Card>`` reached the browser as literal text — no
    exception, no output (#42).
    """
    from jinjax import Catalog
    from jinjax.jinjax import JinjaX

    environment.add_extension(JinjaX)
    catalog = Catalog(jinja_env=environment)
    catalog.add_folder(template_dir, prefix="Cf")
    # setdefault: an app that renders its own JinjaX components keeps its value.
    environment.globals.setdefault(ARGS_PREFIX, "")
    return catalog


def install_cf_ui(
    config: Any,
    theme: str = "bulma",
    composition: str | Mapping[str, str] | None = None,
    value_sets: Mapping[str, Mapping[str, Any]] | None = None,
    value_sets_mode: str = "extend",
) -> None:
    """Register cf-ui with a Litestar TemplateConfig.

    Puts two directories on the template search path — the theme's component
    folder, and the package template root so ``{% from "cf_ui/assets.jinja"
    import ... %}`` resolves — then chains an ``engine_callback`` that
    registers the axis globals and installs a JinjaX catalog on Litestar's
    Jinja2 environment. Any callback the app already set still runs.

    After this, ``<Cf:Card header="Title">Body</Cf:Card>`` renders in an
    ordinary Litestar template, the same tag FastAPI uses.

    The callback never touches the environment's ``autoescape`` setting.
    cf-ui's templates carry their own ``{% autoescape true %}`` blocks (#36) —
    they escape their output whatever the app's engine is configured to do,
    which matters here in particular, because Litestar's
    ``JinjaTemplateEngine`` does not enable autoescaping.

    .. warning::
        Litestar's ``TemplateConfig`` is frozen after construction. Call this
        function **before** passing the config to ``Litestar()``, or pass the
        paths directly via ``TemplateConfig(directory=[...])``. Calling this on
        a config already attached to a running app raises
        ``FrozenInstanceError``.

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
    # The macros live at templates/cf_ui/assets.jinja, a sibling of
    # templates/jinja/ — so the theme folder alone left every documented
    # `{% from "cf_ui/assets.jinja" %}` raising TemplateNotFound (#42).
    package_templates = JINJA_TEMPLATES_DIR.parent

    if isinstance(config.directory, list):
        config.directory.extend([template_dir, package_templates])
    else:
        config.directory = [config.directory, template_dir, package_templates]

    axis_globals = build_axis_globals(composition, value_sets, value_sets_mode)
    previous = getattr(config, "engine_callback", None)

    def _register(engine: Any) -> None:
        if callable(previous):
            previous(engine)
        # JinjaTemplateEngine exposes the Jinja2 Environment as .engine
        environment = getattr(engine, "engine", engine)
        environment.globals.update(axis_globals)
        _install_catalog(environment, template_dir)

    config.engine_callback = _register
