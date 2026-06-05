from lib.score import btc_bottom_score


def test_score_all_inputs_present_returns_components_and_total():
    inputs = {
        "etf_net_flow_musd": 213.2,
        "funding_rate": 0.00008,
        "fng_value": 42,
        "long_short_ratio": 1.85,
    }
    result = btc_bottom_score(**inputs)
    assert "components" in result
    assert "total" in result
    assert 0 <= result["total"] <= 100
    assert result["rating"] in {
        "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed",
    }
    assert result["partial"] is False


def test_score_missing_input_returns_partial_true():
    result = btc_bottom_score(
        etf_net_flow_musd=None,
        funding_rate=0.00008,
        fng_value=42,
        long_short_ratio=1.85,
    )
    assert result["partial"] is True
    assert result["components"]["etf_net_flow"] is None


def test_score_extreme_fear_under_15():
    # All bearish: huge outflows, negative funding, F&G 5, low L/S
    r = btc_bottom_score(
        etf_net_flow_musd=-500.0,
        funding_rate=-0.0005,
        fng_value=5,
        long_short_ratio=0.5,
    )
    assert r["total"] <= 15
    assert r["rating"] == "Extreme Fear"
