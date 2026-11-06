# Estado

- **Actualizado:** 2026-11-06
- **Fase:** 1 — Datos de mercado
- **Tarea en curso:** T-02 · Prueba de Yahoo desde GitHub Actions `[~]`
- **Siguiente tarea:** terminar T-02 (esperar datos de Actions); mientras tanto T-03 no depende de ella.

## Última sesión
- T-02 implementada en local: `src/panel_fondos/collectors/{probe,probe_report}.py`, `configs/probe.yaml`, `.github/workflows/probe.yml`, tests y fixtures grabados. Revisada por `revisor`; corregidos sesgos de la métrica (filtro `schedule`, inicio de job, huecos). `uv run pytest -q` → 17 passed; ruff limpio; sonda local → 4/4 precios no nulos (criterio 1 cumplido).

## Abierto / bloqueos
- **T-02 criterio 2 sin cumplir:** repo público `sotoibon/panel-fondos` creado y código subido (push desde terminal fuera de VS Code o con `GIT_ASKPASS=` vacío, usuario `sotoibon` y token con *Contents* y *Workflows*: la sesión de VS Code usa otra cuenta, IbonLanit). Falta confirmar en GitHub: Actions habilitado, *Workflow permissions* en lectura y escritura, `probe` lanzado a mano y rama `probe-data` creada. Tras ≥3 días: `uv run python -m panel_fondos.collectors.probe_report --input probe.jsonl` (bajar el fichero de `probe-data`) y rellenar `docs/INVESTIGACION.md` §7.
- Sin probar en Actions: el workflow solo está validado sintácticamente (sin `actionlint`).
- Limitaciones conocidas del workflow (D-011): conflicto de rebase puede perder una línea; si la sonda casca antes de escribir no hay registro.
- Dudas sin resolver (T-03): cobertura de divisa del Nasdaq 100; cortes y valuation point de iShares EM; swing y fair value de iShares World.
- Umbrales de precisión pendientes del primer backtest (T-10). El umbral «a tiempo» de 180 s es propuesta mía, sin confirmar.

## Trampas descubiertas (candidatas a CLAUDE.md si se repiten)
- ES0165265002 es MyInvestor Nasdaq 100, no un fondo global.
- iShares EM sigue MSCI EM, no el IMI; no confundir con sus ETFs proxy.
- Yahoo tarda T+2 en publicar el NAV de fondos; Vanguard e Investing, T+1.
- Cifras de precisión en pb de `docs/INVESTIGACION.md` son razonamiento propio, no estudios.
- Yahoo `v8/finance/chart` respondió 200 en local sin cookie ni crumb; desde IP de Actions no medido.
- Medir puntualidad de cron por slot oculta retrasos >5 min: usar también huecos (`probe_report.py`).

## Verificar el estado actual
- `uv sync && uv run pytest -q && uv run ruff check .`
- `uv run python -m panel_fondos.collectors.probe` (4 precios, exit 0)
