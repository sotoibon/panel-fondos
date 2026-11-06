# Registro de decisiones

Una entrada por decisión. No se borran: si una decisión se revierte, se añade otra que la sustituye.

## D-001 · Solo datos gratuitos — 2026-11-06
- **Contexto:** hay proveedores de pago (~25-30 €/mes) pero no está confirmado que cubran Xetra ni los ETFs UCITS.
- **Opciones:** A) solo gratis; B) gratis y pagar si el backtest lo justifica; C) pagar desde el principio.
- **Decisión:** A, solo gratis (Yahoo, Investing, Vanguard, Frankfurter).
- **Consecuencias:** retraso de 10-20 min en los ETFs y futuros, y dependencia de fuentes no oficiales. Se puede revisar si el backtest muestra mucho error.

## D-002 · Cartera en fichero propio, sin conexión con MyInvestor — 2026-11-06
- **Contexto:** hacen falta aportaciones y participaciones para calcular el patrimonio real.
- **Opciones:** A) fichero que edita el usuario; B) importar un export de MyInvestor; C) solo saldo actual.
- **Decisión:** A, un CSV con fecha, ISIN, importe y participaciones por aportación.
- **Consecuencias:** entrada manual mensual. La importación automática queda fuera de alcance.

## D-003 · Panel web estático, PWA, sin lanzar nada — 2026-11-06
- **Contexto:** el usuario consulta a veces solo semanalmente y desde el móvil; no quiere ejecutar comandos.
- **Opciones:** A) panel local en localhost; B) notebook de Colab; C) panel web desplegado.
- **Decisión:** un panel web estático desplegado en GitHub Pages, instalable como PWA.
- **Consecuencias:** la privacidad pasa a depender del cifrado (D-005). Requiere un recolector en la nube (D-004).

## D-004 · Recolector en la nube con GitHub Actions — 2026-11-06
- **Contexto:** el PC del usuario no está siempre encendido y se quiere recolectar de forma robusta.
- **Opciones:** A) proceso local en WSL2; B) GitHub Actions con cron; C) Cloudflare Workers o una VM gratuita.
- **Decisión:** B por defecto; C como plan B si T-02 detecta bloqueos de Yahoo o cron poco fiable.
- **Consecuencias:** el cron de GitHub no garantiza puntualidad y sus límites no están verificados. T-02 lo mide antes de construir encima.

## D-005 · Repo público con CSV de cartera cifrado — 2026-11-06
- **Contexto:** un repo público da minutos de Actions ilimitados, pero las posiciones son datos personales.
- **Opciones:** A) repo público con CSV cifrado y descifrado en el navegador; B) repo privado, con riesgo de quedarse sin minutos gratuitos.
- **Decisión:** A, aprobada por el usuario. Cifrado AES-GCM con clave derivada de una contraseña.
- **Consecuencias:** nunca se sube la cartera en claro; perder la contraseña no tiene recuperación. El servidor solo guarda datos públicos de mercado y valores por participación.

## D-006 · Estimación separada del dato oficial, con rangos — 2026-11-06
- **Contexto:** el usuario exige no confundir estimaciones con valores reales.
- **Opciones:** A) cifra única; B) rango empírico con etiquetas y colores distintos.
- **Decisión:** B. Etiquetas OFICIAL / MERCADO / ESTIMACIÓN, antigüedad de cada dato, bandas de error, y nunca la estimación en la misma tabla que el NAV oficial.
- **Consecuencias:** hace falta un backtest (T-10) para calibrar las bandas antes de mostrarlas como definitivas.

## D-007 · Método de estimación: proxies por región con futuros y FX — 2026-11-06
- **Contexto:** los fondos valoran con cierres asíncronos; reconstruir por holdings es inviable.
- **Opciones:** A) ETF equivalente; B) holdings × precios; C) futuros e índices más FX; D) regresión por factores.
- **Decisión:** C como base (NQ=F para el Nasdaq 100; ES=F, ETFs y FX para el resto), con A como contraste y D a valorar tras el backtest. B descartada.
- **Consecuencias:** la sesión de EE. UU. es incognoscible por la mañana: error irreducible que se mostrará como banda.

## D-008 · Stack: Python con uv, pytest y ruff — 2026-11-06
- **Contexto:** estándar de las instrucciones globales; no hay GPU ni entrenamiento.
- **Opciones:** estándar del usuario, o alternativas.
- **Decisión:** Python con `uv`, `pytest`, `ruff`; `pandas` y `pyyaml` para datos; panel en HTML/JS estático.
- **Consecuencias:** sin framework de servidor. El panel consume un JSON generado por el recolector.

## D-009 · Métrica principal y líneas base — 2026-11-06
- **Contexto:** hay que medir cuánto se equivoca la estimación.
- **Opciones:** MAE, RMSE, sesgo, cobertura de bandas.
- **Decisión:** MAE, RMSE, sesgo y cobertura de la banda del 90 % por fondo y hora, más error en €. Líneas base: «sin cambio» y «solo ETF proxy». Umbrales pendientes del primer backtest.
- **Consecuencias:** no se cambia el protocolo ni las métricas sin consultar al usuario.

## D-010 · Layout src/ con hatchling y ruff ampliado — 2026-11-06
- **Contexto:** T-01 necesitaba estructura instalable para que los tests importen `panel_fondos`.
- **Opciones:** paquete en la raíz o layout `src/`; setuptools o hatchling; ruff con reglas por defecto o ampliadas.
- **Decisión:** layout `src/panel_fondos/` con build backend `hatchling`, dev-deps en `[dependency-groups]`, Python >=3.11, ruff con `E,F,I,UP,B` y línea 100.
- **Consecuencias:** `uv sync` instala el paquete en editable; `data/` y `web/` existen con `.gitkeep`.

## D-011 · Sonda T-02: endpoint chart, rama probe-data y métrica «a tiempo» — 2026-11-06
- **Contexto:** T-02 debe medir bloqueos de Yahoo y puntualidad del cron de Actions durante varios días.
- **Opciones:** `yfinance` o endpoint `v8/finance/chart` con `requests`; guardar en main, en rama aparte o en artefactos; definir «a tiempo» por slot.
- **Decisión:** endpoint chart con `requests` (una petición por símbolo, 429/nulos registrados sin excepción, un reintento); resultados JSONL en la rama `probe-data` (elegido por el usuario); cada ejecución se asigna al slot de 5 min que contiene su arranque, «a tiempo» = arranque ≤ 180 s del slot (configurable), y un slot sin ejecución cuenta como perdido (un retraso mayor que el slot deja el original vacío).
- **Consecuencias:** el umbral de 180 s es propuesta mía, no del usuario: se informan también p50/p90/máx para poder cambiarlo sin re-medir. En local el endpoint respondió 200 sin cookie ni crumb; desde IP de Actions está por medir.
- **Ajustes tras revisión:** solo cuentan para la puntualidad las ejecuciones con `event == schedule`; se usa la hora de inicio del job (`PROBE_JOB_START`, antes de checkout/uv sync) y se informan los huecos entre ejecuciones consecutivas, porque la asignación por slot oculta retrasos >5 min. Limitaciones aceptadas por ahora: conflicto en `pull --rebase` podría perder una línea, y si la sonda casca antes de escribir no queda registro (se vería como slot perdido).

## D-012 · T-03: criterio de «resuelta» y tratamiento de lo no publicado — 2026-11-06
- **Contexto:** el folleto BISF no contiene «swing pricing» y el del Nasdaq 100 no publica valuation point ni hora de publicación del VL; la cobertura de divisa del Nasdaq 100 no está declarada expresamente.
- **Decisión:** una duda se da por resuelta si tiene cita (documento y página) o se marca «no publicado» tras buscar. Cobertura del Nasdaq 100 = «no sistemática, sin cobertura declarada» apoyada en folleto p.1 y en el informe semestral (pp. 6 y 12); swing pricing BISF = «no publicado» (0 apariciones en 602 pp.; antidilución vía «Duties and Charges»).
- **Consecuencias:** el proxy NQ=F necesita EURUSD hasta que el backtest (T-10) demuestre otra cosa. El valuation point del Nasdaq 100 es hipótesis a validar. SPEC.md (líneas 11, 73-74) sigue diciendo «sin confirmar»: actualizar en un `/replan`, no a mano.


## D-013 · T-05: esquema de `funds.yaml` y validación manual — 2026-11-06
- **Contexto:** hacía falta una configuración por fondo validable, sin dependencias nuevas y honesta con lo no verificado.
- **Decisión:** `configs/funds.yaml` + `src/panel_fondos/config.py` con validador manual que acumula todos los errores (descartado pydantic/jsonschema: dependencia extra para 4 fondos). ISIN con dígito de control. Cada proxy lleva `verified` (true solo si T-02 lo capturó: EUNL.DE, ES=F, NQ=F, EURUSD=X; XMME.DE e IUSN.DE son plausibles, `false`). `fx.hedged` admite `unknown` (Nasdaq 100, D-012). `valuation_point: null` si no está publicado. Proxies por región granular (Europa/Asia) y pesos quedan para T-08; aquí solo los proxies documentados en INVESTIGACION §1.
- **Consecuencias:** T-06 debe leer símbolos de este fichero y comprobar los `verified: false`. Las exposiciones FX son de la investigación, no de holdings.

## D-014 · T-04: fuentes de NAV oficial; Investing.com descartado — 2026-11-06
- **Contexto:** el ROADMAP/SPEC daban Vanguard e Investing.com como fuentes principales del NAV.
- **Opciones:** raspar Investing (cargaba sin Cloudflare); solo Yahoo; fuentes oficiales de cada gestora + Yahoo de contraste.
- **Decisión:** Investing.com **fuera**: sus condiciones prohíben usar o almacenar sus datos sin permiso escrito y lo ejecutaríamos con cron desde un repo público. Principal: fichero SpreadsheetML oficial de iShares (World y EM, T+1, 6 decimales) y tabla HTML de la ficha de Vanguard (T+1, ~10 días). Yahoo `0P…F` como contraste y como única fuente del Nasdaq 100 (la gestora no publica nada consultable; T+2/T+3). Orden de prioridad = orden de `nav.sources` en `funds.yaml`; si la principal falla, se cae a la siguiente. Parámetros (URLs, reintentos, caché 6 h) en `configs/nav.yaml`. CSV largo con clave (isin, source, nav_date), idempotente y con escritura atómica.
- **Consecuencias:** contraste real 2026-11-06: iShares y Vanguard vs Yahoo, −0,1 / −0,1 / +0,0 pb en el último día común. Los NAV del Nasdaq 100 llegan hasta 3 días tarde. `ISHARES_AJAX_ID` y el HTML de Vanguard pueden cambiar: falla con error claro y queda Yahoo. SPEC.md:26 está desfasada (`/replan`).
- **Pendiente de la revisión (menores, no aplicados):** no se cachea solo tras parsear OK (una página de consentimiento se serviría 6 h); una fila rara de Vanguard descarta toda la fuente; la divisa viene de la config, no se contrasta con la de la fuente; el test de iShares usa el mismo fixture para World y EM.
