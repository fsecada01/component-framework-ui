"""The version is declared twice, so something has to check they agree (#63).

``pyproject.toml`` carries it because that is what hatchling builds the wheel
from and what ``release.yml`` compares the git tag against.
``src/cf_ui/_version.py`` carries it because ``cf_ui.__version__`` has to
answer at runtime without reading package metadata.

Nothing connected the two. The release workflow's tag-match step reads
``pyproject.toml`` only, so a bump that missed ``_version.py`` would publish a
correctly-named wheel whose ``cf_ui.__version__`` reported the *previous*
version — indefinitely, and with every gate green. This lives in the unit
suite rather than in ``release.yml`` on purpose: the drift is introduced when
the bump commit is written, and that is when it should fail, not at the tag.
"""

import re
import tomllib
from pathlib import Path

import cf_ui

PYPROJECT = Path(__file__).parent.parent.parent / "pyproject.toml"


def _declared_version() -> str:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def test_pyproject_and_dunder_version_agree():
    assert cf_ui.__version__ == _declared_version(), (
        f"cf_ui.__version__ is {cf_ui.__version__!r} but pyproject.toml declares "
        f"{_declared_version()!r} — bump both, or the published wheel reports a "
        f"version its own metadata contradicts"
    )


def test_version_is_pep440_release():
    """A stray suffix would sort wrong on PyPI and break the tag comparison.

    ``release.yml`` asserts ``pyproject`` == ``${tag#v}`` as a literal string,
    so `0.3.0.dev0` left in by accident fails there — but only at the tag,
    after the commit is already on master.
    """
    assert re.fullmatch(r"\d+\.\d+\.\d+", _declared_version()), (
        f"{_declared_version()!r} is not a plain X.Y.Z release version"
    )
