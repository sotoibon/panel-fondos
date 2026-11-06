# Estado

- **Actualizado:** 2026-11-06 (T-04 cerrada)
- **Fase:** 1 — Datos de mercado
- **Tarea en curso:** T-02 · Prueba de Yahoo desde GitHub Actions `[~]` (esperando ≥3 días de cron)
- **Siguiente tarea:** T-07 (calendario y desfase del NAV, S; depende solo de T-05). T-06 espera a T-02; T-08 espera a T-06 y T-07.

## Última sesión
- T-04 `[x]`: `src/panel_fondos/collectors/nav.py` + `configs/nav.yaml`; fuentes iShares, Vanguard y Yahoo (Investing fuera por ToS, D-014); `funds.yaml` y `config.py` validan los bloques `nav.ishares`/`nav.vanguard`. 57 tests pasan, ruff limpio, ejecución real con red OK (contraste ≤0,1 pb). Revisor: arreglado el IMPORTANTE.
- Antes: T-05 `[x]` (D-013), T-03 `[x]` (INVESTIGACION §8, D-012).

## Abierto / bloqueos
- **T-02 criterio 2 pendiente solo de tiempo:** Actions habilitado; rama `probe-data`. Una ejecución manual (2026-11-06 16:54 UTC) dio HTTP 200 en EUNL.DE y ES=F. Aún no hay ejecuciones `schedule`. Tras ≥3 días (desde 2026-11-09): bajar `probe.jsonl` de `probe-data`, `uv run python -m panel_fondos.collectors.probe_report --input probe.jsonl` y rellenar `docs/INVESTIGACION.md` §7.
- **Push pendiente:** el remoto `main` está en `9de4559`; faltan los commits de T-03, T-05 y T-04. Push desde terminal fuera de VS Code o con `GIT_ASKPASS=` vacío (usuario `sotoibon`, token con *Contents* y *Workflows*).
- **`/replan` pendiente:** `docs/SPEC.md:11`, `:26` (Investing como fuente principal → D-014) y `:73-74` («sin confirmar», «réplica con futuros»); además el ROADMAP habla de «dudas 1-3 de SPEC §10» que son las líneas 4-5, y el Objetivo de T-04 sigue nombrando Investing.
- **Menores de T-04 sin aplicar** (lista en D-014): caché solo tras parsear, fila rara de Vanguard, divisa de la fuente, fixture de EM distinto.
- `funds.yaml`: `verified: false` en XMME.DE e IUSN.DE (T-06); `fx.hedged` del Nasdaq 100 = unknown; Vanguard Small-Cap con base USD en config pero «EUR» en su ficha (INVESTIGACION §9).
- Umbrales de precisión pendientes del primer backtest (T-10). Umbral «a tiempo» de 180 s: propuesta mía.

## Trampas descubiertas (candidatas a CLAUDE.md si se repiten)
- ES0165265002 es MyInvestor Nasdaq 100 (cartera real con ~19 % iShares Developed World y ~9 % bonos USD). iShares EM sigue MSCI EM, no el IMI.
- NAV: iShares y Vanguard T+1, Yahoo T+2 (Nasdaq 100 hasta T+3, `close: null` al final). Fecha de Yahoo = fecha local Europe/Berlin de la marca (`nav.py`, `parse_yahoo`).
- Fechas de iShares en alemán e irregulares («31.Juli2026», «31.März2026»): `nav.py` `parse_de_date`.
- Medir puntualidad de cron por slot oculta retrasos >5 min: usar también huecos (`probe_report.py`).
- WebFetch no extrae texto de PDFs: bajar el fichero y usar `pdftotext -layout`.

## Verificar el estado actual
- `uv sync && uv run pytest -q && uv run ruff check .` (esperado: 57 passed)
- `uv run python -m panel_fondos.collectors.nav --isin all --no-write` (4 ISIN con NAV y fecha, exit 0)
- `uv run python -m panel_fondos.collectors.probe` (4 precios, exit 0)
