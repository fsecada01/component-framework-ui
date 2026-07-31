"""No dependency may be resolved from git once it is on PyPI (#50).

`[tool.uv.sources]` does not travel into wheel metadata, so a git pin there is
invisible to consumers — the published `cf-ui` 0.2.0 carries a bare
`Requires-Dist: component-framework>=0.6`, exactly as it should. That
invisibility is the hazard: CI runs `uv pip install -e ".[dev]"`, which
*does* honour the sources table, so the suite silently tested against git
master instead of the release.

It was not hypothetical. Before this ticket the dev environment resolved
`component-framework` **0.6.0b0** from commit 2833311 while 0.6.0 was live on
PyPI — a pre-release, from a tree nobody installs.

The pin was correct while nothing was published. The failure mode is
forgetting to remove it afterwards, which nothing would have surfaced, so it
is pinned here instead.
"""

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

#: Sources that pull a dependency from somewhere other than an index.
#: ``workspace`` and ``editable`` are excluded deliberately — those are local
#: layout, not a substitute for a release.
NON_INDEX_KEYS = {"git", "url", "path"}


def _sources() -> dict[str, dict]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data.get("tool", {}).get("uv", {}).get("sources", {})


def _offending(sources: dict[str, dict]) -> list[tuple[str, str]]:
    """``[(dependency, source kind)]`` for every non-index source."""
    out = []
    for name, spec in sources.items():
        if not isinstance(spec, dict):
            continue
        for key in NON_INDEX_KEYS:
            if key in spec:
                out.append((name, key))
    return out


def test_no_dependency_is_pinned_to_a_non_index_source():
    offenders = _offending(_sources())
    assert not offenders, (
        f"pyproject.toml resolves {offenders} from outside an index. "
        "That never reaches consumers — which is the problem: CI honours "
        "[tool.uv.sources], so the suite would test a tree nobody installs "
        "while the wheel depends on a release. See #50."
    )


def test_the_component_framework_floor_matches_what_is_published():
    """`>=0.4` claimed a range that was only ever tagged as pre-releases.

    Not asserting an exact version — the floor is allowed to rise. Asserting
    it does not sit below 0.6, the first and only final release, because a
    specifier without a pre-release marker resolves to a pre-release only when
    no final exists, and that fallback is what produced 0.6.0b0 locally.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    req = next(
        Requirement(d)
        for d in data["project"]["dependencies"]
        if Requirement(d).name == "component-framework"
    )

    assert not req.specifier.contains(Version("0.5.0")), (
        f"component-framework{req.specifier} admits 0.5.0, which was never "
        "released as a final — only as a `b0` tag. The floor should name a "
        "version that exists on PyPI."
    )


def test_the_installed_component_framework_did_not_come_from_git():
    """The empirical half: check the *installed* distribution, not the file.

    A clean pyproject proves nothing about the environment the suite is
    running in — a stale venv keeps serving whatever the pin last resolved.
    pip and uv both record a non-index install in ``direct_url.json`` (PEP
    610), so its presence with a vcs entry is the tell.
    """
    import importlib.metadata as md

    try:
        dist = md.distribution("component-framework")
    except md.PackageNotFoundError:
        pytest.skip("component-framework is not installed in this environment")

    direct_url = dist.read_text("direct_url.json")
    if direct_url is None:
        return  # came from an index, which is the point

    import json

    info = json.loads(direct_url)
    assert "vcs_info" not in info, (
        f"component-framework {dist.version} is installed from "
        f"{info.get('url')!r}, not from an index. This environment is not "
        "testing what consumers install — reinstall after removing the pin."
    )


# ── The guard's own behaviour, pinned ─────────────────────────────────────


@pytest.mark.parametrize(
    ("sources", "expected"),
    [
        ({}, []),
        ({"cf": {"git": "https://example.invalid/x.git"}}, [("cf", "git")]),
        ({"foo": {"url": "https://example.invalid/foo.whl"}}, [("foo", "url")]),
        ({"foo": {"path": "../foo"}}, [("foo", "path")]),
        # A workspace member is local layout, not a stand-in for a release.
        ({"foo": {"workspace": True}}, []),
        ({"foo": {"index": "testpypi"}}, []),
    ],
    ids=lambda v: str(v)[:44],
)
def test_the_source_check_flags_what_it_claims_to(sources: dict, expected: list):
    assert _offending(sources) == expected


def test_the_sources_lookup_agrees_with_the_raw_file():
    """Guards against the accessor returning ``{}`` for the wrong reason.

    A wrong key path would make ``_sources()`` empty forever, and the main
    test would pass forever with it — the classic vacuous guard. So the
    parsed view is pinned against the raw text in both directions: the table
    is present in one iff it is present in the other.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    assert tomllib.loads(text)["project"]["name"] == "cf-ui", "parsing the wrong file"

    header_present = re.search(r"^\[tool\.uv\.sources\]", text, re.M) is not None
    assert bool(_sources()) == header_present, (
        "the [tool.uv.sources] header and the parsed table disagree — the "
        "accessor is walking a key path uv does not read"
    )
