from pathlib import Path


def test_jinja_templates_dir_exported():
    from cf_ui import JINJA_TEMPLATES_DIR
    assert isinstance(JINJA_TEMPLATES_DIR, Path)
    assert JINJA_TEMPLATES_DIR.exists()
    assert (JINJA_TEMPLATES_DIR / "bulma").exists()


def test_cotton_templates_dir_exported():
    from cf_ui import COTTON_TEMPLATES_DIR
    assert isinstance(COTTON_TEMPLATES_DIR, Path)
    assert COTTON_TEMPLATES_DIR.exists()
    assert (COTTON_TEMPLATES_DIR / "bulma").exists()


def test_jinja_templates_dir_points_inside_package():
    from cf_ui import JINJA_TEMPLATES_DIR
    import cf_ui
    package_root = Path(cf_ui.__file__).parent
    assert str(JINJA_TEMPLATES_DIR).startswith(str(package_root))


def test_django_appconfig_name():
    from django.apps import apps
    app = apps.get_app_config("cf_ui")
    assert app is not None


def test_django_appconfig_ready_registers_cotton_dirs():
    from django.conf import settings
    from cf_ui import COTTON_TEMPLATES_DIR
    theme_dir = COTTON_TEMPLATES_DIR / "bulma"
    assert any(
        str(d) == str(theme_dir) for d in getattr(settings, "COTTON_DIRS", [])
    )


def test_fastapi_install_cf_ui_adds_template_dir():
    from unittest.mock import MagicMock
    from cf_ui.fastapi import install_cf_ui
    from cf_ui import JINJA_TEMPLATES_DIR

    catalog = MagicMock()
    install_cf_ui(catalog, theme="bulma")

    catalog.add_path.assert_called_once_with(
        JINJA_TEMPLATES_DIR / "bulma", prefix="Cf"
    )


def test_litestar_install_cf_ui_adds_template_dir():
    from unittest.mock import MagicMock
    from cf_ui.litestar import install_cf_ui
    from cf_ui import JINJA_TEMPLATES_DIR

    config = MagicMock()
    config.directory = []
    install_cf_ui(config, theme="bulma")

    assert JINJA_TEMPLATES_DIR / "bulma" in config.directory
