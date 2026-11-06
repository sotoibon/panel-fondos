import copy

import pytest
import yaml

from panel_fondos.config import DEFAULT_PATH, ConfigError, isin_checksum_ok, load_funds, validate

EXPECTED = {"IE000ZYRH0Q7", "IE000QAZP7L2", "ES0165265002", "IE00B42W4L06"}


@pytest.fixture
def raw():
    return yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))


def test_loads_the_four_funds():
    assert set(load_funds()) == EXPECTED


def test_isin_checksum():
    assert all(isin_checksum_ok(i) for i in EXPECTED)
    assert not isin_checksum_ok("IE000ZYRH0Q8")


def test_nasdaq_has_no_published_valuation_point_and_unknown_hedge():
    f = load_funds()["ES0165265002"]
    assert f["dealing"]["valuation_point"] is None
    assert f["fx"]["hedged"] == "unknown"


def _bad(raw, mutate):
    data = copy.deepcopy(raw)
    mutate(data["funds"][0])
    with pytest.raises(ConfigError) as exc:
        validate(data)
    return str(exc.value)


def test_missing_required_field_fails(raw):
    assert "dealing" in _bad(raw, lambda f: f.pop("dealing"))


def test_bad_isin_fails(raw):
    assert "ISIN inválido" in _bad(raw, lambda f: f.update(isin="IE000ZYRH0Q8"))


def test_bad_time_and_timezone_fail(raw):
    def m(f):
        f["dealing"]["cutoff_local"] = "25:99"
        f["dealing"]["cutoff_tz"] = "Mars/Olympus"

    msg = _bad(raw, m)
    assert "cutoff_local" in msg and "cutoff_tz" in msg


def test_bad_proxy_fails(raw):
    msg = _bad(raw, lambda f: f["proxies"][0].update(kind="crystal_ball", delay_min=-1))
    assert "kind" in msg and "delay_min" in msg


def test_duplicate_isin_fails(raw):
    raw["funds"].append(copy.deepcopy(raw["funds"][0]))
    with pytest.raises(ConfigError, match="duplicado"):
        validate(raw)


def test_nav_sources_need_their_block(raw):
    # funds[0] usa ishares
    assert "nav.ishares" in _bad(raw, lambda f: f["nav"].pop("ishares"))


def test_investing_is_no_longer_a_source(raw):
    assert "nav.sources" in _bad(raw, lambda f: f["nav"].update(sources=["investing", "yahoo"]))
