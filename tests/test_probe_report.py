import json
from datetime import UTC, datetime

import pytest

from panel_fondos.collectors import probe_report as pr

BASE = datetime(2026, 11, 6, 10, 0, tzinfo=UTC).timestamp()


def run(
    offset_s: float, price: float | None = 1.0, status: int = 200, event: str = "schedule"
) -> dict:
    ts = datetime.fromtimestamp(BASE + offset_s, UTC).isoformat(timespec="seconds")
    return {
        "run_ts_utc": ts,
        "event": event,
        "quotes": [{"symbol": "A", "price": price, "http_status": status}],
    }


def test_analyze_counts_on_time_late_and_missed():
    runs = [
        run(30),  # slot 0, 30 s late: on time
        run(300 + 240),  # slot 1, 240 s late: late
        # slot 2 missing
        run(900 + 10),  # slot 3, on time
        run(900 + 100),  # duplicate in slot 3
    ]
    res = pr.analyze(runs, on_time_s=180)
    assert res["expected_slots"] == 4
    assert res["slots_with_run"] == 3
    assert res["missed_slots"] == 1
    assert res["duplicate_runs"] == 1
    assert res["on_time_pct"] == pytest.approx(50.0)
    assert res["delay_max_s"] == 240
    assert res["delay_p50_s"] == 30


def test_run_delayed_past_slot_counts_as_missed():
    res = pr.analyze([run(10), run(300 + 310)], on_time_s=180)  # second lands in slot 2
    assert res["expected_slots"] == 3 and res["missed_slots"] == 1


def test_per_symbol_nulls_and_http():
    res = pr.analyze([run(0), run(300, price=None, status=429)])
    c = res["per_symbol"]["A"]
    assert c["total"] == 2 and c["null"] == 1 and c["http_429"] == 1 and c["http_200"] == 1


def test_load_runs_since_and_markdown(tmp_path):
    f = tmp_path / "p.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in [run(0), run(600)]) + "\n\n")
    since = datetime.fromtimestamp(BASE + 300, UTC)
    runs = pr.load_runs(f, since)
    assert len(runs) == 1
    md = pr.to_markdown(pr.analyze(pr.load_runs(f)))
    assert "| A | 2 | 0 | 200: 2 |" in md and "perdidos: 1" in md


def test_empty_raises():
    with pytest.raises(ValueError):
        pr.analyze([])


def test_manual_runs_excluded_from_punctuality():
    res = pr.analyze([run(250), run(20, event="workflow_dispatch")], on_time_s=180)
    assert res["scheduled_runs"] == 1 and res["manual_or_local_runs"] == 1
    assert res["on_time_pct"] == 0.0


def test_gaps_expose_delay_beyond_slot():
    # slot 1 run is 420 s late (lands in slot 2), slot 3 on time
    res = pr.analyze([run(0), run(300 + 420), run(900)], on_time_s=180)
    assert res["gap_max_s"] == 720
    assert res["gaps_ok_pct"] == pytest.approx(50.0)
