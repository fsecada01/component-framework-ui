import pytest


def test_card_renders_default_slot(render):
    html = render("Card.jinja", content="Body text", header="", footer="", extra_class="")
    assert "Body text" in html
    assert "card" in html


def test_card_renders_header_when_provided(render):
    html = render("Card.jinja", content="Body", header="My Title", footer="", extra_class="")
    assert "My Title" in html
    assert "card-header" in html


def test_card_omits_header_when_empty(render):
    html = render("Card.jinja", content="Body", header="", footer="", extra_class="")
    assert "card-header" not in html


def test_card_renders_footer_when_provided(render):
    html = render("Card.jinja", content="Body", header="", footer="Footer text", extra_class="")
    assert "Footer text" in html
    assert "card-footer" in html


def test_table_renders_headers(render):
    columns = [{"key": "name", "label": "Name"}, {"key": "age", "label": "Age"}]
    html = render("Table.jinja", columns=columns, rows=[], hx_target="", hx_url="", extra_class="")
    assert "Name" in html
    assert "Age" in html
    assert "<th>" in html


def test_table_renders_rows(render):
    columns = [{"key": "name", "label": "Name"}]
    rows = [{"name": "Alice"}, {"name": "Bob"}]
    html = render("Table.jinja", columns=columns, rows=rows, hx_target="", hx_url="", extra_class="")
    assert "Alice" in html
    assert "Bob" in html


def test_pagination_renders_page_links(render):
    html = render("Pagination.jinja", page=2, total_pages=5,
                  hx_target="#results", hx_url="/items/", extra_class="")
    assert "pagination" in html
    assert "Previous" in html
    assert "Next" in html


def test_pagination_disables_previous_on_first_page(render):
    html = render("Pagination.jinja", page=1, total_pages=5,
                  hx_target="#results", hx_url="/items/", extra_class="")
    assert "disabled" in html


def test_pagination_disables_next_on_last_page(render):
    html = render("Pagination.jinja", page=5, total_pages=5,
                  hx_target="#results", hx_url="/items/", extra_class="")
    lines = [l for l in html.split("\n") if "Next" in l]
    assert any("disabled" in l for l in lines)


def test_pagination_marks_current_page(render):
    html = render("Pagination.jinja", page=3, total_pages=5,
                  hx_target="#results", hx_url="/items/", extra_class="")
    assert "is-current" in html


def test_pagination_includes_hx_get(render):
    html = render("Pagination.jinja", page=2, total_pages=5,
                  hx_target="#results", hx_url="/items/", extra_class="")
    assert "hx-get" in html
    assert "/items/" in html


def test_panel_renders_title(render):
    html = render("Panel.jinja", title="Settings", content="Panel body",
                  open=False, extra_class="")
    assert "Settings" in html


def test_panel_has_alpine_x_data(render):
    html = render("Panel.jinja", title="Settings", content="Body",
                  open=False, extra_class="")
    assert "x-data" in html
    assert "cfPanel" in html


def test_panel_content_has_x_show(render):
    html = render("Panel.jinja", title="Settings", content="Body",
                  open=False, extra_class="")
    assert "x-show" in html
    assert "x-cloak" in html
