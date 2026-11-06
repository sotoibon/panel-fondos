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
