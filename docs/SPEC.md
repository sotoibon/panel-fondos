# Especificación — Panel de fondos

> Consolidada a partir de `docs/fuentes/SPEC_ORIGINAL.md`, la entrevista inicial y la investigación de viabilidad (`docs/INVESTIGACION.md`). Los cambios posteriores se registran en el changelog al final.

## 1. Objetivo
Herramienta personal e independiente de MyInvestor para seguir el valor en euros de una cartera de 4 fondos de inversión lo más cerca posible del tiempo real, con la mayor granularidad que permitan los datos gratuitos. Debe separar de forma inequívoca tres tipos de dato: **oficial** (valor liquidativo publicado), **mercado** (cotizaciones de ETFs, futuros y divisas) y **estimación** (calculada por la herramienta).

Fondos (ISIN → qué son realmente):
- IE000ZYRH0Q7 · iShares Developed World Index (IE) S Acc EUR · MSCI World NR EUR.
- IE000QAZP7L2 · iShares Emerging Markets Index (IE) S Acc EUR · MSCI EM NR EUR (no IMI).
- ES0165265002 · MyInvestor Nasdaq 100 FI (Andbank) · Nasdaq-100 NTR EUR, réplica con futuros. Cobertura de divisa sin confirmar.
- IE00B42W4L06 · Vanguard Global Small-Cap Index EUR Acc · MSCI World Small Cap.

## 2. Entregables
- Recolector de datos programado en la nube (funciona con el PC apagado).
- Motor de estimación intradía por fondo y de cartera, con bandas de error.
- Panel web estático, instalable como PWA en el móvil.
- Backtest que mide el error de la estimación frente al NAV oficial.
- Documentación en `docs/` (español).

## 3. Usuarios y casos de uso
Un único usuario (Ibon). Consulta habitual, a veces solo semanal, desde el móvil o el PC, **sin lanzar nada ni hacer pasos complejos**: abrir un enlace y ver. Aporta dinero mensualmente a los 4 fondos.

## 4. Datos
- **Mercado intradía:** Yahoo Finance (no oficial) vía `yfinance` o endpoint chart: ETFs proxy en Xetra/Ámsterdam/LSE (retraso 15-20 min), futuros ES=F/NQ=F (10 min, sesión nocturna), divisas `EURUSD=X` etc. (tiempo real). Gratuito, sin cuota publicada, con 429 esporádicos.
- **NAV oficial:** descarga del histórico de Vanguard (IE00B42W4L06) e Investing.com (resto) como fuente principal; Yahoo `0P…F` como relleno y contraste. Frankfurter (BCE) como respaldo diario de FX.
- **Cartera del usuario:** CSV con una fila por aportación (fecha, ISIN, importe €, participaciones). Se guarda **cifrado** en el repo y se descifra en el navegador con una contraseña. Nunca en claro.
- **Licencia y ToS:** uso personal y no comercial. Yahoo e Investing tienen ToS restrictivos para scraping: peticiones mínimas y con caché.
- **Almacenamiento:** capturas en ficheros del repo (rama de datos) o equivalente; solo datos públicos de mercado, nunca posiciones del usuario.

## 5. Requisitos funcionales
- RF-01 Mostrar por fondo y total: valor en €, ganancia en € y %, a lo largo del día y en histórico.
- RF-02 Cada cifra lleva etiqueta OFICIAL / MERCADO / ESTIMACIÓN, con fecha/hora del dato y antigüedad.
- RF-03 La estimación se muestra como rango (banda empírica), nunca como cifra única; con distinto color que el dato oficial.
- RF-04 La estimación y el NAV oficial nunca comparten columna o tabla; al publicarse el NAV oficial se registra el error.
- RF-05 Calcular patrimonio real desde aportaciones: participaciones por fondo, coste total, rentabilidad en € y %.
- RF-06 Calendario por fondo: mercados relevantes, festivos, desfase de publicación del NAV (fecha del NAV propia de cada fondo).
- RF-07 Estimación definida como: NAV_oficial(T-1) × Π regiones [1 + retorno desde el cierre de cada región] × ajuste FX desde el fixing; para el Nasdaq 100 el proxy es NQ=F.
- RF-08 Degradar u ocultar la estimación si faltan datos clave (proxy sin precio reciente, NAV demasiado antiguo).
- RF-09 Recolector periódico (cada ~5 min en horario de mercado) ejecutado en la nube.
- RF-10 Panel instalable en móvil (PWA), accesible por enlace, que descifra la cartera en el cliente.

## 6. Requisitos no funcionales
- **Disponibilidad:** el recolector no depende del PC del usuario.
- **Privacidad:** posiciones y aportaciones solo cifradas en el repo; ninguna en logs ni en datos públicos.
- **Coste:** 0 €/mes.
- **Reproducibilidad:** semilla fija y configuración registrada en cualquier calibración; `uv` con lockfile.
- **Hardware:** CPU local en WSL2; sin GPU.
- **Robustez:** tolerar nulos, 429 y huecos de datos sin romper el panel.

## 7. Métricas de éxito y línea base
- Error de la estimación respecto al NAV oficial del día T, en pb y en € sobre la cartera: sesgo, MAE, RMSE y cobertura de la banda del 90 %, por fondo y por hora del día (snapshots a 09:30, 11:00, 15:00, 17:30, 22:00 CET).
- **Líneas base:** (a) «sin cambio» (último NAV oficial); (b) solo ETF proxy sin ajuste.
- Umbrales numéricos: **pendientes de fijar** tras el primer backtest con datos reales. Las cifras de la investigación (World 10-30 pb, EM 30-70 pb, Small Cap 20-50 pb) son razonamiento propio, no estudios.
- No se cambia el protocolo de evaluación ni las métricas para mejorar un resultado sin consultar al usuario.

## 8. Restricciones
- Solo datos gratuitos. Stack: Python con `uv`, `pytest`, `ruff`.
- Repo público; sin datos personales en claro.
- Plazo: sin fecha de entrega. Se construye por tareas pequeñas.

## 9. Fuera de alcance
- Operar o conectarse a MyInvestor, e importar sus ficheros automáticamente.
- Datos de pago o tiempo real europeo de pago.
- Reconstrucción por holdings × precios (inviable para un particular).
- Valoración fiscal y alertas.
- Despliegue con autenticación de servidor.

## 10. Riesgos y preguntas abiertas
- Yahoo sin API oficial: bloqueos, nulos, ToS ambiguo. Yahoo podría bloquear las IP de GitHub Actions (por verificar en T-02).
- Fiabilidad del cron de GitHub Actions y sus límites (por verificar en T-02). Plan B: Cloudflare Workers o VM gratuita.
- Sin histórico intradía gratuito: hay que acumular semanas de capturas antes de calibrar.
- Cobertura de divisa del Nasdaq 100 sin confirmar (T-03).
- Horas de corte y valuation point de iShares EM, de iShares World (swing y fair value) y del Nasdaq 100 sin confirmar (T-03).
- Frecuencia de publicación de holdings (iShares IE y Vanguard) sin confirmar.
- Base USD o EUR del fondo Vanguard sin resolver.
- Varianza irreducible por la mañana: no se conoce la sesión de EE. UU. (cálculo propio ≈ 40-50 pb de desviación típica en World).
- Contraseña del CSV cifrado: si se pierde, no hay recuperación.

## Changelog
- 2026-11-06 — versión inicial.
