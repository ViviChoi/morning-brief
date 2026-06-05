from pathlib import Path
import responses
from lib.fetch import fetch_btc_etf_net_flow_musd

HTML = Path("tests/fixtures/farside_btc_etf.html").read_text()


@responses.activate
def test_fetch_btc_etf_net_flow_latest_row():
    responses.add(
        responses.GET,
        "https://farside.co.uk/bitcoin-etf-flow-all-data/",
        body=HTML,
        status=200,
        content_type="text/html",
    )
    flow = fetch_btc_etf_net_flow_musd()
    assert flow is not None
    assert abs(flow - 213.2) < 1e-6
