"""The documented extras must match the extras ``pyproject.toml`` declares (#47).

Two defects motivated this, both invisible to every existing guard:

* ``[litestar]`` was documented as "Litestar 2.0+, Jinja2 3.1+" long after #44
  added ``jinjax`` to it. Harmless to installs, but the omission read as
  "Litestar is the non-JinjaX path" — the exact misconception #42 was about —
  because the ``[fastapi]`` line right above it *does* name JinjaX.
* ``django-cotton>=0.9`` admitted 0.9.0–0.9.5, which predate the
  ``<c-props>`` → ``<c-vars>`` rename (django-cotton v0.9.6). Every cotton
  wrapper here uses ``<c-vars>``, so those versions install cleanly and then
  drop every prop.

``test_docs_samples.py`` could see neither: it validates Python samples and
link targets, and these are prose claims about packaging metadata.

The README is cf-ui's PyPI landing page, so a stale extras list is not an
internal docs problem — it is the description shipped to every visitor.
"""

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

#: The files that describe the extras to *consumers*. Fixing one and
#: forgetting the other is how the drift lasted two releases, so both are
#: checked — but they carry different obligations, see below.
README = REPO_ROOT / "README.md"
INSTALL_DOC = REPO_ROOT / "docs" / "installation.md"
DOC_FILES = [README, INSTALL_DOC]

#: Contributor-facing extras, deliberately absent from the consumer docs.
#: Anything else added to ``optional-dependencies`` must be documented — that
#: is the point of deriving the list rather than hand-writing it.
UNDOCUMENTED_EXTRAS = {"dev", "docs"}

#: ``docs/installation.md`` is the reference and must list every public extra.
#: The README is a summary and is only required to carry the web-framework
#: extras — but whatever it *does* describe has to be complete, because an
#: extra listed with half its contents is worse than one left out.
README_REQUIRED_EXTRAS = {"django", "fastapi", "litestar"}


def _declared_extras() -> dict[str, list[str]]:
    """``{extra: [distribution names]}`` from pyproject, self-references dropped.

    ``cf-ui[...]`` entries (as in ``all`` and ``dev``) are recursive markers,
    not dependencies a reader would expect named in prose.
    """
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    out = {}
    for extra, specs in data["project"]["optional-dependencies"].items():
        names = []
        for spec in specs:
            # "uvicorn[standard]>=0.27.0" -> "uvicorn"
            name = re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].strip()
            if name and name != "cf-ui":
                names.append(name)
        out[extra] = names
    return out


def _documented_line(text: str, extra: str) -> str | None:
    """The line describing ``[extra]``, in either the README's list or the
    docs table. Returns None if the extra is not described at all.

    The two files use different markup for the same information::

        - `[litestar]` — Litestar 2.0+, Jinja2 3.1+, JinjaX 0.41+
        | `[litestar]` | Litestar 2.0+, Jinja2 3.1+, JinjaX 0.41+ |

    so this matches on the backticked extra name and returns the whole line
    rather than trying to parse either shape.
    """
    for line in text.splitlines():
        if f"`[{extra}]`" in line:
            return line
        # The docs table groups the theme markers on one line:
        # | `[bulma]` `[bootstrap]` ... | nothing — theme markers |
        if re.search(rf"`\[[^`]*\b{re.escape(extra)}\b[^`]*\]`", line):
            return line
    return None


def _names_in(prose: str) -> set[str]:
    """Distribution names mentioned in a line of prose.

    Two subtleties, each one a way an earlier cut of this guard passed a line
    that was actually missing a package:

    * The backticked ``` `[django]` ``` marker naming the extra is stripped
      first. Otherwise the ``django`` distribution counts as "mentioned"
      purely because the extra shares its name, and ``[django]`` validates
      with Django itself absent from the description.
    * Matching is token-bounded, not substring: ``django`` must not be found
      inside ``django-cotton``.
    """
    prose = re.sub(r"`\[[^`]*\]`", " ", prose)
    return {token.lower() for token in re.findall(r"(?<![\w-])[A-Za-z][\w-]*(?![\w-])", prose)}


def _missing(prose: str, packages: list[str]) -> list[str]:
    mentioned = _names_in(prose)
    return [p for p in packages if p.lower() not in mentioned]


DOCUMENTED = [e for e in _declared_extras() if e not in UNDOCUMENTED_EXTRAS]


@pytest.mark.parametrize("extra", DOCUMENTED)
def test_the_installation_reference_documents_every_declared_extra(extra: str):
    """``docs/installation.md`` is the reference — nothing may be missing."""
    assert _documented_line(INSTALL_DOC.read_text(encoding="utf-8"), extra) is not None, (
        f"docs/installation.md never mentions the `[{extra}]` extra, but "
        f"pyproject.toml declares it. A consumer extra nobody documented is "
        f"one nobody can find."
    )


@pytest.mark.parametrize("extra", sorted(README_REQUIRED_EXTRAS))
def test_the_readme_documents_the_web_framework_extras(extra: str):
    """The README is a summary, but these three are the reason to install at all."""
    assert _documented_line(README.read_text(encoding="utf-8"), extra) is not None, (
        f"README.md does not describe the `[{extra}]` extra. It is cf-ui's "
        f"PyPI landing page — this is where a visitor decides what to install."
    )


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: p.name)
@pytest.mark.parametrize("extra", DOCUMENTED)
def test_every_package_in_an_extra_is_named_where_it_is_documented(extra: str, doc: Path):
    """Whatever a file describes, it describes completely.

    Deliberately not conditioned on the file being *required* to carry the
    extra: the README may omit `[bulma]` entirely, but if it names it, the
    description has to be true.
    """
    packages = _declared_extras()[extra]
    if not packages:
        pytest.skip(f"`[{extra}]` is a marker extra with no payload")

    line = _documented_line(doc.read_text(encoding="utf-8"), extra)
    if line is None:
        pytest.skip(f"{doc.name} does not describe `[{extra}]`")

    missing = _missing(line, packages)
    assert not missing, (
        f"{doc.name} describes `[{extra}]` as:\n    {line.strip()}\n"
        f"but pyproject.toml also declares {missing}. Add them — this file is "
        f"how a reader decides what an extra costs them."
    )


def test_the_django_extra_floor_excludes_the_c_props_era():
    """``<c-vars>`` is 0.9.6+; every wrapper here uses it (#47).

    django-cotton renamed ``<c-props>`` to ``<c-vars>`` in v0.9.6
    (wrabit/django-cotton#15, a declared breaking change). A floor at or below
    0.9.5 resolves a version where all 14 wrappers install fine and then
    silently drop every prop — the failure shape that has bitten this repo
    before. The floor is set at the major series actually tested, not at the
    bare syntax minimum.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    spec = next(
        Requirement(s)
        for s in tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"][
            "optional-dependencies"
        ]["django"]
        if Requirement(s).name == "django-cotton"
    )

    assert not spec.specifier.contains(Version("0.9.5")), (
        f"django-cotton{spec.specifier} admits 0.9.5, which predates the "
        "<c-props> -> <c-vars> rename in 0.9.6. Every cotton wrapper here uses "
        "<c-vars>, so that resolution installs cleanly and drops every prop."
    )


def test_every_cotton_wrapper_uses_the_syntax_the_floor_guarantees():
    """The premise the floor rests on, kept executable.

    If a wrapper ever reverts to ``<c-vars>``-free markup the floor above is
    arguing about nothing, and this test says so rather than passing quietly.
    """
    wrappers = sorted((REPO_ROOT / "src" / "cf_ui" / "templates" / "cotton" / "cf").glob("*.html"))
    assert len(wrappers) == 14, f"expected 14 cotton wrappers, found {len(wrappers)}"

    without = [w.name for w in wrappers if "<c-vars" not in w.read_text(encoding="utf-8")]
    assert not without, f"wrappers with no <c-vars> declaration: {without}"


# ── The guard's own behaviour, pinned ─────────────────────────────────────
#
# A parser that stops matching reports clean forever. Each case below is a
# shape that actually appears in the two files, plus the two failure modes
# the real defects took.

PARSER_CASES = [
    # (prose, packages, expected missing)
    ("- `[litestar]` — Litestar 2.0+, Jinja2 3.1+", ["litestar", "jinja2", "jinjax"], ["jinjax"]),
    (
        "- `[litestar]` — Litestar 2.0+, Jinja2 3.1+, JinjaX 0.41+",
        ["litestar", "jinja2", "jinjax"],
        [],
    ),
    # The trap: `django` must not count as present via `django-cotton`.
    ("| `[django]` | django-cotton 2.x |", ["django", "django-cotton"], ["django"]),
    ("| `[django]` | Django 4.2+, django-cotton 2.x |", ["django", "django-cotton"], []),
    # The extra's own marker must not stand in for the package of that name:
    # `[django]` names the extra, it does not say Django is installed.
    ("| `[django]` | django-cotton 2.x |", ["django"], ["django"]),
    ("- `[fastapi]` — FastAPI 0.109+, JinjaX 0.41+, uvicorn", ["uvicorn", "jinjax"], []),
]


@pytest.mark.parametrize(("prose", "packages", "expected"), PARSER_CASES, ids=lambda v: str(v)[:40])
def test_the_parser_flags_what_it_claims_to(prose: str, packages: list[str], expected: list[str]):
    assert _missing(prose, packages) == expected


def test_the_extra_lookup_finds_both_markup_shapes():
    readme_shape = "- `[litestar]` — Litestar 2.0+"
    table_shape = "| `[litestar]` | Litestar 2.0+ |"
    grouped = "| `[bulma]` `[bootstrap]` | nothing — theme markers |"

    assert _documented_line(readme_shape, "litestar") == readme_shape
    assert _documented_line(table_shape, "litestar") == table_shape
    assert _documented_line(grouped, "bootstrap") == grouped
    assert _documented_line(readme_shape, "django") is None


def test_the_parametrized_extras_list_is_not_empty():
    """A guard over an empty list passes. This is what keeps it honest."""
    assert len(DOCUMENTED) >= 8, DOCUMENTED
    assert "litestar" in DOCUMENTED and "django" in DOCUMENTED
