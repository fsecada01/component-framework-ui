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


def test_modal_cotton_renders(client):
    r = client.get("/modal/")
    assert r.status_code == 200
    assert b"modal" in r.content
    assert b"test-modal" in r.content


def test_card_cotton_renders(client):
    r = client.get("/card/")
    assert r.status_code == 200
    assert b"Card Title" in r.content
    assert b"Card body content" in r.content
    assert b"Card Footer" in r.content
