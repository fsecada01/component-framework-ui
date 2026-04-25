def test_cf_ui_head_returns_bulma_cdn_link(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_head
    result = cf_ui_head()
    assert "bulma" in result
    assert '<link rel="stylesheet"' in result
    assert "cdn.jsdelivr.net" in result


def test_cf_ui_head_includes_xcloak_style(settings):
    settings.CF_UI_THEME = "bulma"
    from cf_ui.templatetags.cf_ui import cf_ui_head
    result = cf_ui_head()
    assert "[x-cloak]" in result
    assert "display: none" in result


def test_cf_ui_head_respects_version_override(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {"bulma": "0.9.4"}
    from cf_ui.templatetags.cf_ui import cf_ui_head
    result = cf_ui_head()
    assert "0.9.4" in result


def test_cf_ui_body_includes_alpine_scripts(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body
    result = cf_ui_body()
    assert "alpinejs" in result
    assert "cf_ui_alpine.js" in result
    assert "defer" in result


def test_cf_ui_body_alpine_false_omits_scripts(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body
    result = cf_ui_body(alpine=False)
    assert result == ""


def test_cf_ui_body_cf_alpine_loads_before_alpine(settings):
    settings.CF_UI_THEME = "bulma"
    settings.CF_UI_CDN_VERSIONS = {}
    from cf_ui.templatetags.cf_ui import cf_ui_body
    result = cf_ui_body()
    cf_pos = result.find("cf_ui_alpine.js")
    alpine_pos = result.find("alpinejs")
    assert cf_pos < alpine_pos, "cf_ui_alpine.js must appear before Alpine CDN"
