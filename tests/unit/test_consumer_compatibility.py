"""
Regression tests guarding against COTTON_DIR hijacking.

Background: an earlier fix (commit 5814476c) set ``COTTON_DIR="cotton/bulma"``
in ``CfUiConfig.ready()``. Because django-cotton uses ``COTTON_DIR`` as a
single global prefix for *every* ``<c-foo.bar>`` lookup, any consumer with
its own templates at ``templates/cotton/<their-app>/...`` immediately broke
once it added ``cf_ui.django.CfUiConfig`` to ``INSTALLED_APPS``.

cf-ui's templates now live at ``cotton/cf/*.html`` (no theme prefix), and
``CfUiConfig`` no longer touches ``COTTON_DIR``. These tests pin both
behaviors so the regression cannot return.
"""

from pathlib import Path


def test_cf_ui_does_not_set_cotton_dir():
    """CfUiConfig.ready() must not write to settings.COTTON_DIR."""
    from django.conf import settings

    cf_ui_managed_value = "cotton/bulma"
    assert getattr(settings, "COTTON_DIR", None) != cf_ui_managed_value


def test_consumer_and_cf_ui_cotton_templates_resolve_together(tmp_path: Path):
    """A consumer's ``cotton/<app>/foo.html`` and cf-ui's ``cotton/cf/*.html``
    must both resolve through the same Django template engine when
    ``cf_ui.django.CfUiConfig`` is installed.
    """
    from django.apps import apps
    from django.template.engine import Engine

    # Django is configured + populated by tests/unit/conftest.py
    # (which calls django.setup()). Verify cf_ui is registered as an app
    # before testing template resolution.
    assert apps.get_app_config("cf_ui") is not None

    # Simulate a consumer's template tree at templates/cotton/myapp/foo.html
    consumer_root = tmp_path / "templates"
    consumer_template = consumer_root / "cotton" / "myapp" / "foo.html"
    consumer_template.parent.mkdir(parents=True)
    consumer_template.write_text("consumer-foo-content")

    # Engine with APP_DIRS=True walks INSTALLED_APPS for templates,
    # exactly like Django's default get_template() flow.
    engine = Engine(
        dirs=[str(consumer_root)],
        app_dirs=True,
        libraries={"cf_ui": "cf_ui.templatetags.cf_ui"},
    )

    from django.template import Context

    # Consumer template at cotton/myapp/foo.html resolves cleanly —
    # the regression made this raise TemplateDoesNotExist because
    # the Cotton lookup got rewritten to cotton/bulma/myapp/foo.html.
    consumer_t = engine.get_template("cotton/myapp/foo.html")
    assert "consumer-foo-content" in consumer_t.render(Context({}))
    assert str(consumer_template) == consumer_t.origin.name

    # cf-ui's templates also resolve under the default Cotton path.
    cf_ui_t = engine.get_template("cotton/cf/notification.html")
    assert cf_ui_t is not None
    # Sanity-check we found cf-ui's actual file, not a same-named consumer one.
    assert "cf_ui" in (cf_ui_t.origin.name or "")


def test_all_cf_ui_cotton_components_resolve_at_cotton_cf_path():
    """Every cf-ui cotton component must be reachable at cotton/cf/<name>.html."""
    from django.template.engine import Engine

    engine = Engine(
        app_dirs=True,
        libraries={"cf_ui": "cf_ui.templatetags.cf_ui"},
    )
    expected = [
        "breadcrumb",
        "card",
        "checkbox-group",
        "form-field",
        "modal",
        "navbar",
        "notification",
        "pagination",
        "panel",
        "progress",
        "select",
        "table",
        "tabs",
        "textarea",
    ]
    for name in expected:
        t = engine.get_template(f"cotton/cf/{name}.html")
        assert t is not None
