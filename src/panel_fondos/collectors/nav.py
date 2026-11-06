"""Descarga del NAV oficial de los fondos (T-04).

Fuentes (por fondo, en el orden de ``nav.sources`` de ``configs/funds.yaml``; la primera que
devuelve datos es la principal y el resto sirven de contraste):

- ``ishares``: fichero SpreadsheetML oficial de iShares con el histórico completo.
- ``vanguard``: tabla de los últimos NAV en el HTML de la ficha del fondo (no hay histórico largo).
- ``yahoo``: gráfico ``0P…F`` (T+2/T+3, con nulos al final).

Cada NAV lleva **su propia fecha**; nunca se asume una fecha común entre fondos. Investing.com
queda fuera: sus condiciones de uso prohíben almacenar sus datos (ver D-014).

Los parsers son puros (sin red) y las peticiones usan una sesión inyectable para los tests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml

from panel_fondos.config import DEFAULT_PATH, ConfigError, load_funds

SETTINGS_PATH = Path(__file__).resolve().parents[3] / "configs" / "nav.yaml"
ISHARES_SHEET = "Historisch"
YAHOO_TZ = "Europe/Berlin"  # la marca de tiempo de Yahoo es 08:00 locales del día del NAV
CSV_FIELDS = ["isin", "nav_date", "nav", "currency", "source", "fetched_at"]
_SETTING_KEYS = {
    "user_agent": str, "timeout_s": (int, float), "retries": int, "backoff_s": (int, float),
    "cache_dir": str, "cache_ttl_s": (int, float), "out": str, "yahoo_url": str,
    "ishares_url": str, "ishares_ajax_id": str,
}  # fmt: skip


def load_settings(path: Path | str = SETTINGS_PATH) -> dict:
    """Carga ``configs/nav.yaml`` y comprueba que están todas las claves con su tipo."""
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path}: se esperaba un mapa")
    errors = [
        f"{path}: falta o es inválida la clave {k!r}"
        for k, t in _SETTING_KEYS.items()
        if not isinstance(cfg.get(k), t) or isinstance(cfg.get(k), bool)
    ]
    if errors:
        raise ConfigError("\n".join(errors))
    return cfg


class NavParseError(ValueError):
    """La respuesta de una fuente no tiene el formato esperado."""


@dataclass(frozen=True)
class NavRow:
    isin: str
    nav_date: date
    nav: float
    currency: str
    source: str
    fetched_at: str

    def as_csv(self) -> dict[str, str]:
        return {
            "isin": self.isin,
            "nav_date": self.nav_date.isoformat(),
            "nav": repr(self.nav),
            "currency": self.currency,
            "source": self.source,
            "fetched_at": self.fetched_at,
        }


# --------------------------------------------------------------------------- parsers


def parse_yahoo(payload: dict | bytes | str) -> list[tuple[date, float]]:
    """Pares (fecha del NAV, NAV) del gráfico de Yahoo; descarta los nulos."""
    if isinstance(payload, (bytes, str)):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise NavParseError(f"Yahoo: JSON inválido ({exc})") from exc
    try:
        result = payload["chart"]["result"][0]
        stamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NavParseError(f"Yahoo: respuesta sin timestamp/close ({exc!r})") from exc
    tz = ZoneInfo(result.get("meta", {}).get("exchangeTimezoneName") or YAHOO_TZ)
    out = []
    for ts, close in zip(stamps, closes, strict=False):
        if close is None or ts is None:
            continue
        try:
            out.append((datetime.fromtimestamp(ts, tz).date(), float(close)))
        except (TypeError, ValueError, OverflowError, OSError) as exc:
            raise NavParseError(f"Yahoo: valor inválido ({ts!r}, {close!r})") from exc
    if not out:
        raise NavParseError("Yahoo: ningún valor no nulo")
    return sorted(out)


_DE_MONTHS = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4, "mai": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}  # fmt: skip
_EN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}  # fmt: skip
_DE_DATE = re.compile(r"^(\d{1,2})\.\s*([A-Za-zäÄ]+)\.?\s*(\d{4})$")
_EN_DATE = re.compile(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$")


def _safe_date(year: int, month: int, day: int, text: str, source: str) -> date:
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise NavParseError(f"{source}: fecha imposible {text!r}") from exc


def parse_de_date(text: str) -> date:
    """«05.Nov.2026», «31.Juli2026», «31.März2026», «30.Sept.2026» → date."""
    m = _DE_DATE.match(text.strip())
    month = _DE_MONTHS.get(m.group(2).lower()[:3]) if m else None
    if not m or month is None:
        raise NavParseError(f"iShares: fecha no reconocida {text!r}")
    return _safe_date(int(m.group(3)), month, int(m.group(1)), text, "iShares")


def parse_en_date(text: str) -> date:
    """«05 Nov 2026» → date."""
    m = _EN_DATE.match(text.strip())
    month = _EN_MONTHS.get(m.group(2).lower()[:3]) if m else None
    if not m or month is None:
        raise NavParseError(f"Vanguard: fecha no reconocida {text!r}")
    return _safe_date(int(m.group(3)), month, int(m.group(1)), text, "Vanguard")


def parse_ishares(content: bytes) -> list[tuple[date, float]]:
    """Hoja «Historisch» del SpreadsheetML de iShares: columnas ``per | NAV | …``."""
    text = content.decode("utf-8", errors="replace").lstrip("﻿")
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as exc:
        raise NavParseError(f"iShares: XML inválido ({exc})") from exc
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    name_attr = "{urn:schemas-microsoft-com:office:spreadsheet}Name"
    sheet = next(
        (ws for ws in root.findall("ss:Worksheet", ns) if ws.get(name_attr) == ISHARES_SHEET),
        None,
    )
    if sheet is None:
        raise NavParseError(f"iShares: no hay hoja {ISHARES_SHEET!r}")
    out = []
    for i, row in enumerate(sheet.findall("ss:Table/ss:Row", ns)):
        cells = [(c.findtext("ss:Data", default="", namespaces=ns) or "") for c in row]
        if i == 0:
            if len(cells) < 2 or cells[0].strip() != "per" or cells[1].strip() != "NAV":
                raise NavParseError(f"iShares: cabecera inesperada {cells[:2]!r}")
            continue
        if len(cells) < 2 or not cells[0].strip():
            continue
        try:
            nav = float(cells[1])
        except ValueError as exc:
            raise NavParseError(f"iShares: NAV no numérico {cells[1]!r}") from exc
        out.append((parse_de_date(cells[0]), nav))
    if not out:
        raise NavParseError("iShares: hoja sin filas de NAV")
    return sorted(out)


class _NavTableParser(HTMLParser):
    """Recoge las filas de la tabla cuya cabecera es «Date | NAV …»."""

    def __init__(self) -> None:
        super().__init__()
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("th", "td") and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            head = self._table[0] if self._table else []
            if len(head) >= 2 and head[0] == "Date" and head[1].startswith("NAV"):
                self.rows = self._table[1:]
            self._table = None


def parse_vanguard(html: bytes | str) -> list[tuple[date, float]]:
    """Tabla «Date | NAV (EUR)» de la ficha de Vanguard (últimos ~10 días)."""
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    parser = _NavTableParser()
    parser.feed(html)
    out = []
    for row in parser.rows:
        if len(row) < 2:
            continue
        digits = re.sub(r"[^\d.]", "", row[1].replace(",", ""))
        try:
            nav = float(digits)
        except ValueError as exc:
            raise NavParseError(f"Vanguard: NAV no numérico {row[1]!r}") from exc
        out.append((parse_en_date(row[0]), nav))
    if not out:
        raise NavParseError("Vanguard: no se encontró la tabla «Date | NAV»")
    return sorted(out)


# --------------------------------------------------------------------------- red y caché


def get_with_retries(
    session,
    url: str,
    params: dict | None = None,
    *,
    retries: int = 2,
    backoff_s: float = 2.0,
    timeout_s: float = 30,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[bytes | None, str | None]:
    """GET con reintentos en 429, 5xx y errores de red. Nunca lanza: ``(contenido, error)``."""
    error = "sin intentos"
    for attempt in range(1, retries + 2):
        try:
            resp = session.get(url, params=params, timeout=timeout_s)
        except requests.RequestException as exc:
            error = f"error de red: {exc.__class__.__name__}"
        else:
            if resp.status_code == 200:
                return resp.content, None
            error = f"HTTP {resp.status_code}"
            if resp.status_code != 429 and resp.status_code < 500:
                return None, error
        if attempt <= retries:
            sleep(backoff_s * attempt)
    return None, error


def _cache_path(cache_dir: Path, url: str, params: dict | None) -> Path:
    key = json.dumps([url, sorted((params or {}).items())])
    return cache_dir / hashlib.sha1(key.encode()).hexdigest()[:20]  # noqa: S324


def cached_get(
    session,
    url: str,
    params: dict | None,
    *,
    cache_dir: Path | None,
    ttl_s: float = 6 * 3600,
    now: Callable[[], float] = time.time,
    **kw,
) -> tuple[bytes | None, str | None]:
    """``get_with_retries`` con caché en disco de las respuestas 200 durante ``ttl_s``."""
    path = _cache_path(cache_dir, url, params) if cache_dir else None
    if path and path.exists() and now() - path.stat().st_mtime < ttl_s:
        return path.read_bytes(), None
    content, error = get_with_retries(session, url, params, **kw)
    if content is not None and path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return content, error


# --------------------------------------------------------------------------- orquestación


def fetch_source(
    session, source: str, fund: dict, *, settings: dict, yahoo_range: str, use_cache: bool, **kw
) -> list[tuple[date, float]]:
    """Descarga y parsea una fuente de un fondo. Lanza ``NavParseError`` o ``RuntimeError``."""
    nav_cfg = fund["nav"]
    if source == "yahoo":
        url = settings["yahoo_url"].format(symbol=nav_cfg["yahoo_symbol"])
        params = {"interval": "1d", "range": yahoo_range}
        parser = parse_yahoo
    elif source == "ishares":
        blk = nav_cfg["ishares"]
        url = settings["ishares_url"].format(
            product_id=blk["product_id"], ajax_id=settings["ishares_ajax_id"]
        )
        params = {"fileType": "xls", "fileName": blk["file_name"], "dataType": "fund"}
        parser = parse_ishares
    elif source == "vanguard":
        url, params, parser = nav_cfg["vanguard"]["url"], None, parse_vanguard
    else:  # pragma: no cover - lo impide la validación de config
        raise NavParseError(f"fuente desconocida {source!r}")
    content, error = cached_get(
        session,
        url,
        params,
        cache_dir=Path(settings["cache_dir"]) if use_cache else None,
        ttl_s=settings["cache_ttl_s"],
        retries=settings["retries"],
        backoff_s=settings["backoff_s"],
        timeout_s=settings["timeout_s"],
        **kw,
    )
    if content is None:
        raise RuntimeError(error)
    return parser(content)


def collect_fund(
    session, fund: dict, *, settings: dict, yahoo_range: str, use_cache: bool, fetched_at: str, **kw
) -> tuple[dict[str, list[NavRow]], dict[str, str]]:
    """Todas las fuentes del fondo: ``({fuente: filas}, {fuente: error})``."""
    ok: dict[str, list[NavRow]] = {}
    failed: dict[str, str] = {}
    for source in fund["nav"]["sources"]:
        try:
            pairs = fetch_source(
                session,
                source,
                fund,
                settings=settings,
                yahoo_range=yahoo_range,
                use_cache=use_cache,
                **kw,
            )
        except (NavParseError, RuntimeError) as exc:
            failed[source] = str(exc)
            continue
        ok[source] = [
            NavRow(fund["isin"], d, v, fund["share_currency"], source, fetched_at) for d, v in pairs
        ]
    return ok, failed


def upsert_csv(rows: list[NavRow], path: Path) -> int:
    """Añade/actualiza filas por clave (isin, source, nav_date). Devuelve las filas nuevas.

    Idempotente: si el NAV no cambia se conserva la fila (y su ``fetched_at``) tal cual.
    """
    existing: dict[tuple[str, str, str], dict[str, str]] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                existing[(r["isin"], r["source"], r["nav_date"])] = r
    added = 0
    for row in rows:
        rec = row.as_csv()
        key = (rec["isin"], rec["source"], rec["nav_date"])
        old = existing.get(key)
        if old is None:
            added += 1
        if old is None or float(old["nav"]) != row.nav:
            existing[key] = rec
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow(existing[key])
    os.replace(tmp, path)  # atómico: un corte no destruye el histórico
    return added


def _latest(rows: list[NavRow]) -> NavRow:
    return max(rows, key=lambda r: r.nav_date)


def main(
    argv: list[str] | None = None,
    *,
    session=None,
    funds_path: Path | str = DEFAULT_PATH,
    settings_path: Path | str = SETTINGS_PATH,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    ap = argparse.ArgumentParser(description="Último NAV oficial de los fondos y CSV normalizado")
    ap.add_argument("--isin", default="all", help="ISIN o 'all' (por defecto)")
    ap.add_argument("--out", type=Path, default=None, help="CSV de salida (por defecto, nav.yaml)")
    ap.add_argument("--range", dest="yahoo_range", default="1mo", help="rango de Yahoo (1mo, 5y…)")
    ap.add_argument("--no-cache", action="store_true", help="ignora la caché de .cache/nav")
    ap.add_argument("--no-write", action="store_true", help="no escribe el CSV")
    args = ap.parse_args(argv)

    try:
        funds = load_funds(funds_path)
        settings = load_settings(settings_path)
    except (ConfigError, OSError) as exc:
        print(f"error de configuración: {exc}", file=sys.stderr)
        return 2
    if args.isin != "all":
        if args.isin not in funds:
            print(f"ISIN desconocido: {args.isin} (hay {', '.join(funds)})", file=sys.stderr)
            return 2
        funds = {args.isin: funds[args.isin]}

    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = settings["user_agent"]
    out_path = args.out or Path(settings["out"])
    fetched_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_rows: list[NavRow] = []
    missing = 0
    for isin, fund in funds.items():
        ok, failed = collect_fund(
            session,
            fund,
            settings=settings,
            yahoo_range=args.yahoo_range,
            use_cache=not args.no_cache,
            fetched_at=fetched_at,
            sleep=sleep,
        )
        for rows in ok.values():
            all_rows.extend(rows)
        label = f"{isin} {fund['name']}"
        if not ok:
            missing += 1
            print(f"{label}: SIN NAV ({'; '.join(f'{s}: {e}' for s, e in failed.items())})")
            continue
        primary_src = next(iter(ok))
        main_row = _latest(ok[primary_src])
        note = ""
        if primary_src != fund["nav"]["sources"][0]:
            first = fund["nav"]["sources"][0]
            note = f" [respaldo: falló {first}: {failed[first]}]"
        print(
            f"{label}: NAV {main_row.nav:.4f} {main_row.currency} "
            f"fecha {main_row.nav_date.isoformat()} ({primary_src}){note}"
        )
        for src, rows in ok.items():
            if src == primary_src:
                continue
            primary_by_date = {r.nav_date: r.nav for r in ok[primary_src]}
            common = sorted(primary_by_date.keys() & {r.nav_date for r in rows})
            if common:
                d = common[-1]
                other = next(r.nav for r in rows if r.nav_date == d)
                diff_pb = (other / primary_by_date[d] - 1) * 1e4
                print(
                    f"    contraste {src}: último día común {d.isoformat()}, dif {diff_pb:+.1f} pb"
                )
            else:
                last = _latest(rows)
                print(f"    contraste {src}: sin fecha común (último {last.nav_date.isoformat()})")
        for src, err in failed.items():
            if src != fund["nav"]["sources"][0] or primary_src == src:
                print(f"    {src}: no disponible ({err})")

    if all_rows and not args.no_write:
        added = upsert_csv(all_rows, out_path)
        print(f"CSV {out_path}: {added} filas nuevas")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
