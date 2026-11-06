# Estado

- **Actualizado:** 2026-11-06
- **Fase:** 0 — Andamiaje (completa)
- **Tarea en curso:** —
- **Siguiente tarea:** T-02 · Prueba de Yahoo desde GitHub Actions (Fase 1)

## Última sesión
- T-01 hecha: `pyproject.toml` (uv, hatchling), `src/panel_fondos/{collectors,estimation,portfolio}`, `tests/`, `configs/`, `web/`, `data/`, README mínimo. `uv run pytest -q` → 1 passed; `uv run ruff check .` limpio.

## Abierto / bloqueos
- El usuario debe crear un repo público en GitHub antes de T-02 (pasos al llegar a esa tarea).
- Dudas sin resolver (T-03): cobertura de divisa del Nasdaq 100; cortes y valuation point de iShares EM; swing y fair value de iShares World.
- Umbrales de precisión pendientes del primer backtest (T-10).

## Trampas descubiertas (candidatas a CLAUDE.md si se repiten)
- ES0165265002 es MyInvestor Nasdaq 100, no un fondo global.
- iShares EM sigue MSCI EM, no el IMI; no confundir con sus ETFs proxy.
- Yahoo tarda T+2 en publicar el NAV de fondos; Vanguard e Investing, T+1.
- Cifras de precisión en pb de `docs/INVESTIGACION.md` son razonamiento propio, no estudios.

## Verificar el estado actual
- `uv sync && uv run pytest -q && uv run ruff check .`
