"""Carga y validación de ``configs/funds.yaml``.

Validación manual (sin dependencias nuevas): acumula todos los errores y lanza un
``ConfigError`` con la lista completa, indicando el fondo y el campo.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "configs" / "funds.yaml"

PROXY_KINDS = {"etf", "future", "fx", "index"}
PROXY_ROLES = {"primary", "contrast"}
NAV_SOURCES = {"vanguard", "investing", "yahoo"}
HEDGED_VALUES = {True, False, "unknown"}
CLOSE_REGIONS = {"asia", "europe", "us"}
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")


class ConfigError(ValueError):
    """La configuración de fondos no es válida."""


def isin_checksum_ok(isin: str) -> bool:
    """Comprueba el dígito de control (Luhn sobre letras convertidas a números)."""
    if not _ISIN.match(isin):
        return False
    digits = "".join(str(int(c, 36)) for c in isin)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            n = n - 9 if n > 9 else n
        total += n
    return total % 10 == 0


def _validate_fund(f: Any, where: str, errors: list[str]) -> None:
    if not isinstance(f, dict):
        errors.append(f"{where}: debe ser un mapa")
        return
    isin = f.get("isin")
    if not isinstance(isin, str) or not isin_checksum_ok(isin):
        errors.append(f"{where}.isin: ISIN inválido ({isin!r})")
    where = isin if isinstance(isin, str) else where

    for key in ("name", "index", "base_currency", "share_currency"):
        if not isinstance(f.get(key), str) or not f[key].strip():
            errors.append(f"{where}.{key}: obligatorio, texto no vacío")

    fx = f.get("fx")
    if not isinstance(fx, dict):
        errors.append(f"{where}.fx: obligatorio (mapa)")
    else:
        exp = fx.get("exposure")
        if not isinstance(exp, list) or not exp or not all(isinstance(c, str) for c in exp):
            errors.append(f"{where}.fx.exposure: lista no vacía de divisas")
        if fx.get("hedged") not in HEDGED_VALUES:
            errors.append(f"{where}.fx.hedged: debe ser true, false o 'unknown'")

    proxies = f.get("proxies")
    if not isinstance(proxies, list) or not proxies:
        errors.append(f"{where}.proxies: lista no vacía")
    else:
        for i, p in enumerate(proxies):
            pw = f"{where}.proxies[{i}]"
            if not isinstance(p, dict):
                errors.append(f"{pw}: debe ser un mapa")
                continue
            for key in ("region", "symbol"):
                if not isinstance(p.get(key), str) or not p[key]:
                    errors.append(f"{pw}.{key}: obligatorio")
            if p.get("kind") not in PROXY_KINDS:
                errors.append(f"{pw}.kind: debe ser uno de {sorted(PROXY_KINDS)}")
            if p.get("role") not in PROXY_ROLES:
                errors.append(f"{pw}.role: debe ser uno de {sorted(PROXY_ROLES)}")
            d = p.get("delay_min")
            if not isinstance(d, int) or isinstance(d, bool) or d < 0:
                errors.append(f"{pw}.delay_min: entero >= 0")
            if not isinstance(p.get("verified"), bool):
                errors.append(f"{pw}.verified: booleano")

    markets = f.get("markets")
    if not isinstance(markets, list) or not markets or not all(isinstance(m, str) for m in markets):
        errors.append(f"{where}.markets: lista no vacía de códigos MIC")

    closes = f.get("closes")
    if not isinstance(closes, dict) or not closes:
        errors.append(f"{where}.closes: mapa no vacío")
    else:
        for region, hhmm in closes.items():
            if region not in CLOSE_REGIONS:
                errors.append(f"{where}.closes.{region}: región desconocida")
            if not isinstance(hhmm, str) or not _HHMM.match(hhmm):
                errors.append(f"{where}.closes.{region}: hora 'HH:MM' esperada ({hhmm!r})")

    dealing = f.get("dealing")
    if not isinstance(dealing, dict):
        errors.append(f"{where}.dealing: obligatorio (mapa)")
    else:
        cut = dealing.get("cutoff_local")
        if not isinstance(cut, str) or not _HHMM.match(cut):
            errors.append(f"{where}.dealing.cutoff_local: hora 'HH:MM' esperada ({cut!r})")
        tz = dealing.get("cutoff_tz")
        try:
            ZoneInfo(tz)  # type: ignore[arg-type]
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            errors.append(f"{where}.dealing.cutoff_tz: zona horaria inválida ({tz!r})")
        off = dealing.get("cutoff_offset_bd")
        if not isinstance(off, int) or isinstance(off, bool) or off > 0:
            errors.append(f"{where}.dealing.cutoff_offset_bd: entero <= 0 (días hábiles)")
        if not isinstance(dealing.get("published"), bool):
            errors.append(f"{where}.dealing.published: booleano")
        if "valuation_point" not in dealing:
            errors.append(f"{where}.dealing.valuation_point: obligatorio (puede ser null)")

    nav = f.get("nav")
    if not isinstance(nav, dict):
        errors.append(f"{where}.nav: obligatorio (mapa)")
    else:
        lag = nav.get("lag_business_days")
        if not isinstance(lag, int) or isinstance(lag, bool) or lag < 0:
            errors.append(f"{where}.nav.lag_business_days: entero >= 0")
        src = nav.get("sources")
        if not isinstance(src, list) or not src or not set(src) <= NAV_SOURCES:
            errors.append(f"{where}.nav.sources: lista no vacía de {sorted(NAV_SOURCES)}")
        if not isinstance(nav.get("yahoo_symbol"), str):
            errors.append(f"{where}.nav.yahoo_symbol: obligatorio")


def validate(data: Any) -> list[dict]:
    """Valida el contenido ya parseado y devuelve la lista de fondos."""
    errors: list[str] = []
    funds = data.get("funds") if isinstance(data, dict) else None
    if not isinstance(funds, list) or not funds:
        raise ConfigError("'funds' debe ser una lista no vacía")
    for i, f in enumerate(funds):
        _validate_fund(f, f"funds[{i}]", errors)
    isins = [f.get("isin") for f in funds if isinstance(f, dict)]
    for isin in {x for x in isins if isins.count(x) > 1}:
        errors.append(f"{isin}: ISIN duplicado")
    if errors:
        raise ConfigError("\n".join(errors))
    return funds


def load_funds(path: Path | str = DEFAULT_PATH) -> dict[str, dict]:
    """Carga y valida el YAML; devuelve ``{isin: fondo}``."""
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return {f["isin"]: f for f in validate(data)}
