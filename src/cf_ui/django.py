from pathlib import Path

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


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

        if not hasattr(settings, "COTTON_DIRS"):
            settings.COTTON_DIRS = []

        if cotton_dir not in [Path(d) for d in settings.COTTON_DIRS]:
            settings.COTTON_DIRS.append(cotton_dir)
