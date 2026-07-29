from pathlib import Path

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

from cf_ui.axes import (
    DEFAULT_VALUE_SETS,
    AxisConfigError,
    merge_value_sets,
    resolve_composition,
)


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

    def ready(self) -> None:
        from django.conf import settings

        theme = getattr(settings, "CF_UI_THEME", "bulma")
        cotton_dir = Path(__file__).parent / "templates" / "cotton" / theme

        if not cotton_dir.is_dir():
            raise ImproperlyConfigured(
                f"cf-ui: no templates found for theme {theme!r} at {cotton_dir}. "
                f"Check CF_UI_THEME in settings."
            )

        # django-cotton reads COTTON_DIR (singular). Setting it to
        # "cotton/<theme>" makes <c-cf.foo> resolve to
        # cotton/<theme>/cf/foo.html, which the cotton loader finds via
        # the app-templates walk (cf_ui/templates/cotton/<theme>/cf/foo.html).
        # Don't overwrite a value the consumer has already set.
        if not getattr(settings, "COTTON_DIR", None):
            settings.COTTON_DIR = f"cotton/{theme}"

        # Fail at startup, not at first render, on a bad axis composition.
        try:
            resolve_composition(
                getattr(settings, "CF_UI_COMPOSITION", None),
                value_sets=axis_value_sets(),
            )
        except AxisConfigError as exc:
            raise ImproperlyConfigured(
                f"cf-ui: {exc}. Check CF_UI_COMPOSITION in settings."
            ) from exc
