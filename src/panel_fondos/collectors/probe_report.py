"""Reliability report for the T-02 probe JSONL (cron punctuality and Yahoo failures).

A run is assigned to the 5-minute slot that contains its start time; its delay is the offset
inside that slot. A run delayed past the next boundary therefore lands in a later slot and
leaves its own slot empty (counted as missed), so slot delay alone hides lateness over 5 min;
the consecutive-gap statistics expose it.
Only runs with event == "schedule" count for punctuality (manual and local runs are excluded).
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SLOT_S = 300


def load_runs(path: Path, since: datetime | None = None) -> list[dict[str, Any]]:
    runs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        run = json.loads(line)
        if since and datetime.fromisoformat(run["run_ts_utc"]) < since:
            continue
        runs.append(run)
    return runs


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def analyze(runs: list[dict[str, Any]], on_time_s: int = 180) -> dict[str, Any]:
    if not runs:
        raise ValueError("no runs to analyze")
    sched = [r for r in runs if r.get("event") == "schedule"]
    if not sched:
        raise ValueError("no runs with event == 'schedule'")
    # Job start (before checkout/uv sync) when recorded, else the probe's own timestamp.
    ts = sorted(
        datetime.fromisoformat(r.get("job_start_utc") or r["run_ts_utc"]).timestamp() for r in sched
    )
    slots = defaultdict(list)
    for t in ts:
        slots[int(t // SLOT_S)].append(t - (t // SLOT_S) * SLOT_S)
    first, last = min(slots), max(slots)
    expected = last - first + 1
    delays = [min(d) for d in slots.values()]  # first run of each slot
    on_time = sum(1 for d in delays if d <= on_time_s)
    gaps = [b - a for a, b in zip(ts, ts[1:], strict=False)]
    gap_ok = sum(1 for g in gaps if g <= SLOT_S + on_time_s)
    per_symbol: dict[str, Counter] = defaultdict(Counter)
    for run in runs:
        for q in run["quotes"]:
            c = per_symbol[q["symbol"]]
            c["total"] += 1
            c["null"] += q["price"] is None
            c[f"http_{q['http_status']}"] += 1
    return {
        "runs": len(runs),
        "scheduled_runs": len(sched),
        "gap_p50_s": statistics.median(gaps) if gaps else 0.0,
        "gap_p90_s": _percentile(gaps, 90) if gaps else 0.0,
        "gap_max_s": max(gaps) if gaps else 0.0,
        "gaps_ok_pct": 100 * gap_ok / len(gaps) if gaps else 100.0,
        "start": datetime.fromtimestamp(ts[0], UTC).isoformat(timespec="minutes"),
        "end": datetime.fromtimestamp(ts[-1], UTC).isoformat(timespec="minutes"),
        "expected_slots": expected,
        "slots_with_run": len(slots),
        "missed_slots": expected - len(slots),
        "duplicate_runs": len(ts) - len(slots),
        "manual_or_local_runs": len(runs) - len(sched),
        "on_time_s": on_time_s,
        "on_time_pct": 100 * on_time / expected,
        "delay_p50_s": statistics.median(delays),
        "delay_p90_s": _percentile(delays, 90),
        "delay_max_s": max(delays),
        "per_symbol": {s: dict(c) for s, c in sorted(per_symbol.items())},
    }


def to_markdown(res: dict[str, Any]) -> str:
    lines = [
        f"**Ventana:** {res['start']} → {res['end']} UTC · {res['runs']} ejecuciones",
        "",
        f"- Slots de 5 min esperados: {res['expected_slots']}; con ejecución: "
        f"{res['slots_with_run']}; perdidos: {res['missed_slots']}; "
        f"ejecuciones duplicadas: {res['duplicate_runs']}",
        f"- A tiempo (arranque ≤ {res['on_time_s']} s del slot, sobre slots esperados): "
        f"**{res['on_time_pct']:.1f} %**",
        f"- Retraso dentro del slot: p50 {res['delay_p50_s']:.0f} s · "
        f"p90 {res['delay_p90_s']:.0f} s · máx {res['delay_max_s']:.0f} s",
        f"- Hueco entre ejecuciones consecutivas (ideal 300 s): p50 {res['gap_p50_s']:.0f} s · "
        f"p90 {res['gap_p90_s']:.0f} s · máx {res['gap_max_s']:.0f} s · "
        f"{res['gaps_ok_pct']:.1f} % ≤ {SLOT_S + res['on_time_s']} s",
        "",
        "| Símbolo | Peticiones | Nulos | Estados HTTP |",
        "|---|---|---|---|",
    ]
    for sym, c in res["per_symbol"].items():
        http = ", ".join(f"{k[5:]}: {v}" for k, v in sorted(c.items()) if k.startswith("http_"))
        lines.append(f"| {sym} | {c['total']} | {c.get('null', 0)} | {http} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--since", type=datetime.fromisoformat, default=None)
    parser.add_argument("--on-time-s", type=int, default=180)
    args = parser.parse_args(argv)
    since = args.since.replace(tzinfo=UTC) if args.since and not args.since.tzinfo else args.since
    runs = load_runs(args.input, since)
    print(to_markdown(analyze(runs, args.on_time_s)))  # noqa: T201 (CLI output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
