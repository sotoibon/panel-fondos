import csv
from datetime import date
from pathlib import Path

import pytest
import requests

from panel_fondos.collectors import nav

FIXTURES = Path(__file__).parent / "fixtures"

WORLD, EM, NASDAQ, VANGUARD = "IE000ZYRH0Q7", "IE000QAZP7L2", "ES0165265002", "IE00B42W4L06"
YAHOO_SYMBOL = {
    WORLD: "0P0001XF40.F",
    EM: "0P0001XF3Z.F",
    NASDAQ: "0P0001MRGW.F",
    VANGUARD: "0P0000XR9M.F",
}


def raw(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class FakeResponse:
    def __init__(self, status: int, content: bytes = b""):
        self.status_code = status
        self.content = content


class FakeSession:
    """Responde por trozo de URL; una lista se reproduce en orden (y repite la última)."""

    def __init__(self, routes: dict[str, FakeResponse | Exception | list]):
        self.routes = routes
        self.calls: list[str] = []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append(url)
        for fragment, item in self.routes.items():
            if fragment in url:
                if isinstance(item, list):
                    n = sum(1 for c in self.calls if fragment in c) - 1
                    item = item[min(n, len(item) - 1)]
                if isinstance(item, Exception):
                    raise item
                return item
        return FakeResponse(404)


def all_routes() -> dict:
    routes: dict = {
        f"chart/{s}": FakeResponse(200, raw(f"yahoo_nav_{s}.json")) for s in YAHOO_SYMBOL.values()
    }
    routes["/345277/"] = FakeResponse(200, raw("ishares_nav_history.xls"))
    routes["/345276/"] = FakeResponse(200, raw("ishares_nav_history.xls"))
    routes["ch.vanguard"] = FakeResponse(200, raw("vanguard_fund_page.html"))
    return routes


def no_sleep(_):
    pass


# ------------------------------------------------------------------ parsers


def test_parse_yahoo_uses_berlin_date_and_drops_nulls():
    rows = nav.parse_yahoo(raw(f"yahoo_nav_{YAHOO_SYMBOL[NASDAQ]}.json"))
    assert rows == sorted(rows)
    assert all(isinstance(v, float) for _, v in rows)
    # Los últimos días del fixture son nulos: el último NAV es anterior al último timestamp.
    assert rows[-1][0] < date(2026, 11, 6)


def test_parse_yahoo_timestamp_is_local_not_utc():
    # 2026-11-04 08:00 en Berlín (CET, UTC+1) = 07:00 UTC; si fuera en UTC seguiría siendo 04-nov,
    # pero 00:30 locales del 05-nov son 23:30 UTC del 04-nov: la fecha debe ser la local.
    payload = {
        "chart": {
            "result": [
                {
                    "meta": {"exchangeTimezoneName": "Europe/Berlin"},
                    "timestamp": [1793835000],  # 2026-11-04T23:30:00Z = 05-nov 00:30 Berlín
                    "indicators": {"quote": [{"close": [1.5]}]},
                }
            ]
        }
    }
    assert nav.parse_yahoo(payload) == [(date(2026, 11, 5), 1.5)]


def test_parse_yahoo_rejects_garbage():
    with pytest.raises(nav.NavParseError):
        nav.parse_yahoo({"chart": {"result": None}})
    with pytest.raises(nav.NavParseError):
        nav.parse_yahoo(b"not json")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("05.Nov.2026", date(2026, 11, 5)),
        ("31.Juli2026", date(2026, 7, 31)),
        ("30.Juni2026", date(2026, 6, 30)),
        ("31.März2026", date(2026, 3, 31)),
        ("30.Sept.2026", date(2026, 9, 30)),
        ("29.Mai2026", date(2026, 5, 29)),
        ("30.Okt.2026", date(2026, 10, 30)),
        ("30.Dez.2025", date(2025, 12, 30)),
    ],
)
def test_parse_de_date_variants(text, expected):
    assert nav.parse_de_date(text) == expected


def test_parse_de_date_rejects_unknown_month():
    with pytest.raises(nav.NavParseError):
        nav.parse_de_date("05.Foo.2026")


def test_parse_ishares_fixture():
    rows = nav.parse_ishares(raw("ishares_nav_history.xls"))
    d = dict(rows)
    assert d[date(2026, 11, 5)] == pytest.approx(12.092755)
    assert d[date(2026, 11, 4)] == pytest.approx(12.494146)
    assert date(2026, 7, 31) in d and date(2026, 3, 31) in d  # meses irregulares
    assert rows == sorted(rows)


def test_parse_ishares_errors():
    with pytest.raises(nav.NavParseError):
        nav.parse_ishares(b"<html>no es xml")
    other_sheet = raw("ishares_nav_history.xls").replace(b"Historisch", b"Otra")
    with pytest.raises(nav.NavParseError, match="Historisch"):
        nav.parse_ishares(other_sheet)


def test_parse_vanguard_fixture():
    rows = nav.parse_vanguard(raw("vanguard_fund_page.html"))
    d = dict(rows)
    assert d[date(2026, 11, 5)] == pytest.approx(425.6129)
    assert d[date(2026, 11, 4)] == pytest.approx(435.4551)
    assert len(rows) >= 5


def test_parse_vanguard_without_table_fails():
    with pytest.raises(nav.NavParseError):
        nav.parse_vanguard("<html><body><table><tr><th>X</th></tr></table></body></html>")


# ------------------------------------------------------------------ red


def test_get_with_retries_recovers_from_429():
    s = FakeSession({"x": [FakeResponse(429), FakeResponse(200, b"ok")]})
    assert nav.get_with_retries(s, "https://x", retries=2, sleep=no_sleep) == (b"ok", None)
    assert len(s.calls) == 2


def test_get_with_retries_gives_up_without_raising():
    s = FakeSession({"x": [requests.ConnectionError("boom")]})
    content, error = nav.get_with_retries(s, "https://x", retries=1, sleep=no_sleep)
    assert content is None and "ConnectionError" in error
    assert len(s.calls) == 2


def test_get_with_retries_does_not_retry_404():
    s = FakeSession({"x": FakeResponse(404)})
    assert nav.get_with_retries(s, "https://x", retries=3, sleep=no_sleep) == (None, "HTTP 404")
    assert len(s.calls) == 1


def test_cache_avoids_second_request_and_expires(tmp_path):
    s = FakeSession({"x": FakeResponse(200, b"data")})
    t = [1000.0]
    kw = {"cache_dir": tmp_path, "ttl_s": 100, "now": lambda: t[0], "sleep": no_sleep}
    assert nav.cached_get(s, "https://x", None, **kw)[0] == b"data"
    assert nav.cached_get(s, "https://x", None, **kw)[0] == b"data"
    assert len(s.calls) == 1
    import os

    for p in tmp_path.iterdir():
        os.utime(p, (1000.0, 1000.0))
    t[0] = 1000.0 + 101
    nav.cached_get(s, "https://x", None, **kw)
    assert len(s.calls) == 2


# ------------------------------------------------------------------ CSV


def _row(d: date, v: float, src="yahoo", fetched="2026-11-06T10:00:00Z") -> nav.NavRow:
    return nav.NavRow(WORLD, d, v, "EUR", src, fetched)


def test_upsert_csv_is_idempotent(tmp_path):
    out = tmp_path / "nav.csv"
    rows = [_row(date(2026, 11, 4), 12.5), _row(date(2026, 11, 3), 12.4)]
    assert nav.upsert_csv(rows, out) == 2
    first = out.read_text()
    later = [_row(r.nav_date, r.nav, fetched="2026-11-07T10:00:00Z") for r in rows]
    assert nav.upsert_csv(later, out) == 0
    assert out.read_text() == first  # ni duplica ni cambia fetched_at


def test_upsert_csv_updates_revised_nav_and_keeps_sources_apart(tmp_path):
    out = tmp_path / "nav.csv"
    nav.upsert_csv(
        [_row(date(2026, 11, 4), 12.5), _row(date(2026, 11, 4), 12.6, src="ishares")], out
    )
    nav.upsert_csv([_row(date(2026, 11, 4), 12.55)], out)
    with open(out, newline="") as fh:
        recs = list(csv.DictReader(fh))
    assert len(recs) == 2
    by_src = {r["source"]: float(r["nav"]) for r in recs}
    assert by_src == {"yahoo": 12.55, "ishares": 12.6}


# ------------------------------------------------------------------ CLI


def test_cli_all_prints_last_nav_and_date_per_fund(tmp_path, capsys):
    out = tmp_path / "nav.csv"
    code = nav.main(
        ["--isin", "all", "--no-cache", "--out", str(out)],
        session=FakeSession(all_routes()),
        sleep=no_sleep,
    )
    text = capsys.readouterr().out
    assert code == 0
    for isin in (WORLD, EM, NASDAQ, VANGUARD):
        assert isin in text
    assert "12.0928 EUR fecha 2026-11-05 (ishares)" in text
    assert "425.6129 EUR fecha 2026-11-05 (vanguard)" in text
    assert "contraste yahoo: último día común" in text
    sources = {r["source"] for r in csv.DictReader(open(out, newline=""))}
    assert sources == {"ishares", "vanguard", "yahoo"}
    # Segunda ejecución: mismo CSV.
    before = out.read_text()
    nav.main(["--no-cache", "--out", str(out)], session=FakeSession(all_routes()), sleep=no_sleep)
    assert out.read_text() == before


def test_cli_falls_back_to_yahoo_when_primary_keeps_failing(tmp_path, capsys):
    routes = all_routes()
    routes["/345277/"] = FakeResponse(500)
    code = nav.main(
        ["--isin", WORLD, "--no-cache", "--no-write"], session=FakeSession(routes), sleep=no_sleep
    )
    text = capsys.readouterr().out
    assert code == 0
    assert "(yahoo)" in text and "respaldo" in text and "HTTP 500" in text


def test_cli_exit_1_when_a_fund_has_no_nav(tmp_path, capsys):
    routes = all_routes()
    routes[f"chart/{YAHOO_SYMBOL[NASDAQ]}"] = FakeResponse(429)
    code = nav.main(["--no-cache", "--no-write"], session=FakeSession(routes), sleep=no_sleep)
    text = capsys.readouterr().out
    assert code == 1
    assert f"{NASDAQ}" in text and "SIN NAV" in text
    assert "12.0928" in text  # los demás fondos siguen apareciendo


def test_cli_unknown_isin_exit_2(capsys):
    assert nav.main(["--isin", "XX0000000000"], session=FakeSession({}), sleep=no_sleep) == 2


def test_each_fund_keeps_its_own_nav_date():
    rows_by_fund = {}
    session = FakeSession(all_routes())
    from panel_fondos.config import load_funds

    for isin, fund in load_funds().items():
        ok, _ = nav.collect_fund(
            session,
            fund,
            settings=nav.load_settings(),
            yahoo_range="1mo",
            use_cache=False,
            fetched_at="t",
            sleep=no_sleep,
        )
        rows_by_fund[isin] = max(r.nav_date for r in next(iter(ok.values())))
    assert rows_by_fund[NASDAQ] < rows_by_fund[WORLD]  # Yahoo T+3 frente a iShares T+1


def test_settings_validation(tmp_path):
    good = nav.load_settings()
    assert good["retries"] >= 0 and "{symbol}" in good["yahoo_url"]
    bad = tmp_path / "nav.yaml"
    bad.write_text("retries: 2\n", encoding="utf-8")
    with pytest.raises(nav.ConfigError, match="yahoo_url"):
        nav.load_settings(bad)


def test_parsers_turn_impossible_dates_and_null_stamps_into_parse_errors():
    with pytest.raises(nav.NavParseError, match="imposible"):
        nav.parse_de_date("31.Juni2026")
    with pytest.raises(nav.NavParseError, match="imposible"):
        nav.parse_en_date("31 Nov 2026")
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [None, 1793835000],
                    "indicators": {"quote": [{"close": [1.0, 2.0]}]},
                }
            ]
        }
    }
    assert nav.parse_yahoo(payload) == [(date(2026, 11, 5), 2.0)]


def test_cli_survives_a_fund_whose_source_returns_unparseable_dates(capsys):
    routes = all_routes()
    routes["/345277/"] = FakeResponse(
        200, raw("ishares_nav_history.xls").replace(b"05.Nov.2026", b"31.Juni2026")
    )
    code = nav.main(["--no-cache", "--no-write"], session=FakeSession(routes), sleep=no_sleep)
    text = capsys.readouterr().out
    assert code == 0
    assert "fecha imposible" in text  # iShares World cae a Yahoo, el resto sigue
    assert EM in text and VANGUARD in text and NASDAQ in text
