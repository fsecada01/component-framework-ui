from collections.abc import Mapping
from typing import Any

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.axes import build_axis_globals


def install_cf_ui(
    catalog: Any,
    theme: str = "bulma",
    composition: str | Mapping[str, str] | None = None,
    value_sets: Mapping[str, Mapping[str, Any]] | None = None,
    value_sets_mode: str = "extend",
    cf_ui_autoescape: bool = True,
) -> None:
    """Register cf-ui Jinja2 templates with a JinjaX ComponentCatalog.

    Also registers the axis globals the ``assets.jinja`` macros delegate to,
    so ``<html {{ cf_ui_root_attrs() }}>`` stamps all five attributes from
    this one call.

    Args:
        catalog: JinjaX ComponentCatalog instance.
        theme: CSS framework theme name. Defaults to "bulma".
        composition: A named composition, a partial ``{axis: value}`` mapping,
            or ``None`` for the default composition.
        value_sets: The app's own axis value sets, if any.
        value_sets_mode: ``"extend"`` (default) or ``"replace"``.
        cf_ui_autoescape: Turn Jinja2 autoescaping on for the catalog's
            environment **if it is currently off**. Defaults to ``True``.
            ``jinjax.Catalog`` builds ``Environment(undefined=StrictUndefined)``
            and autoescape defaults to ``False``, so without this every
            ``{{ … }}`` in a cf-ui template emits raw output and a
            request-controlled value carrying a double quote can close its
            attribute and open one of its own (#36). A catalog whose
            environment already autoescapes — including one configured with a
            ``select_autoescape`` callable — is left exactly as it is. Pass
            ``False`` only if the app depends on unescaped interpolation
            through a cf-ui component; the safer fix is to escape at the source.

    Raises:
        AxisConfigError: if the composition or value sets are invalid. This is
            raised eagerly at install time rather than at first render.
    """
    template_dir = JINJA_TEMPLATES_DIR / theme
    catalog.add_folder(template_dir, prefix="Cf")

    # Only when it is off. Jinja accepts a callable here, and `select_autoescape`
    # is how an app expresses a per-template policy — overwriting it with a
    # blanket `True` would change how the app's *own* templates render, not just
    # cf-ui's. Any truthy setting is the caller's and is left alone.
    if cf_ui_autoescape and not catalog.jinja_env.autoescape:
        catalog.jinja_env.autoescape = True
        # `autoescape` is read at *compile* time and JinjaX caches compiled
        # components, so a component rendered before this call would stay
        # compiled without escaping for the life of the process — silently,
        # while the flag reads `True`. Dropping the cache makes the change
        # retroactive. `_cache` is private, so this is guarded: a JinjaX release
        # that renames it degrades to the old behaviour rather than raising at
        # install time, and
        # `test_escaping_does_not_depend_on_when_the_installer_ran` fails in CI.
        cache = getattr(catalog, "_cache", None)
        if isinstance(cache, dict):
            cache.clear()

    catalog.jinja_env.globals.update(build_axis_globals(composition, value_sets, value_sets_mode))
