import pytest


@pytest.fixture
def cotton_render():
    """Render a django-cotton component by template path and return HTML string.

    Usage: cotton_render("cf/form-field.html", name="x", label="X")
    """
    from django.template.loader import render_to_string

    def _render(template_name: str, **props: object) -> str:
        return render_to_string(f"cotton/bulma/{template_name}", props)

    return _render
