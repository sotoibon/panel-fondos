"""Yahoo Finance reliability probe (T-02).

Fetches one batch of symbols from the public chart endpoint and optionally appends the
result as one JSON line, so cron punctuality and Yahoo blocking can be measured over days.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml

log = logging.getLogger(__name__)

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "configs" / "probe.yaml"


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _empty(symbol: str, status: int | None, error: str | None) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "price": None,
        "market_time": None,
        "currency": None,
        "http_status": status,
        "error": error,
    }


def fetch_quote(symbol: str, session: requests.Session, cfg: dict[str, Any]) -> dict[str, Any]:
    """Return one quote record; never raises. Retries on 429/5xx and network errors."""
    url = cfg["url"].format(symbol=symbol)
    attempts = int(cfg.get("retries", 1)) + 1
    record = _empty(symbol, None, "no attempt")
    for attempt in range(attempts):
        if attempt:
            time.sleep(float(cfg.get("backoff_s", 2.0)) * attempt)
        try:
            resp = session.get(url, params=cfg.get("params"), timeout=cfg.get("timeout_s", 15))
        except requests.RequestException as exc:
            record = _empty(symbol, None, f"request: {type(exc).__name__}")
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            record = _empty(symbol, resp.status_code, f"http {resp.status_code}")
            continue
        if resp.status_code != 200:
            return _empty(symbol, resp.status_code, f"http {resp.status_code}")
        try:
            meta = resp.json()["chart"]["result"][0]["meta"]
        except (ValueError, KeyError, IndexError, TypeError):
            return _empty(symbol, 200, "malformed response")
        price = meta.get("regularMarketPrice")
        record = {
            "symbol": symbol,
            "price": price,
            "market_time": meta.get("regularMarketTime"),
            "currency": meta.get("currency"),
            "http_status": 200,
            "error": None if price is not None else "null price",
        }
        return record
    return record


def run_probe(cfg: dict[str, Any], session: requests.Session | None = None) -> dict[str, Any]:
    """Fetch every configured symbol once and return one run record."""
    own = session is None
    session = session or requests.Session()
    session.headers["User-Agent"] = cfg.get("user_agent", "panel-fondos-probe")
    try:
        started = datetime.now(UTC)
        quotes = [fetch_quote(s, session, cfg) for s in cfg["symbols"]]
    finally:
        if own:
            session.close()
    return {
        "run_ts_utc": started.isoformat(timespec="seconds"),
        "job_start_utc": os.environ.get("PROBE_JOB_START"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "event": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "quotes": quotes,
    }


def append_jsonl(record: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=None, help="append the run as a JSONL line")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    record = run_probe(load_config(args.config))
    if args.out:
        append_jsonl(record, args.out)
    bad = 0
    for q in record["quotes"]:
        if q["price"] is None:
            bad += 1
            log.warning("%s: no price (%s)", q["symbol"], q["error"])
        else:
            log.info("%s: %s %s", q["symbol"], q["price"], q["currency"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
