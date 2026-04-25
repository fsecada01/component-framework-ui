

def test_navbar_renders_nav_element(render):
    html = render("Navbar.jinja", brand="", start="", end="", extra_class="")
    assert "<nav" in html
    assert "navbar" in html


def test_navbar_has_alpine_cfnavbar(render):
    html = render("Navbar.jinja", brand="", start="", end="", extra_class="")
    assert "cfNavbar" in html
    assert "x-data" in html


def test_navbar_burger_has_alpine_click(render):
    html = render("Navbar.jinja", brand="", start="", end="", extra_class="")
    assert "navbar-burger" in html
    assert "@click" in html
    assert "menuOpen" in html


def test_navbar_menu_has_class_binding(render):
    html = render("Navbar.jinja", brand="", start="", end="", extra_class="")
    assert ":class" in html
    assert "is-active" in html


def test_breadcrumb_renders_items(render):
    items = [{"label": "Home", "url": "/"}, {"label": "Products", "url": "/products/"}]
    html = render("Breadcrumb.jinja", items=items, extra_class="")
    assert "Home" in html
    assert "Products" in html
    assert 'href="/"' in html


def test_breadcrumb_last_item_is_active(render):
    items = [{"label": "Home", "url": "/"}, {"label": "Current", "url": "/cur/"}]
    html = render("Breadcrumb.jinja", items=items, extra_class="")
    assert "is-active" in html
    assert "aria-current" in html


def test_tabs_renders_tab_labels(render):
    tabs = [{"id": "one", "url": "/tab/one/"}, {"id": "two", "url": "/tab/two/"}]
    html = render("Tabs.jinja", tabs=tabs, hx_target="tab-content",
                  content="", extra_class="")
    assert "one" in html
    assert "two" in html


def test_tabs_has_alpine_cftabs(render):
    tabs = [{"id": "one", "url": "/tab/one/"}]
    html = render("Tabs.jinja", tabs=tabs, hx_target="tab-content",
                  content="", extra_class="")
    assert "cfTabs" in html
    assert "x-data" in html


def test_tabs_links_have_hx_get(render):
    tabs = [{"id": "one", "url": "/tab/one/"}]
    html = render("Tabs.jinja", tabs=tabs, hx_target="tab-content",
                  content="", extra_class="")
    assert "hx-get" in html
    assert "/tab/one/" in html


def test_tabs_renders_content_container(render):
    tabs = [{"id": "one", "url": "/tab/one/"}]
    html = render("Tabs.jinja", tabs=tabs, hx_target="tab-content",
                  content="", extra_class="")
    assert 'id="tab-content"' in html
