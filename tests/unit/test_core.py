import re
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
    assert (COTTON_TEMPLATES_DIR / "cf").exists()
    assert (COTTON_TEMPLATES_DIR / "cf" / "card.html").exists()


def test_jinja_templates_dir_points_inside_package():
    import cf_ui
    from cf_ui import JINJA_TEMPLATES_DIR

    package_root = Path(cf_ui.__file__).parent
    assert str(JINJA_TEMPLATES_DIR).startswith(str(package_root))


def test_django_appconfig_name():
    from django.apps import apps

    app = apps.get_app_config("cf_ui")
    assert app is not None


def test_django_appconfig_does_not_override_cotton_dir():
    """cf-ui must not set COTTON_DIR; doing so breaks consumer cotton trees.

    cf-ui templates live at cotton/cf/*.html so the django-cotton default
    (COTTON_DIR="cotton") resolves <c-cf.foo>. Consumers keep whatever value
    they configured (or the default).
    """
    from django.conf import settings

    cf_ui_managed_value = "cotton/bulma"
    assert getattr(settings, "COTTON_DIR", None) != cf_ui_managed_value


def test_fastapi_install_cf_ui_adds_template_dir():
    from unittest.mock import MagicMock

    from cf_ui import JINJA_TEMPLATES_DIR
    from cf_ui.fastapi import install_cf_ui

    catalog = MagicMock()
    install_cf_ui(catalog, theme="bulma")

    catalog.add_folder.assert_called_once_with(JINJA_TEMPLATES_DIR / "bulma", prefix="Cf")


def test_litestar_install_cf_ui_adds_template_dir():
    from unittest.mock import MagicMock

    from cf_ui import JINJA_TEMPLATES_DIR
    from cf_ui.litestar import install_cf_ui

    config = MagicMock()
    config.directory = []
    install_cf_ui(config, theme="bulma")

    assert JINJA_TEMPLATES_DIR / "bulma" in config.directory


def test_litestar_install_cf_ui_wraps_single_dir():
    from pathlib import Path
    from unittest.mock import MagicMock

    from cf_ui import JINJA_TEMPLATES_DIR
    from cf_ui.litestar import install_cf_ui

    config = MagicMock()
    config.directory = Path("/some/dir")
    install_cf_ui(config, theme="bulma")
    assert config.directory == [Path("/some/dir"), JINJA_TEMPLATES_DIR / "bulma"]


def test_version_exported():
    from cf_ui import __version__

    assert isinstance(__version__, str)
    # Shape only — the value is asserted against pyproject.toml below rather
    # than restated here. A literal in this file is a third place to edit and
    # the one most likely to be missed, since it fails loudly enough to be
    # "fixed" by updating the number without checking the other two.
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-.]?(?:a|b|rc|dev)\d*)?", __version__), __version__


def test_the_two_version_sources_agree():
    """``pyproject.toml`` and ``_version.py`` both state the version (#38).

    Nothing connected them. A bump that lands in one ships a wheel whose
    metadata disagrees with ``cf_ui.__version__`` — installed consumers see one
    number, ``pip show`` another — and no test could tell, because the only
    assertion on the version was a literal that matched whichever file the
    editor happened to open.

    Read from source rather than from installed metadata: the package is
    installed editable in dev and in CI, so ``importlib.metadata`` can serve a
    version cached at install time and report agreement that a fresh build
    would not have.
    """
    import tomllib

    from cf_ui import __version__

    pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]

    assert __version__ == declared, (
        f"cf_ui.__version__ is {__version__!r} but pyproject.toml declares "
        f"{declared!r} — bump both, or the wheel's metadata lies about itself."
    )
