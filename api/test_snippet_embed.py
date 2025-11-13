from api.utils import parse_snippet_embed


def test_parse_power_bi_with_report_id():
    html = (
        '<div class="embed-power-bi" '
        'data-snippet-type="power_bi" '
        'data-report-id="00000000-0000-0000-0000-000000000000" '
        'data-auth-required="true"></div>'
    )
    res = parse_snippet_embed(html)
    assert res is not None
    assert res.get("type") == "power_bi"
    assert res.get("report_id") == "00000000-0000-0000-0000-000000000000"
    assert res.get("auth_required") is True


def test_parse_power_bi_with_embed_url_and_default_auth():
    html = (
        '<div class="embed-power-bi" '
        'data-snippet-type="power_bi" '
        'data-embed-url="https://app.powerbi.com/reportEmbed?x=1"></div>'
    )
    res = parse_snippet_embed(html)
    assert res is not None
    assert res.get("type") == "power_bi"
    assert res.get("report_id") is None
    assert res.get("embed_url", "").startswith("https://")
    # default is True when data-auth-required missing
    assert res.get("auth_required") is True


def test_parse_non_power_bi_returns_none():
    html = '<div data-snippet-type="tableau" data-report-id="x"></div>'
    assert parse_snippet_embed(html) is None


def test_parse_empty_or_none_returns_none():
    assert parse_snippet_embed("") is None
    # Defensive handling: function returns None for falsy html
    # NOTE: pass a whitespace-only string instead of None to satisfy type check
    assert parse_snippet_embed("   ") is None
