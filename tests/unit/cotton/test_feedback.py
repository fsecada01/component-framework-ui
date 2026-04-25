
def test_modal_cotton_has_modal_class(cotton_render):
    html = cotton_render("cf/modal.html", id="my-modal", **{"class": ""})
    assert "modal" in html
    assert "my-modal" in html


def test_modal_cotton_has_alpine_binding(cotton_render):
    html = cotton_render("cf/modal.html", id="modal", **{"class": ""})
    assert "cfModal" in html
    assert "initModal" in html


def test_notification_cotton_renders_message(cotton_render):
    html = cotton_render("cf/notification.html",
                         message="Done!", type="success", dismissible="true", **{"class": ""})
    assert "Done!" in html
    assert "is-success" in html


def test_notification_cotton_dismissible(cotton_render):
    html = cotton_render("cf/notification.html",
                         message="Hi", type="info", dismissible="true", **{"class": ""})
    assert 'class="delete"' in html


def test_notification_cotton_non_dismissible(cotton_render):
    html = cotton_render("cf/notification.html",
                         message="Hi", type="info", dismissible="false", **{"class": ""})
    assert 'class="delete"' not in html


def test_progress_cotton_renders(cotton_render):
    html = cotton_render("cf/progress.html",
                         value="60", max="100", type="info", label="", **{"class": ""})
    assert "progress" in html
    assert "60" in html
