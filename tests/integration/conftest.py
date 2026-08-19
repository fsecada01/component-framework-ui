"""
Integration test configuration.

Django can only be set up once per process, so this tier must never share a
pytest process with tests/unit — see the justfile's `test-all` recipe and
.github/workflows/ci.yml, which both run tests/unit and tests/integration as
separate invocations for exactly this reason. django-cotton's
AppConfig.ready() (see tests/integration/cotton_app/settings.py) mutates
settings.TEMPLATES in place and resets Django's global template-engine cache
the moment it's in INSTALLED_APPS, so a combined process would leak real
cotton compilation into the unit tier's render_to_string calls.

This conftest sets DJANGO_SETTINGS_MODULE before collection begins so Django
configures from tests/integration/cotton_app/settings — the settings module
this tier actually needs cotton registered under.
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


def pytest_collection_modifyitems(items):
    """Fail fast if tests/unit and tests/integration get collected together.

    A bare `pytest` (pyproject.toml's `testpaths = ["tests"]` default),
    `pytest tests/`, or an IDE "run all tests" still collects both tiers
    into one process — silently reintroducing the settings.TEMPLATES leak
    this conftest's docstring describes, as hundreds of unrelated unit
    failures rather than an obvious error. Catch it here instead.
    """
    has_unit = any(item.nodeid.startswith("tests/unit/") for item in items)
    has_integration = any(item.nodeid.startswith("tests/integration/") for item in items)
    if has_unit and has_integration:
        raise pytest.UsageError(
            "tests/unit and tests/integration were collected into the same "
            "pytest process. django-cotton's AppConfig.ready() mutates "
            "Django's global template settings once tests/integration "
            "registers it, which silently breaks tests/unit's "
            "render_to_string calls. Run the tiers separately — "
            "`just test-all`, or `pytest tests/unit` then "
            "`pytest tests/integration`."
        )


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
