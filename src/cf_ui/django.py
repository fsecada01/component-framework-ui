from django.apps import AppConfig


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
