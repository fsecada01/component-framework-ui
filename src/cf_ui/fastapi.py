from collections.abc import Mapping
from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.axes import build_axis_globals
from cf_ui.primitives import build_primitive_globals


def install_cf_ui(
    catalog: Any,
    theme: str = "bulma",
    composition: str | Mapping[str, str] | None = None,
    value_sets: Mapping[str, Mapping[str, Any]] | None = None,
    value_sets_mode: str = "extend",
) -> None:
    """Register cf-ui Jinja2 templates with a JinjaX ComponentCatalog.

    Also registers the axis globals the ``assets.jinja`` macros delegate to,
    so ``<html {{ cf_ui_root_attrs() }}>`` stamps all five attributes from
    this one call.

    The installer never touches the environment's ``autoescape`` setting.
    cf-ui's templates carry their own ``{% autoescape true %}`` blocks (#36),
    so they escape their output whatever the catalog is configured to do —
    including on a bare ``Catalog()``, whose environment does not autoescape,
    and regardless of whether this function was ever called. The app's own
    escaping policy, ``select_autoescape`` callables included, is the app's.

    Args:
        catalog: JinjaX ComponentCatalog instance.
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
    catalog.add_folder(template_dir, prefix="Cf")
    catalog.jinja_env.globals.update(build_axis_globals(composition, value_sets, value_sets_mode))
    catalog.jinja_env.globals.update(build_primitive_globals())
