"""
Django settings for E2E tests only.

This module is used by the E2E server subprocess. It explicitly includes
django_cotton in INSTALLED_APPS so that cf-ui cotton components render fully.

It MUST NOT be imported by the main pytest process to avoid polluting
the shared Django settings used by unit and integration tests.
"""

from pathlib import Path

from cf_ui import JINJA_TEMPLATES_DIR

BASE_DIR = Path(__file__).parent.parent / "integration" / "cotton_app"

# cf-ui templates root — contains cotton/cf/*.html (theme-agnostic path)
CF_UI_TEMPLATES_ROOT = JINJA_TEMPLATES_DIR.parent.parent

SECRET_KEY = "e2e-test-secret-key-not-for-production"
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django_cotton",
    "cf_ui.django.CfUiConfig",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            CF_UI_TEMPLATES_ROOT,  # provides cotton/cf/*.html
            BASE_DIR / "templates",  # provides cotton_gallery/*.html
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
            "libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"},
        },
    }
]
CF_UI_THEME = "bulma"
# django-cotton default COTTON_DIR="cotton" resolves <c-cf.card> ->
# cotton/cf/card.html, picked up via APP_DIRS from cf_ui's package templates.
# Allow hyphenated filenames (form-field.html, checkbox-group.html)
COTTON_SNAKE_CASED_NAMES = False
ROOT_URLCONF = "tests.integration.cotton_app.urls"
STATIC_URL = "/static/"
