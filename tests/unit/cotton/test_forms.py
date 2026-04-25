import pytest


def test_form_field_cotton_renders_label(cotton_render):
    html = cotton_render("cf/form-field.html",
                         name="email", label="Email Address",
                         value="", error="", type="text", required="false")
    assert "Email Address" in html
    assert "label" in html.lower()


def test_form_field_cotton_renders_input(cotton_render):
    html = cotton_render("cf/form-field.html",
                         name="email", label="Email",
                         value="test@example.com", error="", type="email", required="false")
    assert 'name="email"' in html
    assert "test@example.com" in html


def test_form_field_cotton_shows_error(cotton_render):
    html = cotton_render("cf/form-field.html",
                         name="email", label="Email",
                         value="", error="Required", type="text", required="false")
    assert "Required" in html
    assert "is-danger" in html


def test_select_cotton_renders_options(cotton_render):
    html = cotton_render("cf/select.html",
                         name="choice", label="Choose",
                         value="a", error="",
                         options=[{"value": "a", "label": "Option A"},
                                  {"value": "b", "label": "Option B"}])
    assert "Option A" in html
    assert "Option B" in html


def test_textarea_cotton_renders(cotton_render):
    html = cotton_render("cf/textarea.html",
                         name="bio", label="Bio",
                         value="Hello", error="", rows="4")
    assert "Hello" in html
    assert "textarea" in html.lower()


def test_checkbox_group_cotton_renders_choices(cotton_render):
    html = cotton_render("cf/checkbox-group.html",
                         name="fruits", label="Fruits",
                         choices=[{"value": "a", "label": "Apple"}],
                         selected=["a"], error="")
    assert "Apple" in html
    assert "checked" in html
