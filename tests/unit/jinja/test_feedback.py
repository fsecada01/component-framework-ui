def test_modal_renders_with_id(render):
    html = render("Modal.jinja", id="my-modal", extra_class="")
    assert 'id="my-modal"' in html
    assert "modal" in html
    assert "modal-card" in html


def test_modal_has_alpine_x_data(render):
    html = render("Modal.jinja", id="modal", extra_class="")
    assert "x-data" in html
    assert "cfModal" in html


def test_modal_close_button_has_alpine_click(render):
    html = render("Modal.jinja", id="modal", extra_class="")
    assert "@click" in html
    assert "close()" in html


def test_modal_is_active_binding(render):
    html = render("Modal.jinja", id="modal", extra_class="")
    assert "is-active" in html
    assert ":class" in html


def test_modal_has_init_modal(render):
    html = render("Modal.jinja", id="modal", extra_class="")
    assert "initModal" in html


def test_notification_renders_message(render):
    html = render(
        "Notification.jinja", message="Saved!", type="success", dismissible=True, extra_class=""
    )
    assert "Saved!" in html
    assert "is-success" in html


def test_notification_dismissible_has_delete_button(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=True, extra_class="")
    assert 'class="delete"' in html
    assert "@click" in html


def test_notification_non_dismissible_omits_delete(render):
    html = render(
        "Notification.jinja", message="Hi", type="info", dismissible=False, extra_class=""
    )
    assert 'class="delete"' not in html


def test_notification_has_alpine_x_show(render):
    html = render("Notification.jinja", message="Hi", type="info", dismissible=True, extra_class="")
    assert "x-show" in html


def test_progress_renders_value_and_max(render):
    html = render("Progress.jinja", value=40, max=100, type="primary", label="", extra_class="")
    assert 'value="40"' in html
    assert 'max="100"' in html
    assert "progress" in html


def test_progress_renders_label(render):
    html = render(
        "Progress.jinja", value=40, max=100, type="primary", label="Loading...", extra_class=""
    )
    assert "Loading..." in html


def test_progress_type_class(render):
    html = render("Progress.jinja", value=75, max=100, type="danger", label="", extra_class="")
    assert "is-danger" in html
