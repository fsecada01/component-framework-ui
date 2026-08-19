import pytest


@pytest.fixture
def client():
    from django.test import Client

    return Client()


def test_form_field_cotton_renders(client):
    r = client.get("/form-field/")
    assert r.status_code == 200
    assert b'name="email"' in r.content
    assert b"Email" in r.content
    # The gallery template's raw `<c-cf.form-field ...>` tag must be
    # compiled away, not passed through as literal text — see #79.
    assert b"<c-cf.form-field" not in r.content


def test_modal_cotton_renders(client):
    r = client.get("/modal/")
    assert r.status_code == 200
    assert b"modal" in r.content
    assert b"test-modal" in r.content
    assert b"<c-cf.modal" not in r.content


def test_card_cotton_renders(client):
    r = client.get("/card/")
    assert r.status_code == 200
    assert b"Card Title" in r.content
    assert b"Card body content" in r.content
    assert b"Card Footer" in r.content
    assert b"<c-cf.card" not in r.content
