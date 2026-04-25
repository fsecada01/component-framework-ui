def test_card_cotton_renders_body(cotton_render):
    html = cotton_render("cf/card.html", **{"class": ""})
    assert "card" in html


def test_table_cotton_renders_headers(cotton_render):
    columns = [{"key": "name", "label": "Name"}]
    html = cotton_render("cf/table.html",
                         columns=columns, rows=[], hx_target="", hx_url="", **{"class": ""})
    assert "Name" in html
    assert "<th>" in html


def test_table_cotton_renders_rows(cotton_render):
    columns = [{"key": "name", "label": "Name"}]
    rows = [{"name": "Alice"}]
    html = cotton_render("cf/table.html",
                         columns=columns, rows=rows, hx_target="", hx_url="", **{"class": ""})
    assert "Alice" in html


def test_pagination_cotton_renders(cotton_render):
    html = cotton_render("cf/pagination.html",
                         page="2", total_pages="5",
                         hx_target="#results", hx_url="/items/", **{"class": ""})
    assert "pagination" in html
    assert "Previous" in html
    assert "Next" in html


def test_panel_cotton_has_alpine(cotton_render):
    html = cotton_render("cf/panel.html", title="Settings", **{"class": ""})
    assert "cfPanel" in html
    assert "x-data" in html
