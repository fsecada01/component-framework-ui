import pytest


def test_form_field_renders_label(render):
    html = render("FormField.jinja", name="email", label="Email Address",
                  value="", error=None, type="text", required=False, **{"class": ""})
    assert "Email Address" in html
    assert '<label class="label"' in html


def test_form_field_renders_input(render):
    html = render("FormField.jinja", name="email", label="Email",
                  value="test@example.com", error=None, type="email",
                  required=False, **{"class": ""})
    assert 'name="email"' in html
    assert 'type="email"' in html
    assert 'value="test@example.com"' in html


def test_form_field_shows_error(render):
    html = render("FormField.jinja", name="email", label="Email",
                  value="", error="This field is required.", type="text",
                  required=False, **{"class": ""})
    assert "This field is required." in html
    assert "is-danger" in html
    assert 'class="help is-danger"' in html


def test_form_field_no_error_omits_danger(render):
    html = render("FormField.jinja", name="email", label="Email",
                  value="", error=None, type="text", required=False, **{"class": ""})
    assert "is-danger" not in html


def test_form_field_required_attribute(render):
    html = render("FormField.jinja", name="email", label="Email",
                  value="", error=None, type="text", required=True, **{"class": ""})
    assert "required" in html


def test_select_renders_options(render):
    options = [{"value": "a", "label": "Option A"}, {"value": "b", "label": "Option B"}]
    html = render("Select.jinja", name="choice", label="Choose",
                  value="a", error=None, options=options, **{"class": ""})
    assert "Option A" in html
    assert "Option B" in html
    assert 'value="a"' in html
    assert "selected" in html


def test_select_shows_error(render):
    html = render("Select.jinja", name="choice", label="Choose",
                  value="", error="Required", options=[], **{"class": ""})
    assert "Required" in html
    assert "is-danger" in html


def test_textarea_renders_value(render):
    html = render("Textarea.jinja", name="bio", label="Bio",
                  value="Hello world", error=None, rows=4, **{"class": ""})
    assert "Hello world" in html
    assert 'name="bio"' in html
    assert 'rows="4"' in html


def test_textarea_shows_error(render):
    html = render("Textarea.jinja", name="bio", label="Bio",
                  value="", error="Too short", rows=4, **{"class": ""})
    assert "Too short" in html
    assert "is-danger" in html


def test_checkbox_group_renders_choices(render):
    choices = [{"value": "a", "label": "Apple"}, {"value": "b", "label": "Banana"}]
    html = render("CheckboxGroup.jinja", name="fruits", label="Fruits",
                  choices=choices, selected=["a"], error=None, **{"class": ""})
    assert "Apple" in html
    assert "Banana" in html
    assert 'value="a"' in html
    assert "checked" in html


def test_checkbox_group_unchecked_item(render):
    choices = [{"value": "a", "label": "Apple"}, {"value": "b", "label": "Banana"}]
    html = render("CheckboxGroup.jinja", name="fruits", label="Fruits",
                  choices=choices, selected=["a"], error=None, **{"class": ""})
    assert html.count("checked") == 1


def test_checkbox_group_shows_error(render):
    html = render("CheckboxGroup.jinja", name="fruits", label="Fruits",
                  choices=[], selected=[], error="Select at least one", **{"class": ""})
    assert "Select at least one" in html
    assert "is-danger" in html
