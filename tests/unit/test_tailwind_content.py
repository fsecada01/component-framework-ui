"""Tailwind tree-shaking guards for the DaisyUI theme (issue #6).

DaisyUI sits on Tailwind, so a consuming app builds its own CSS. Every class
cf-ui's templates use has to be visible to Tailwind's content scanner, or it
is shaken out and the page renders unstyled. That fails silently — nothing
errors, the markup is just naked.

There are exactly two ways it happens, and both are tested here:

1. The content glob does not reach the installed package's templates.
2. A class name is assembled at render time (``alert-{{ type }}``), so the
   complete token never appears in the source the scanner reads.
"""

import glob as globlib
import re
from pathlib import Path

import pytest

PKG_DIR = Path(__file__).parent.parent.parent / "src" / "cf_ui"
TEMPLATES_DIR = PKG_DIR / "templates"

DAISY_TEMPLATES = sorted(
    [*(TEMPLATES_DIR / "jinja" / "daisy").glob("*.jinja")]
    + [*(TEMPLATES_DIR / "cotton" / "_themes" / "daisy").glob("*.html")]
)


# --- Failure mode 1: the glob does not reach the templates -----------------


def test_tailwind_content_globs_are_published():
    from cf_ui.themes import tailwind_content_globs

    patterns = tailwind_content_globs()
    assert patterns, "no content globs published"
    assert all(isinstance(p, str) for p in patterns)


def test_content_globs_resolve_to_absolute_paths():
    """A consumer's tailwind.config.js lives elsewhere — relative would break."""
    from cf_ui.themes import tailwind_content_globs

    for pattern in tailwind_content_globs():
        assert Path(pattern).is_absolute(), pattern


def test_content_globs_use_forward_slashes_on_every_platform():
    """These strings get pasted into JS, where a backslash is an escape.

    fast-glob (Tailwind's matcher) reads ``\\`` as an escape rather than a
    separator, so a native Windows path matches nothing — and matching nothing
    is indistinguishable from the tree-shaking this whole module prevents.
    """
    from cf_ui.themes import tailwind_content_globs

    for pattern in tailwind_content_globs():
        assert "\\" not in pattern, pattern


def test_content_globs_cover_every_daisy_template():
    """The test that fails when the templates would be tree-shaken away."""
    from cf_ui.themes import tailwind_content_globs

    covered = set()
    for pattern in tailwind_content_globs():
        covered.update(Path(p).resolve() for p in globlib.glob(pattern, recursive=True))

    assert DAISY_TEMPLATES, "no daisy templates found — the suite would pass vacuously"
    missing = [t for t in DAISY_TEMPLATES if t.resolve() not in covered]
    assert not missing, f"not reachable by the documented content glob: {missing}"


def test_content_globs_cover_the_public_cotton_wrappers():
    """The wrappers hold no classes today, but the glob must not exclude them."""
    from cf_ui.themes import tailwind_content_globs

    covered = set()
    for pattern in tailwind_content_globs():
        covered.update(Path(p).resolve() for p in globlib.glob(pattern, recursive=True))

    wrapper = (TEMPLATES_DIR / "cotton" / "cf" / "card.html").resolve()
    assert wrapper in covered


def test_content_globs_are_rooted_in_the_installed_package():
    """Derived from ``cf_ui.__file__``, so a site-packages install works too."""
    from cf_ui.themes import tailwind_content_globs

    for pattern in tailwind_content_globs():
        assert str(PKG_DIR.resolve()) in str(Path(pattern).resolve())


def test_documentation_publishes_the_same_glob():
    """Drift guard: docs that disagree with the code cause silent unstyled pages."""
    from cf_ui.themes import TAILWIND_CONTENT_SUFFIX

    doc = (Path(__file__).parent.parent.parent / "docs" / "daisyui.md").read_text(encoding="utf-8")
    assert TAILWIND_CONTENT_SUFFIX in doc


# --- Failure mode 2: class names assembled at render time ------------------

# A class token split across a template construct is invisible to the scanner.
#   alert-{{ type }}          -> flagged (variable glued to a prefix)
#   alert-{% if x %}error{%   -> flagged (tag glued to a prefix)
#   input-bordered{% if e %}  -> fine (complete token, then a tag)
#   {{ extra_class }}         -> fine (a whole class handed in by the consumer)
_SPLIT_TOKEN = re.compile(r"[\w-]\{\{|\}\}[\w-]|-\{%|%\}-")
_CLASS_ATTR = re.compile(r"""\bclass="([^"]*)\"""")


def test_the_daisy_template_set_is_complete():
    """Without this, the parametrized scan below silently degrades to a skip."""
    from cf_ui.themes import COMPONENTS

    assert COMPONENTS, "the component registry is empty"
    assert len(DAISY_TEMPLATES) == 2 * len(COMPONENTS), (
        f"expected {len(COMPONENTS)} jinja + {len(COMPONENTS)} cotton, got {DAISY_TEMPLATES}"
    )


@pytest.mark.parametrize("template", DAISY_TEMPLATES, ids=lambda p: p.name)
def test_no_daisy_class_name_is_assembled_at_render_time(template):
    source = template.read_text(encoding="utf-8")
    offenders = [value for value in _CLASS_ATTR.findall(source) if _SPLIT_TOKEN.search(value)]
    assert not offenders, (
        f"{template.name}: class token split across a template construct — "
        f"Tailwind will tree-shake it: {offenders}"
    )


def test_the_split_token_detector_actually_detects_a_split():
    """Meta-test: a guard that cannot fail is not a guard."""
    assert _SPLIT_TOKEN.search("alert alert-{{ type }}")
    assert _SPLIT_TOKEN.search("alert alert-{% if e %}error{% endif %}")
    assert not _SPLIT_TOKEN.search("input input-bordered {{ extra_class }}")
    assert not _SPLIT_TOKEN.search("input input-bordered{% if error %} input-error{% endif %}")


# --- The type -> daisy class maps emit whole tokens ------------------------


@pytest.mark.parametrize(
    "prefix,expected",
    [
        ("alert", {"alert-info", "alert-success", "alert-warning", "alert-error"}),
        (
            "progress",
            {
                "progress-primary",
                "progress-info",
                "progress-success",
                "progress-warning",
                "progress-error",
            },
        ),
    ],
)
def test_variant_class_names_appear_literally_in_the_sources(prefix, expected):
    """Whatever a component maps `type=` onto must be greppable as a whole word."""
    blob = "\n".join(t.read_text(encoding="utf-8") for t in DAISY_TEMPLATES)
    missing = {name for name in expected if name not in blob}
    assert not missing, f"{prefix} variants never appear literally: {missing}"
