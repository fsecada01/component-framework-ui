from fastapi.testclient import TestClient

from tests.integration.jinja_app.main import app

client = TestClient(app)


def test_form_field_endpoint_renders_input():
    r = client.get("/form-field")
    assert r.status_code == 200
    assert 'name="email"' in r.text
    assert "Email" in r.text


def test_modal_endpoint_renders_modal():
    r = client.get("/modal")
    assert r.status_code == 200
    assert "modal" in r.text
    assert "cfModal" in r.text
    assert 'id="test-modal"' in r.text


def test_card_endpoint_renders_card():
    r = client.get("/card")
    assert r.status_code == 200
    assert "Card body" in r.text
    assert "Card Title" in r.text
    assert "card-header" in r.text


def test_navbar_endpoint_renders_nav():
    r = client.get("/navbar")
    assert r.status_code == 200
    assert "<nav" in r.text
    assert "cfNavbar" in r.text
    assert "navbar-burger" in r.text


def test_tabs_endpoint_renders_tabs():
    r = client.get("/tabs")
    assert r.status_code == 200
    assert "cfTabs" in r.text
    assert "hx-get" in r.text
