from pathlib import Path

from django.apps import AppConfig


class CfUiConfig(AppConfig):
    name = "cf_ui.django"
    label = "cf_ui"
    verbose_name = "Component Framework UI"

    def ready(self) -> None:
        from django.conf import settings

        theme = getattr(settings, "CF_UI_THEME", "bulma")
        cotton_dir = Path(__file__).parent / "templates" / "cotton" / theme

        if not hasattr(settings, "COTTON_DIRS"):
            settings.COTTON_DIRS = []

        if cotton_dir not in [Path(d) for d in settings.COTTON_DIRS]:
            settings.COTTON_DIRS.append(cotton_dir)


default_app_config = "cf_ui.django.CfUiConfig"
