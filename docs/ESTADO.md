# Estado

- **Actualizado:** 2026-11-06
- **Fase:** 1 — Datos de mercado
- **Tarea en curso:** T-02 · Prueba de Yahoo desde GitHub Actions `[~]` (esperando ≥3 días de cron)
- **Siguiente tarea:** T-04 (NAV oficial) o T-05 (`funds.yaml`, ya desbloqueada por T-03). T-06 espera a T-02 y T-05.

## Última sesión
- T-03 `[x]`: `docs/INVESTIGACION.md` §8 con corte, valuation point, cobertura, swing y fair value por fondo, con página. Revisada por `revisor`; corregidos swing («no publicado») y citas. Decisión D-012. Sin cambios de código.

## Abierto / bloqueos
- **T-02 criterio 2 pendiente solo de tiempo:** Actions habilitado y con escritura; rama `probe-data` creada. Una ejecución manual (2026-11-06 16:54 UTC, `workflow_dispatch`) dio HTTP 200 y precio en EUNL.DE y ES=F (el registro estaba truncado y no se vieron NQ=F ni EURUSD=X). Aún no hay ejecuciones `schedule`, que son las que cuenta la puntualidad. Tras ≥3 días (a partir del 2026-11-09): bajar `probe.jsonl` de `probe-data` y `uv run python -m panel_fondos.collectors.probe_report --input probe.jsonl`, y rellenar `docs/INVESTIGACION.md` §7.
- **Push pendiente:** el remoto `main` está en `9de4559`; faltan `6dc433c` y los commits de T-03. Push desde terminal fuera de VS Code o con `GIT_ASKPASS=` vacío (usuario `sotoibon`, token con *Contents* y *Workflows*).
- Limitaciones del workflow (D-011).
- **SPEC desfasada:** `docs/SPEC.md:11` y `:73-74` aún dicen «sin confirmar» (T-03) y «réplica con futuros» (el fondo mezcla ETFs, swaps y futuros). Actualizar con `/replan`. Además, el ROADMAP habla de «dudas 1-3 de SPEC §10» pero allí son las líneas 4-5.
- Residual de T-03: significado del índice «NDXERNRH» del KID, KID de iShares World, cortes propios de MyInvestor (no publicado; mirar área privada).
- Umbrales de precisión pendientes del primer backtest (T-10). Umbral «a tiempo» de 180 s: propuesta mía.

## Trampas descubiertas (candidatas a CLAUDE.md si se repiten)
- ES0165265002 es MyInvestor Nasdaq 100, no un fondo global; su cartera real (informe semestral p.12) incluye ~19 % iShares Developed World y ~9 % bonos USD, no solo Nasdaq.
- iShares EM sigue MSCI EM, no el IMI. Cortes BISF: EM 13:30, World 14:30 (Irlanda) en DD-1BD; precio = cierre del DD (`INVESTIGACION.md` §8).
- Yahoo tarda T+2 en publicar el NAV; Vanguard e Investing, T+1.
- Cifras de precisión en pb de `docs/INVESTIGACION.md` son razonamiento propio.
- Medir puntualidad de cron por slot oculta retrasos >5 min: usar también huecos (`probe_report.py`).
- WebFetch no extrae texto de PDFs: bajar el fichero y usar `pdftotext -layout`.

## Verificar el estado actual
- `uv sync && uv run pytest -q && uv run ruff check .` (esperado: 17 passed)
- `uv run python -m panel_fondos.collectors.probe` (4 precios, exit 0)
