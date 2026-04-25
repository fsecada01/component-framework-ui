from pathlib import Path

ALPINE_JS = (
    Path(__file__).parent.parent.parent / "src" / "cf_ui" / "static" / "cf_ui" / "cf_ui_alpine.js"
)


def test_alpine_js_exists():
    assert ALPINE_JS.exists(), "cf_ui_alpine.js not found"


def test_alpine_js_registers_cf_modal():
    content = ALPINE_JS.read_text()
    assert "Alpine.data('cfModal'" in content


def test_alpine_js_registers_cf_navbar():
    content = ALPINE_JS.read_text()
    assert "Alpine.data('cfNavbar'" in content


def test_alpine_js_registers_cf_panel():
    content = ALPINE_JS.read_text()
    assert "Alpine.data('cfPanel'" in content


def test_alpine_js_registers_cf_tabs():
    content = ALPINE_JS.read_text()
    assert "Alpine.data('cfTabs'" in content


def test_alpine_js_registers_cf_store():
    content = ALPINE_JS.read_text()
    assert "Alpine.store('cf'" in content


def test_alpine_js_store_has_notify():
    content = ALPINE_JS.read_text()
    assert "notify(" in content


def test_alpine_js_store_has_modal_open_close():
    content = ALPINE_JS.read_text()
    assert "modal" in content
    assert "open(" in content
    assert "close(" in content


def test_alpine_js_uses_alpine_init_event():
    content = ALPINE_JS.read_text()
    assert "alpine:init" in content
