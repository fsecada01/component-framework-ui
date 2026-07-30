"""The documentation's code samples are checked against the real package (#39).

Prose rots silently. Two live bugs were sitting in README.md when this suite
was written, both of which read perfectly:

* ``from jinjax import ComponentCatalog`` — jinjax exports ``Catalog``; that
  import raises ``ImportError`` on the first line of the FastAPI quickstart.
* ``<CfCard>`` — ``Cf`` is a JinjaX *prefix* and the prefix separator is
  ``:``, so the documented tag raises ``ComponentNotFound``. ``<Cf.Card>``
  fails too; only ``<Cf:Card>`` resolves.

Neither is the kind of thing review catches, because both are what you would
guess the API looks like. So the docs are parsed and their claims executed:
every ``python`` block must parse, every name imported from an installed
module must actually exist on it, and every component referenced anywhere in
the docs must be one the package ships.
"""

import ast
import importlib
import re
import textwrap
from pathlib import Path

import pytest

from cf_ui import JINJA_TEMPLATES_DIR
from cf_ui.themes import COMPONENTS

REPO_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"

#: Fenced blocks, including the 4-space-indented ones inside `=== "Tab"`
#: containers — the closing fence must match the opening fence's indent.
FENCE = re.compile(r"^([ \t]*)```(\w+)?[^\n]*\n(.*?)^\1```", re.M | re.S)

#: `Cf:Card`, in a tag, in a `catalog.render("...")`, or in a prose backtick.
JINJA_COMPONENT = re.compile(r"\bCf:([A-Z]\w*)")

#: `<c-cf.form-field ...>` — the django-cotton public wrappers.
COTTON_COMPONENT = re.compile(r"<c-cf\.([a-z][a-z0-9-]*)")

#: The tag shape that does not resolve. Banned inside code fences only: the
#: pages that warn about it necessarily name it in prose.
BROKEN_JINJA_TAG = re.compile(r"<Cf[A-Z.]")


def _markdown_files() -> list[Path]:
    return sorted([REPO_ROOT / "README.md", *DOCS_DIR.glob("*.md")])


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _blocks(path: Path) -> list[tuple[str, str]]:
    """(language, dedented source) for each fenced block in the file."""
    text = path.read_text(encoding="utf-8")
    return [(m.group(2) or "", textwrap.dedent(m.group(3))) for m in FENCE.finditer(text)]


MARKDOWN_FILES = _markdown_files()


def test_the_doc_set_the_guard_walks_is_not_empty():
    """A guard over an empty glob passes. Pin what it is supposed to cover."""
    names = {p.name for p in MARKDOWN_FILES}
    assert "README.md" in names
    for expected in ("index.md", "quickstart.md", "components.md", "escaping.md"):
        assert expected in names, f"{expected} missing from the docs set"


# ── Python samples parse, and their imports resolve ───────────────────────


def _python_blocks() -> list[tuple[Path, str]]:
    out = []
    for path in MARKDOWN_FILES:
        for lang, source in _blocks(path):
            if lang == "python":
                out.append((path, source))
    return out


PYTHON_BLOCKS = _python_blocks()


@pytest.mark.parametrize(
    ("path", "source"),
    PYTHON_BLOCKS,
    ids=[f"{_rel(p)}:{i}" for i, (p, _) in enumerate(PYTHON_BLOCKS)],
)
def test_every_python_sample_parses(path: Path, source: str):
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"{_rel(path)}: sample does not parse: {exc}\n\n{source}")


def _imported_names() -> list[tuple[Path, str, str]]:
    """(file, module, name) for every ``from module import name`` in the docs.

    Blocks that do not parse are skipped here rather than raising at collection
    time — ``test_every_python_sample_parses`` is what reports those, and a
    collection error would hide every other finding in this module behind it.
    """
    out = []
    for path, source in PYTHON_BLOCKS:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                for alias in node.names:
                    out.append((path, node.module, alias.name))
    return out


IMPORTED_NAMES = _imported_names()


@pytest.mark.parametrize(
    ("path", "module", "name"),
    IMPORTED_NAMES,
    ids=[f"{m}.{n}" for _, m, n in IMPORTED_NAMES],
)
def test_every_documented_import_exists(path: Path, module: str, name: str):
    """``from jinjax import ComponentCatalog`` is the bug this test exists for.

    Modules that are not installed here are skipped rather than failed — the
    docs legitimately mention frameworks outside this suite's dependency set.
    ``test_the_import_check_is_not_all_skips`` keeps that from hollowing the
    check out.
    """
    try:
        mod = importlib.import_module(module)
    except ImportError:
        pytest.skip(f"{module} is not installed in this environment")

    assert hasattr(mod, name), (
        f"{_rel(path)} documents `from {module} import {name}`, but {module} exposes no such name."
    )


def test_the_import_check_is_not_all_skips():
    """At least the imports that matter must have been really checked.

    Every one of these is installed wherever the unit suite runs, so a skip
    here means the sample stopped being documented, not that the environment
    is thin.
    """
    checked = {(m, n) for _, m, n in IMPORTED_NAMES}
    for required in [
        ("jinjax", "Catalog"),
        ("cf_ui.fastapi", "install_cf_ui"),
        ("cf_ui.litestar", "install_cf_ui"),
        ("markupsafe", "Markup"),
    ]:
        assert required in checked, (
            f"no doc sample imports {required[1]} from {required[0]} any more — "
            "either the docs regressed or this list is stale."
        )


# ── Component references name components that exist ───────────────────────


def _jinja_component_names() -> set[str]:
    return {p.stem for p in (JINJA_TEMPLATES_DIR / "bulma").glob("*.jinja")}


def _referenced(pattern: re.Pattern[str]) -> list[tuple[Path, str]]:
    out = []
    for path in MARKDOWN_FILES:
        text = path.read_text(encoding="utf-8")
        for name in sorted(set(pattern.findall(text))):
            out.append((path, name))
    return out


JINJA_REFS = _referenced(JINJA_COMPONENT)
COTTON_REFS = _referenced(COTTON_COMPONENT)


@pytest.mark.parametrize(
    ("path", "name"), JINJA_REFS, ids=[f"{_rel(p)}:Cf:{n}" for p, n in JINJA_REFS]
)
def test_every_documented_jinjax_component_exists(path: Path, name: str):
    known = _jinja_component_names()
    assert name in known, (
        f"{_rel(path)} references `Cf:{name}`, which is not a shipped "
        f"component. Known: {', '.join(sorted(known))}"
    )


@pytest.mark.parametrize(
    ("path", "name"), COTTON_REFS, ids=[f"{_rel(p)}:c-cf.{n}" for p, n in COTTON_REFS]
)
def test_every_documented_cotton_component_exists(path: Path, name: str):
    assert name in COMPONENTS, (
        f"{_rel(path)} references `<c-cf.{name}>`, which is not a shipped "
        f"component. Known: {', '.join(COMPONENTS)}"
    )


def test_the_component_reference_check_covers_both_engines():
    """Both regexes must actually be matching something."""
    assert len(JINJA_REFS) >= 10, f"only {len(JINJA_REFS)} JinjaX references found"
    assert len(COTTON_REFS) >= 10, f"only {len(COTTON_REFS)} cotton references found"


@pytest.mark.parametrize("path", MARKDOWN_FILES, ids=_rel)
def test_no_code_sample_uses_the_tag_form_that_does_not_resolve(path: Path):
    """``<CfCard>`` and ``<Cf.Card>`` both raise ``ComponentNotFound``.

    Prose may name them — the quickstart and the component reference both warn
    about them explicitly — so this looks only inside code fences, where an
    occurrence is a sample telling the reader to write something broken.
    """
    for lang, source in _blocks(path):
        match = BROKEN_JINJA_TAG.search(source)
        assert match is None, (
            f"{_rel(path)}: a {lang or 'plain'} sample contains "
            f"{source[match.start() : match.start() + 20]!r} — JinjaX needs the "
            "prefix separator, as in `<Cf:Card>`."
        )


# ── The two tag forms really do behave as documented ──────────────────────


def test_the_documented_tag_form_resolves_and_the_others_do_not(tmp_path: Path):
    """Executable backing for the warnings in quickstart.md and components.md.

    Without this the docs would merely *assert* that `<Cf:Card>` is the working
    form; here the claim is rendered.
    """
    from jinjax import Catalog
    from jinjax.exceptions import ComponentNotFound

    catalog = Catalog()
    catalog.add_folder(JINJA_TEMPLATES_DIR / "bulma", prefix="Cf")
    catalog.add_folder(tmp_path)

    def render(tag: str) -> str:
        (tmp_path / "Wrapper.jinja").write_text("{#def #}\n" + tag + "\n", encoding="utf-8")
        catalog._cache.clear()
        return catalog.render("Wrapper")

    html = render('<Cf:Card header="Title">Body</Cf:Card>')
    assert "Title" in html and "Body" in html

    for broken in ['<CfCard header="T">B</CfCard>', '<Cf.Card header="T">B</Cf.Card>']:
        with pytest.raises(ComponentNotFound):
            render(broken)


def test_slot_content_from_python_uses_the_underscore_prefix():
    """``content`` is reserved by JinjaX; the docs say to pass ``_content``."""
    from jinjax import Catalog

    catalog = Catalog()
    catalog.add_folder(JINJA_TEMPLATES_DIR / "bulma", prefix="Cf")

    html = catalog.render("Cf:Card", header="Welcome", _content="Card body.")
    assert "Welcome" in html
    assert "Card body." in html
