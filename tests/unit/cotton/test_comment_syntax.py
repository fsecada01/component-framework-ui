"""A multi-line ``{# #}`` renders into the page, so no cotton template has one.

Django's comment regex is ``\\{#.*?#\\}`` **without** ``DOTALL``: ``{# #}`` is a
single-line construct. Open one on one line and close it on another and the
lexer never forms a comment token — every line in between is emitted as
literal text, straight into the consumer's rendered HTML. There is no error,
no warning, and no test failure unless something looks for it, which is what
this file does.

Six shipped bootstrap and daisy partials carried the defect before #52 and
leaked their rationale comments — several paragraphs of prose about z-index
stacking and Tailwind layer ordering — into every page that rendered them.
``{% comment %}…{% endcomment %}`` is the multi-line form and is what every
cotton template uses now.

This is a *cotton-only* rule. The Jinja templates in ``templates/jinja/`` run
under Jinja2, whose ``{# #}`` spans lines perfectly well.
"""

import re
from pathlib import Path

import pytest

COTTON_DIR = Path(__file__).parent.parent.parent.parent / "src" / "cf_ui" / "templates" / "cotton"

#: Django's own comment pattern, minus ``DOTALL`` — deliberately mirroring the
#: engine rather than approximating it. A match that spans a newline is
#: therefore impossible; what this finds is a ``{#`` whose ``#}`` never arrives
#: on the same line, which is precisely the broken shape.
SINGLE_LINE_COMMENT = re.compile(r"\{#.*?#\}")

COTTON_TEMPLATES = sorted(COTTON_DIR.rglob("*.html"))


def _unclosed_comment_lines(source: str) -> list[tuple[int, str]]:
    """Lines opening a ``{#`` that no ``#}`` closes before the newline."""
    offenders = []
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = SINGLE_LINE_COMMENT.sub("", line)
        if "{#" in stripped:
            offenders.append((number, line.strip()))
    return offenders


def test_the_template_tree_is_not_empty():
    """Stops the parametrised guard below from passing on an empty collection."""
    assert len(COTTON_TEMPLATES) > 50


@pytest.mark.parametrize("template", COTTON_TEMPLATES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_no_cotton_template_opens_a_multi_line_comment(template: Path):
    offenders = _unclosed_comment_lines(template.read_text(encoding="utf-8"))
    assert not offenders, (
        f"{template.name} opens a `{{#` that does not close on the same line — "
        f"Django will render the following lines as literal page text. Use "
        f"`{{% comment %}}`…`{{% endcomment %}}`. Lines: {offenders}"
    )


# ── The guard's own behaviour, pinned ─────────────────────────────────────


@pytest.mark.parametrize(
    ("source", "expected_count"),
    [
        ("{# fine #}\n<div></div>", 0),
        ("<div>{# also fine #}</div>", 0),
        ("{# broken\n   across lines #}", 1),
        ("  {# indented\n     and broken #}", 1),
        ("{# ok #} {# broken\n#}", 1),
        ("{% comment %}\nmany\nlines\n{% endcomment %}", 0),
        ("<div>no comments at all</div>", 0),
    ],
    ids=lambda v: str(v)[:32],
)
def test_the_reader_flags_what_it_claims_to(source: str, expected_count: int):
    assert len(_unclosed_comment_lines(source)) == expected_count
