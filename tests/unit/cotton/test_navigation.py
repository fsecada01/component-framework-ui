

def test_navbar_cotton_renders(cotton_render):
    html = cotton_render("cf/navbar.html", **{"class": ""})
    assert "navbar" in html
    assert "cfNavbar" in html


def test_navbar_cotton_has_burger(cotton_render):
    html = cotton_render("cf/navbar.html", **{"class": ""})
    assert "navbar-burger" in html
    assert "@click" in html


def test_breadcrumb_cotton_renders_items(cotton_render):
    items = [{"label": "Home", "url": "/"}, {"label": "Page", "url": "/page/"}]
    html = cotton_render("cf/breadcrumb.html", items=items, **{"class": ""})
    assert "Home" in html
    assert "Page" in html


def test_tabs_cotton_renders(cotton_render):
    tabs = [{"id": "one", "url": "/tab/one/"}]
    html = cotton_render("cf/tabs.html",
                         tabs=tabs, hx_target="tab-content", **{"class": ""})
    assert "cfTabs" in html
    assert "hx-get" in html
