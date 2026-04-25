"""
Integration test configuration.

Django can only be set up once per process. When running the full test suite,
tests/unit/conftest.py configures Django first with minimal settings. This
conftest handles the case where we run integration tests in isolation (so
Django is NOT yet configured) by setting DJANGO_SETTINGS_MODULE before
collection begins.

When the full suite runs together, the unit conftest already configured Django.
The cotton integration tests use Django's test Client which works regardless of
which settings module was used to configure Django, as long as the required
apps (cf_ui.django.CfUiConfig) are in INSTALLED_APPS — which they are in both
settings modules.

The ROOT_URLCONF setting differs: unit tests don't set it, integration tests
need it. The session-scoped fixture below ensures ROOT_URLCONF is set for all
integration tests regardless of which conftest configured Django first.
"""

import os

import django
import pytest
from django.conf import settings


def pytest_configure(config):
    if not settings.configured:
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "tests.integration.cotton_app.settings",
        )
        django.setup()


@pytest.fixture(scope="session", autouse=True)
def _set_root_urlconf():
    """Ensure ROOT_URLCONF is set for integration URL routing."""
    original = getattr(settings, "ROOT_URLCONF", None)
    settings.ROOT_URLCONF = "tests.integration.cotton_app.urls"
    yield
    if original is None:
        if hasattr(settings, "ROOT_URLCONF"):
            delattr(settings, "ROOT_URLCONF")
    else:
        settings.ROOT_URLCONF = original
