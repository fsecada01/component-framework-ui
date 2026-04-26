def test_form_field_renders_label(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email Address",
        value="",
        error="",
        type="text",
        required=False,
        extra_class="",
        input_class="",
    )
    assert "Email Address" in html
    assert '<label class="label"' in html


def test_form_field_renders_input(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="test@example.com",
        error="",
        type="email",
        required=False,
        extra_class="",
        input_class="",
    )
    assert 'name="email"' in html
    assert 'type="email"' in html
    assert 'value="test@example.com"' in html


def test_form_field_shows_error(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="",
        error="This field is required.",
        type="text",
        required=False,
        extra_class="",
        input_class="",
    )
    assert "This field is required." in html
    assert "is-danger" in html
    assert 'class="help is-danger"' in html


def test_form_field_no_error_omits_danger(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="",
        error="",
        type="text",
        required=False,
        extra_class="",
        input_class="",
    )
    assert "is-danger" not in html


def test_form_field_required_attribute(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="",
        error="",
        type="text",
        required=True,
        extra_class="",
        input_class="",
    )
    assert "required" in html


def test_select_renders_options(render):
    options = [{"value": "a", "label": "Option A"}, {"value": "b", "label": "Option B"}]
    html = render(
        "Select.jinja",
        name="choice",
        label="Choose",
        value="a",
        error="",
        options=options,
        extra_class="",
        input_class="",
    )
    assert "Option A" in html
    assert "Option B" in html
    assert 'value="a"' in html
    assert "selected" in html


def test_select_shows_error(render):
    html = render(
        "Select.jinja",
        name="choice",
        label="Choose",
        value="",
        error="Required",
        options=[],
        extra_class="",
        input_class="",
    )
    assert "Required" in html
    assert "is-danger" in html


def test_textarea_renders_value(render):
    html = render(
        "Textarea.jinja",
        name="bio",
        label="Bio",
        value="Hello world",
        error="",
        rows=4,
        extra_class="",
        input_class="",
    )
    assert "Hello world" in html
    assert 'name="bio"' in html
    assert 'rows="4"' in html


def test_textarea_shows_error(render):
    html = render(
        "Textarea.jinja",
        name="bio",
        label="Bio",
        value="",
        error="Too short",
        rows=4,
        extra_class="",
        input_class="",
    )
    assert "Too short" in html
    assert "is-danger" in html


def test_checkbox_group_renders_choices(render):
    choices = [{"value": "a", "label": "Apple"}, {"value": "b", "label": "Banana"}]
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="Fruits",
        choices=choices,
        selected=["a"],
        error="",
        extra_class="",
        control_class="",
    )
    assert "Apple" in html
    assert "Banana" in html
    assert 'value="a"' in html
    assert "checked" in html


def test_checkbox_group_unchecked_item(render):
    choices = [{"value": "a", "label": "Apple"}, {"value": "b", "label": "Banana"}]
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="Fruits",
        choices=choices,
        selected=["a"],
        error="",
        extra_class="",
        control_class="",
    )
    assert html.count("checked") == 1


def test_checkbox_group_shows_error(render):
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="Fruits",
        choices=[],
        selected=[],
        error="Select at least one",
        extra_class="",
        control_class="",
    )
    assert "Select at least one" in html
    assert "is-danger" in html


# ── Granular class prop tests ────────────────────────────────────────────────


def test_form_field_input_class_applied(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="",
        error="",
        type="text",
        required=False,
        extra_class="",
        input_class="is-rounded",
    )
    assert "is-rounded" in html
    assert 'class="input is-rounded"' in html


def test_form_field_input_class_default_omitted(render):
    html = render(
        "FormField.jinja",
        name="email",
        label="Email",
        value="",
        error="",
        type="text",
        required=False,
        extra_class="",
        input_class="",
    )
    assert 'class="input"' in html


def test_select_input_class_applied(render):
    html = render(
        "Select.jinja",
        name="choice",
        label="Choose",
        value="",
        error="",
        options=[],
        extra_class="",
        input_class="my-select",
    )
    assert 'class="my-select"' in html


def test_select_input_class_default_omitted(render):
    html = render(
        "Select.jinja",
        name="choice",
        label="Choose",
        value="",
        error="",
        options=[],
        extra_class="",
        input_class="",
    )
    # No class attribute on the bare <select> when input_class is empty
    assert "<select " not in html or 'class=""' not in html


def test_textarea_input_class_applied(render):
    html = render(
        "Textarea.jinja",
        name="bio",
        label="Bio",
        value="",
        error="",
        rows=4,
        extra_class="",
        input_class="has-fixed-size",
    )
    assert "has-fixed-size" in html
    assert 'class="textarea has-fixed-size"' in html


def test_textarea_input_class_default_omitted(render):
    html = render(
        "Textarea.jinja",
        name="bio",
        label="Bio",
        value="",
        error="",
        rows=4,
        extra_class="",
        input_class="",
    )
    assert 'class="textarea"' in html


def test_checkbox_group_control_class_applied(render):
    choices = [{"value": "a", "label": "Apple"}]
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="Fruits",
        choices=choices,
        selected=[],
        error="",
        extra_class="",
        control_class="is-flex",
    )
    assert "is-flex" in html
    assert 'class="control is-flex"' in html


def test_checkbox_group_control_class_default_omitted(render):
    choices = [{"value": "a", "label": "Apple"}]
    html = render(
        "CheckboxGroup.jinja",
        name="fruits",
        label="Fruits",
        choices=choices,
        selected=[],
        error="",
        extra_class="",
        control_class="",
    )
    assert 'class="control"' in html
