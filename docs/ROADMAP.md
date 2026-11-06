# Roadmap — Panel de fondos

Leyenda: `[ ]` pendiente · `[~]` en curso · `[x]` hecha · `[-]` descartada. Tamaño: S / M / L.
Cada tarea cabe en una sesión y tiene un criterio verificable con un comando.

## Fase 0 — Andamiaje
### T-01 · Entorno y estructura del proyecto `[x]` · S
- Objetivo: `uv` con dependencias base (`pandas`, `requests`, `pyyaml`, `pytest`, `ruff`), `src/panel_fondos/{collectors,estimation,portfolio}`, `tests/`, `configs/`, `web/`, `.gitignore`, README mínimo.
- Aceptación: `uv run pytest -q` pasa con un test trivial y `uv run ruff check .` sin errores.
- Depende de: —
- Agentes sugeridos: implementador → verificador

## Fase 1 — Viabilidad (resolver incógnitas antes de construir)
### T-02 · Prueba de Yahoo desde GitHub Actions `[ ]` · M
- Objetivo: workflow mínimo con cron cada 5 min que pide 1 lote (EUNL.DE, ES=F, NQ=F, EURUSD=X) y guarda el resultado. Medir bloqueos, nulos y puntualidad del cron durante varios días. Si falla, documentar y proponer plan B (Cloudflare Workers o VM gratuita).
- Aceptación: `uv run python -m panel_fondos.collectors.probe` devuelve precios no nulos para los 4 símbolos en local; informe de fiabilidad del cron en `docs/INVESTIGACION.md` con % de ejecuciones a tiempo.
- Depende de: T-01
- Agentes sugeridos: implementador → investigador
- Notas: el repo es público y no puede contener posiciones del usuario. Requiere que el usuario cree el repo en GitHub.

### T-03 · Folletos y KIID: cobertura, cortes y valuation point `[ ]` · M
- Objetivo: leer el KID/folleto actual del Nasdaq 100 (cobertura de divisa, hora de corte, publicación del NAV) y el Apéndice V del folleto BISF (EM y World: corte, valuation point, swing, fair value). Guardar los datos en `docs/INVESTIGACION.md` con fuente y página.
- Aceptación: cada una de las dudas 1-3 de la sección 10 de SPEC queda marcada como resuelta con cita (documento y página) o como «no publicado».
- Depende de: T-01
- Agentes sugeridos: investigador

### T-04 · Descarga del NAV oficial de los 4 fondos `[ ]` · M
- Objetivo: módulo que obtiene el histórico de NAV oficial (Vanguard, Investing.com, Yahoo `0P…F` como contraste), con fecha propia de cada NAV, y lo normaliza a un CSV.
- Aceptación: `uv run pytest tests/test_nav.py -q` pasa con respuestas grabadas; `uv run python -m panel_fondos.collectors.nav --isin all` imprime el último NAV y su fecha para los 4 ISIN.
- Depende de: T-01
- Agentes sugeridos: investigador → implementador → verificador
- Notas: respetar ToS: pocas peticiones y caché. Si Investing bloquea, usar solo Yahoo y Vanguard.

## Fase 2 — Datos
### T-05 · `funds.yaml`: proxies, divisas y calendarios `[ ]` · S
- Objetivo: `configs/funds.yaml` con por fondo: ISIN, índice, proxies por región y tramo horario, exposición FX, mercados relevantes, hora de cierre y desfase de publicación; validación con esquema.
- Aceptación: `uv run pytest tests/test_config.py -q` valida los 4 fondos y falla con un fondo mal formado.
- Depende de: T-03
- Agentes sugeridos: implementador → verificador

### T-06 · Recolector intradía con almacenamiento `[ ]` · M
- Objetivo: captura periódica de precios de proxies, futuros y FX con marca temporal, ordenada por día en `data/`; idempotente y tolerante a nulos y 429.
- Aceptación: `uv run pytest tests/test_collector.py -q` pasa con respuestas grabadas; `uv run python -m panel_fondos.collectors.snapshot` añade una fila por símbolo sin duplicar si se ejecuta dos veces en el mismo minuto.
- Depende de: T-02, T-05
- Agentes sugeridos: implementador → verificador

### T-07 · Calendario y desfase del NAV `[ ]` · S
- Objetivo: función que, dado un fondo y un instante, indica qué fecha de NAV es la última publicada, si hoy hay valoración y qué regiones están abiertas o de festivo.
- Aceptación: `uv run pytest tests/test_calendar.py -q` pasa con casos de festivos (p. ej. 25-dic, Acción de Gracias) y cambio de hora.
- Depende de: T-05
- Agentes sugeridos: implementador → verificador

## Fase 3 — Motor de estimación
### T-08 · Estimador de un fondo (Nasdaq 100) `[ ]` · M
- Objetivo: valor estimado por participación = NAV(T-1) × variación de NQ=F desde el cierre anterior, con degradación si faltan datos. Salida separada del NAV oficial.
- Aceptación: `uv run pytest tests/test_estimator.py -q` pasa, incluido un caso con dato obsoleto que devuelve «sin estimación».
- Depende de: T-04, T-06, T-07
- Agentes sugeridos: implementador → verificador

### T-09 · Estimador de los 4 fondos con FX y futuros `[ ]` · L
- Objetivo: estimación por regiones (Asia, Europa, EE. UU.) con ES=F, ETFs proxy y ajuste FX desde el fixing de Londres, para World, EM y Small Cap, más la agregación a cartera.
- Aceptación: `uv run pytest tests/test_estimator_multi.py -q` pasa; con datos grabados de un día, el estimador devuelve un valor por fondo y un total.
- Depende de: T-08
- Agentes sugeridos: implementador → verificador → revisor
- Notas: si pasa de una sesión, dividir por fondo.

### T-10 · Backtest y bandas de error `[ ]` · M
- Objetivo: comparar estimación frente a NAV oficial por fondo y hora; calcular sesgo, MAE, RMSE, cobertura de la banda del 90 % y error en €; comparar con las dos líneas base. Registrar en `docs/EXPERIMENTOS.md`.
- Aceptación: `uv run python -m panel_fondos.estimation.backtest --seed 0` genera la tabla de métricas y la anota en EXPERIMENTOS.md. Los umbrales de aceptación se fijan con el usuario tras el primer resultado.
- Depende de: T-09 y al menos 2-3 semanas de capturas acumuladas
- Agentes sugeridos: experimentador → revisor
- Notas: no cambiar el protocolo ni las métricas sin consultar.

## Fase 4 — Cartera del usuario
### T-11 · Modelo de aportaciones y participaciones `[ ]` · M
- Objetivo: leer el CSV (fecha, ISIN, importe €, participaciones) y calcular participaciones, coste y rentabilidad en € y % por fondo y total, con valoración a NAV oficial y a estimación.
- Aceptación: `uv run pytest tests/test_portfolio.py -q` pasa con una cartera de ejemplo ficticia y casos de varias aportaciones al mismo fondo.
- Depende de: T-01
- Agentes sugeridos: implementador → verificador

### T-12 · CSV cifrado y descifrado en el navegador `[ ]` · M
- Objetivo: script que cifra el CSV con una contraseña (AES-GCM con clave derivada por PBKDF2/scrypt) y fragmento JavaScript que lo descifra en el cliente. Documentar que perder la contraseña no tiene recuperación.
- Aceptación: `uv run pytest tests/test_crypto.py -q` pasa; un CSV cifrado por Python se descifra correctamente por el JS en una prueba, y con contraseña errónea falla.
- Depende de: T-11
- Agentes sugeridos: implementador → revisor

## Fase 5 — Panel
### T-13 · Panel: total y por fondo `[ ]` · L
- Objetivo: página estática con gráfico intradía, valor en €, ganancia en € y %, etiquetas OFICIAL / MERCADO / ESTIMACIÓN, bandas de error y antigüedad de cada dato.
- Aceptación: `uv run pytest tests/test_web_data.py -q` valida el JSON que consume el panel; captura de pantalla revisada con el usuario con datos de ejemplo.
- Depende de: T-09, T-11, T-12
- Agentes sugeridos: implementador → verificador
- Notas: usar la habilidad dataviz. Si pasa de una sesión, dividir entre total y detalle por fondo.

### T-14 · PWA para móvil `[ ]` · S
- Objetivo: manifiesto, icono y service worker mínimos para instalar el panel en el móvil y abrirlo con un toque.
- Aceptación: auditoría de Lighthouse de PWA aprobada, o instalación verificada en el móvil por el usuario.
- Depende de: T-13
- Agentes sugeridos: implementador

### T-15 · Despliegue y automatización `[ ]` · M
- Objetivo: workflow de GitHub Actions que recolecta, regenera el JSON y publica en GitHub Pages; documentar el alta del repo y la contraseña.
- Aceptación: tras un push a `main`, la URL de Pages muestra datos con una antigüedad menor de 15 min en horario de mercado.
- Depende de: T-13, T-14
- Agentes sugeridos: implementador → verificador
