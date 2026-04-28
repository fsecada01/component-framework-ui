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

        # django-cotton reads COTTON_DIR (singular). Setting it to
        # "cotton/<theme>" makes <c-cf.foo> resolve to
        # cotton/<theme>/cf/foo.html, which the cotton loader finds via
        # the app-templates walk (cf_ui/templates/cotton/<theme>/cf/foo.html).
        # Don't overwrite a value the consumer has already set.
        if not getattr(settings, "COTTON_DIR", None):
            settings.COTTON_DIR = f"cotton/{theme}"
