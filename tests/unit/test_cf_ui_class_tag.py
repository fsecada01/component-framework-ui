"""``{% cf_ui_class %}`` — whitespace-collapse for cotton class chains.

Django has no Jinja-style ``{%- -%}`` trim markers (see
``tests/unit/test_theme_dispatch.py`` for the cotton dispatch story and
CLAUDE.md's django-cotton gotchas), so a chained ``{% if %}...{% elif
%}...{% endif %}`` class attribute has to stay on one physical line or a
literal newline becomes literal whitespace in the rendered ``class``
attribute. This tag lets that chain be written one branch per line by
rendering its nodelist normally and collapsing the result's whitespace runs
to a single space, stripped at both ends.
"""

import pytest
from django.template import Context, Template, TemplateSyntaxError

HOSTILE = '" onmouseover="window.cfPwned=true" x="'


def _render(source: str, **ctx) -> str:
    return Template("{% load cf_ui %}" + source).render(Context(ctx))


def test_collapses_internal_whitespace_to_single_spaces():
    out = _render(
        "{% cf_ui_class %}\n  button\n  {% if hot %}\n    is-primary\n  {% endif %}\n"
        "{% endcf_ui_class %}",
        hot=True,
    )
    assert out == "button is-primary"


def test_strips_leading_and_trailing_whitespace():
    out = _render("{% cf_ui_class %}\n  button\n{% endcf_ui_class %}")
    assert out == "button"


def test_a_branch_that_does_not_render_leaves_no_double_space():
    out = _render(
        "{% cf_ui_class %}\n  button\n  {% if hot %}is-primary{% endif %}\n  is-small\n"
        "{% endcf_ui_class %}",
        hot=False,
    )
    assert out == "button is-small"
    assert "  " not in out


def test_renders_inline_by_default():
    out = _render('<button class="{% cf_ui_class %}button{% endcf_ui_class %}">')
    assert out == '<button class="button">'


def test_as_form_stores_the_result_and_renders_nothing_inline():
    out = _render(
        "[{% cf_ui_class as cf_class %}\n  button\n  extra\n{% endcf_ui_class %}]"
        '<button class="{{ cf_class }}">'
    )
    assert out == '[]<button class="button extra">'


def test_hostile_class_prop_is_escaped_like_any_other_django_output():
    """The tag only reflows whitespace — it does not turn off autoescape.

    Each ``{{ }}`` inside the captured nodelist is escaped exactly as Django
    would escape it in place; ``mark_safe`` on the joined result must not
    reopen that hole.
    """
    out = _render(
        "{% cf_ui_class %}\n  button\n  {% if extra %}{{ extra }}{% endif %}\n{% endcf_ui_class %}",
        extra=HOSTILE,
    )
    assert 'onmouseover="window.cfPwned=true"' not in out
    assert "&#34;" in out or "&quot;" in out


def test_rejects_a_second_bit_that_is_not_as():
    with pytest.raises(TemplateSyntaxError, match="takes either no arguments"):
        Template("{% load cf_ui %}{% cf_ui_class oops %}x{% endcf_ui_class %}")


def test_rejects_more_than_two_bits_after_as():
    with pytest.raises(TemplateSyntaxError, match="takes either no arguments"):
        Template("{% load cf_ui %}{% cf_ui_class as x y %}z{% endcf_ui_class %}")


# --- Applied to the real button partials -----------------------------------


@pytest.mark.parametrize("theme", ["bulma", "bootstrap", "foundation", "fomantic", "daisy"])
def test_button_partial_class_attribute_has_no_stray_whitespace(settings, theme):
    """The property the reformat was actually done for.

    A regression here would mean either the tag stopped collapsing (multiple
    spaces or a stray newline leaking into the attribute) or a template
    stopped using it (falling back to Django's raw multi-line join).
    """
    import re

    from django.template.loader import render_to_string

    settings.CF_UI_THEME = theme
    html = render_to_string(
        "cotton/cf/button.html",
        {
            "variant": "primary",
            "size": "small",
            "full_width": True,
            "class": "extra-token",
            # render_to_string bypasses <c-vars> defaults (see CLAUDE.md's
            # django-cotton gotchas), so the type axis needs a value here.
            "type": "submit",
        },
    )
    match = re.search(r'class="([^"]*)"', html)
    assert match, f"{theme}: no class attribute found in {html!r}"
    class_value = match.group(1)
    assert "  " not in class_value
    assert class_value == class_value.strip()
    assert "\n" not in class_value
