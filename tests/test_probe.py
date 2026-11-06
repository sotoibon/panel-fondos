import json
from pathlib import Path

import requests

from panel_fondos.collectors import probe

FIXTURES = Path(__file__).parent / "fixtures"
CFG = {
    "symbols": ["EUNL.DE", "ES=F", "NQ=F", "EURUSD=X"],
    "url": "https://example.test/chart/{symbol}",
    "params": {},
    "timeout_s": 1,
    "retries": 1,
    "backoff_s": 0,
}


class FakeResponse:
    def __init__(self, status: int, payload=None, bad_json: bool = False):
        self.status_code = status
        self._payload = payload
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("bad json")
        return self._payload


class FakeSession:
    """Plays back a list of responses (or exceptions) per call, then repeats the last one."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        item = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item

    def close(self):
        pass


def fixture(symbol: str) -> dict:
    return json.loads((FIXTURES / f"yahoo_chart_{symbol}.json").read_text())


def test_fetch_quote_parses_recorded_response():
    session = FakeSession([FakeResponse(200, fixture("EUNL.DE"))])
    q = probe.fetch_quote("EUNL.DE", session, CFG)
    assert q["price"] is not None and q["currency"] == "EUR"
    assert q["http_status"] == 200 and q["error"] is None
    assert isinstance(q["market_time"], int)


def test_null_price_is_recorded_not_raised():
    payload = fixture("NQ=F")
    payload["chart"]["result"][0]["meta"]["regularMarketPrice"] = None
    q = probe.fetch_quote("NQ=F", FakeSession([FakeResponse(200, payload)]), CFG)
    assert q["price"] is None and q["error"] == "null price"


def test_429_retries_then_succeeds():
    session = FakeSession([FakeResponse(429), FakeResponse(200, fixture("ES=F"))])
    q = probe.fetch_quote("ES=F", session, CFG)
    assert session.calls == 2 and q["price"] is not None


def test_429_persistent_is_reported():
    session = FakeSession([FakeResponse(429)])
    q = probe.fetch_quote("ES=F", session, CFG)
    assert session.calls == 2
    assert q["price"] is None and q["http_status"] == 429


def test_network_error_is_reported():
    session = FakeSession([requests.ConnectionError("boom")])
    q = probe.fetch_quote("ES=F", session, CFG)
    assert q["price"] is None and q["http_status"] is None and "ConnectionError" in q["error"]


def test_malformed_json_and_structure():
    q = probe.fetch_quote("X", FakeSession([FakeResponse(200, bad_json=True)]), CFG)
    assert q["error"] == "malformed response"
    q = probe.fetch_quote("X", FakeSession([FakeResponse(200, {"chart": {"result": None}})]), CFG)
    assert q["error"] == "malformed response"


def test_404_is_not_retried():
    session = FakeSession([FakeResponse(404)])
    q = probe.fetch_quote("X", session, CFG)
    assert session.calls == 1 and q["http_status"] == 404


def test_run_probe_and_append_jsonl(tmp_path):
    responses = [FakeResponse(200, fixture(s)) for s in CFG["symbols"]]
    record = probe.run_probe(CFG, FakeSession(responses))
    assert [q["symbol"] for q in record["quotes"]] == CFG["symbols"]
    assert all(q["price"] is not None for q in record["quotes"])
    out = tmp_path / "sub" / "p.jsonl"
    probe.append_jsonl(record, out)
    probe.append_jsonl(record, out)
    lines = out.read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["run_ts_utc"] == record["run_ts_utc"]


def test_load_default_config():
    cfg = probe.load_config()
    assert cfg["symbols"] == ["EUNL.DE", "ES=F", "NQ=F", "EURUSD=X"]
