# Panel de fondos

Panel personal que estima en tiempo casi real el valor en € de 4 fondos de MyInvestor,
separando dato oficial, de mercado y estimación. Especificación en `docs/SPEC.md`.

## Uso

- Instalar: `uv sync`
- Tests: `uv run pytest -q`
- Lint/format: `uv run ruff check . --fix && uv run ruff format .`

> El repo es público: nunca subir la cartera en claro (solo cifrada).

## Sonda de Yahoo (T-02)

- Una pasada: `uv run python -m panel_fondos.collectors.probe` (config en `configs/probe.yaml`; `--out f.jsonl` añade una línea).
- Informe de fiabilidad: `uv run python -m panel_fondos.collectors.probe_report --input probe.jsonl [--since 2026-11-07T00:00]`.
- En GitHub, `.github/workflows/probe.yml` corre cada 5 min y guarda `probe.jsonl` en la rama `probe-data`.
