# Panel de fondos

Panel personal (para Ibon) que estima en tiempo casi real el valor en € de 4 fondos de MyInvestor, separando dato oficial, de mercado y estimación. Especificación completa en `docs/SPEC.md`; hallazgos de la investigación en `docs/INVESTIGACION.md`.

## Estado actual
@docs/ESTADO.md

## Cómo trabajamos en este repo
- Al empezar una sesión: lee el estado de arriba y, del `docs/ROADMAP.md`, solo la sección de la tarea en curso.
- Una tarea por sesión. Al terminar: `/cierre` (actualiza ESTADO, ROADMAP y DECISIONES y hace commit).
- Si cambia el alcance o la especificación: `/replan`, nunca reescribas el roadmap a mano en mitad de una tarea.
- Decisiones nuevas → entrada en `docs/DECISIONES.md`. Experimentos y backtests → `docs/EXPERIMENTOS.md`.

## Comandos
- Instalar: `uv sync`
- Tests: `uv run pytest -q` (un fichero: `uv run pytest tests/test_x.py -q`)
- Lint/format: `uv run ruff check . --fix && uv run ruff format .`
- Recolector, backtest y panel: se añaden en sus tareas (ver ROADMAP).

## Arquitectura (lo que no se deduce leyendo el código)
- Recolector en GitHub Actions (cron) → capturas de mercado en `data/` → motor de estimación → JSON → panel estático en GitHub Pages (PWA). Sin servidor propio.
- El repo es **público**: solo datos públicos de mercado y NAV oficiales. La cartera del usuario (participaciones, aportaciones) va **solo cifrada** (AES-GCM) y se descifra en el navegador. Nunca subir un CSV de cartera en claro, ni escribir importes personales en logs, tests o commits (usar carteras ficticias).
- Estimación y NAV oficial se guardan y muestran siempre por separado (RF-04).

## Convenciones y trampas
- ES0165265002 es MyInvestor Nasdaq 100 (proxy NQ=F), no un fondo global. iShares EM sigue MSCI EM, no el IMI.
- Cada fondo tiene su propia fecha de NAV; nunca asumas una fecha común. Yahoo publica el NAV con T+2; Vanguard e Investing, con T+1.
- Yahoo no tiene API oficial: pocas peticiones por lote, caché, y tolerar nulos y 429. Datos de Xetra/LSE con 15-20 min de retraso, futuros con 10 min.
- Las cifras de error en pb de la investigación son hipótesis. No presentes una estimación como valor real. Umbrales de precisión pendientes del primer backtest.
- No cambies el protocolo de evaluación ni las métricas para mejorar un resultado sin preguntar. Semilla fija y configuración registrada en todo backtest.
- Los tests usan respuestas grabadas, no red.

## Compactación
Al compactar, conserva siempre: la tarea en curso y su criterio de aceptación, la lista de ficheros modificados y los comandos de verificación.
