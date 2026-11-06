<!-- Este fichero se REESCRIBE en cada /cierre. Máximo ~40 líneas. El histórico está en git. -->
# Estado

- **Actualizado:** 2026-11-06
- **Fase:** 0 — Andamiaje
- **Tarea en curso:** —
- **Siguiente tarea:** T-01 · Entorno y estructura del proyecto

## Última sesión
- Arranque: investigación de viabilidad (fondos, fuentes de datos, métodos de estimación), entrevista y propuesta aprobada. Memoria del proyecto escrita. No hay código todavía.

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
- `uv run pytest -q` (cuando exista T-01)
