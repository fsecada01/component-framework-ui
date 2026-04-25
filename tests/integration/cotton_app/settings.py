from pathlib import Path

BASE_DIR = Path(__file__).parent

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "cf_ui.django.CfUiConfig",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
            "libraries": {"cf_ui": "cf_ui.templatetags.cf_ui"},
        },
    }
]
CF_UI_THEME = "bulma"
ROOT_URLCONF = "tests.integration.cotton_app.urls"
STATIC_URL = "/static/"
