from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

from cf_ui.axes import (
    DEFAULT_VALUE_SETS,
    AxisConfigError,
    merge_value_sets,
    resolve_composition,
)
from cf_ui.themes import ThemeError, resolve_theme


def axis_value_sets() -> dict:
    """Resolve the active axis value sets from Django settings.

    ``CF_UI_AXIS_VALUES`` supplies an app's own value sets;
    ``CF_UI_AXIS_VALUES_MODE`` chooses whether they extend (default) or
    replace the shipped ones.
    """
    from django.conf import settings

    custom = getattr(settings, "CF_UI_AXIS_VALUES", None)
    if not custom:
        return DEFAULT_VALUE_SETS
    mode = getattr(settings, "CF_UI_AXIS_VALUES_MODE", "extend")
    return merge_value_sets(custom, mode=mode)


class CfUiConfig(AppConfig):
    name = "cf_ui.django"
    label = "cf_ui"
    verbose_name = "Component Framework UI"

    # cf-ui Cotton templates live at src/cf_ui/templates/cotton/cf/*.html.
    # Django's app-templates loader (APP_DIRS=True) picks them up directly
    # and django-cotton's default COTTON_DIR ("cotton") resolves
    # <c-cf.foo> -> cotton/cf/foo.html. We deliberately do not touch
    # COTTON_DIR here: doing so would break consumer projects whose own
    # cotton templates live at cotton/<their-app>/*.html.

    def ready(self) -> None:
        """Validate the theme and axis composition at startup.

        Both would otherwise surface at first render — an unknown theme as a
        ``TemplateDoesNotExist`` naming a partial the app never wrote, which
        is a poor way to learn that ``CF_UI_THEME`` holds a stub theme's name.

        Deliberately touches no template settings — see the note above.
        """
        from django.conf import settings

        try:
            resolve_theme(getattr(settings, "CF_UI_THEME", None))
        except ThemeError as exc:
            raise ImproperlyConfigured(f"cf-ui: {exc}. Check CF_UI_THEME in settings.") from exc

        try:
            resolve_composition(
                getattr(settings, "CF_UI_COMPOSITION", None),
                value_sets=axis_value_sets(),
            )
        except AxisConfigError as exc:
            raise ImproperlyConfigured(
                f"cf-ui: {exc}. Check CF_UI_COMPOSITION in settings."
            ) from exc
