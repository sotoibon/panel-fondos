# Investigación de viabilidad (2026-11-06)

Resultado de tres investigaciones previas al desarrollo. Leyenda: **[F]** respaldado por fuente leída · **[R]** razonamiento propio, sin estudio · **[?]** no confirmado. Las cifras en pb son [R] y deben validarse con el backtest (T-10).

## 1. Los fondos
| ISIN | Fondo | Índice | Proxy intradía | Notas |
|---|---|---|---|---|
| IE000ZYRH0Q7 | iShares Developed World Index (IE) S Acc EUR, BlackRock, TER 0,06 % | MSCI World NR EUR, 1.251 valores | iShares Core MSCI World IE00B4L5Y983 (EUNL Xetra, IWDA Ámsterdam); futuros ES=F; ICE MSCI World NTR (ESI) | Clase sin cobertura. Mínimo 200 M EUR: MyInvestor accede por canal agregado [?] |
| IE000QAZP7L2 | iShares Emerging Markets Index (IE) S Acc EUR, TER 0,16 % | MSCI EM NR EUR (no IMI) | Xtrackers MSCI EM 1C IE00BTJRMP35 (XMME Xetra); EEM [?] | Divisas EM; el ETF iShares Core EM IMI es otro índice |
| ES0165265002 | MyInvestor Nasdaq 100 FI, Andbank, CNMV 5540, TER ~0,36-0,40 % | Nasdaq-100 NTR EUR | NQ=F; ETFs Nasdaq con cobertura EUR (EQEU IE00BYVTMS52, HNDX LU1681038599) | Réplica con futuros. **Cobertura de divisa [?]** (T-03) |
| IE00B42W4L06 | Vanguard Global Small-Cap Index EUR Acc, TER 0,29 % | MSCI World Small Cap, 3.899 valores | iShares MSCI World Small Cap IE00BF4RFH31 (IUSN Xetra) | Sin futuros líquidos; combinar RTY y Europa/Japón |

Tickers Yahoo de NAV: IE00B42W4L06 → 0P0000XR9M.F · IE000ZYRH0Q7 → 0P0001XF40.F · IE000QAZP7L2 → 0P0001XF3Z.F · ES0165265002 → 0P0001MRGW.F [F, verificado con chart].

Exposición por país (30-sep-2026): World EE. UU. 72,9 %, Japón 5,9 %, UK 3,4 %. Small Cap EE. UU. 61 %, Japón 13 %. EM Taiwán 28,9 %, Corea 21,4 %, China 19,8 %, India 10,7 %.

## 2. Mecánica del NAV
- **BlackRock (BISF):** Valuation Point = cierre del último mercado relevante. NAV disponible el día hábil siguiente (T+1). Hora de corte del World 14:30 Irlanda [F, prospecto Singapur]. EM, swing y fair value: [?]. El precio de suscripción suma «Duties and Charges» [F].
- **Vanguard:** Valuation Point = cierre de cada mercado principal. Corte 16:00 Irlanda del día hábil anterior; liquidación T+2. Swing pricing discrecional y fair value posible con aprobación del depositario [F, prospecto pp. 144-148, 380-382]. Cierre anticipado si un mercado con ≥25 % cierra antes.
- **Nasdaq 100 (Andbank):** cortes y publicación [?]. Rankia mostraba el 06-nov el último VL con fecha 02-nov: guardar la fecha del NAV por fondo, nunca asumir una común.
- Documentos: prospecto BISF https://www.blackrock.com/es/particulares/literature/prospectus/blackrock-index-selection-fund-prospectus-en.pdf · prospecto Vanguard https://fund-docs.vanguard.com/prospectus-en.pdf · informe semestral Nasdaq 100 https://www.inversis.com/fondos/contenidos/inf_semestral/ES0165265002_inf_semestral_es_ES.pdf

## 3. Fuentes de datos
**NAV oficial:** Vanguard web (T+1, descarga de histórico) y Investing.com (T+1, ToS restrictivo) son las mejores. Yahoo `0P…F` llega a T+2 y con nulos. mstarpy 11 exige Selenium con Chrome con ventana (frágil en WSL2). CNMV solo publica XML mensual. FT no es consultable. Cbonds iba atrasado.

**Intradía [F, verificado con WebFetch]:** Yahoo da 1m para EUNL.DE, VWCE.DE, IWDA.L, ES=F, EURUSD=X, ^GSPC. Retardos oficiales: Xetra/Frankfurt/Stuttgart/Ámsterdam/París 15 min, LSE 20 min, SIX 30 min, futuros CME 10 min; divisas `=X` e índices S&P/Nasdaq/Dow en tiempo real. Sin cuota publicada y con 429 esporádicos. `yfinance` 1.8.0 (3-nov-2026) activo.

**Otras:** Twelve Data gratis (solo US, forex y cripto, 800 créditos/día). Tiingo gratis (1.000/día, cobertura no-US poco clara). EODHD gratis inútil; intradía desde 24,99 €/mes (Xetra y UCITS sin confirmar). Alpha Vantage 25/día. Stooq exige apikey con captcha. Tradegate y L&S sin feed oficial gratuito. IBKR da tiempo real con cuenta (tarifas no verificadas). Frankfurter (BCE) es FX diario, útil como respaldo.

**Futuros:** ES=F y NQ=F, con sesión nocturna, son el mejor proxy gratuito. FESX y MSCI sin fuente gratuita fiable.

## 4. Método de estimación
- **Fórmula de partida [R]:** V_est(t) = NAV(T-1) × Π regiones [1 + r_región(cierre de su región en T-1 → t)] × (1 + r_FX(fixing 16:00 Londres de T-1 → spot t)). Cierres: Asia ~08:00 CET, Europa 17:30, EE. UU. 22:00.
- **Respaldo [F]:** el iNAV de STOXX/Deutsche Börse admite variantes por futuros, por índice y multi-zona horaria; el cálculo es NAV(T-1)/Index(T-1) × Index(t) × FX (https://www.stoxx.com/documents/stoxxnet/Documents/Indices/Common/Indexguide/iNAV_Guide.pdf). Boudoukh et al. (FAJ 2002) muestran que los NAV con precios obsoletos son predecibles con la sesión posterior de EE. UU.
- **Métodos descartados o secundarios:** holdings × precios, 2-5 pb pero inviable para un particular. ETF equivalente, 10-30 pb, sirve de contraste. Regresión por factores regionales, útil para estimar pesos y bandas (D-007).
- **Error irreducible [R]:** por la mañana, la sesión de EE. UU. es desconocida: ≈ peso EE. UU. (0,6-0,7) × volatilidad de la sesión (~0,7 %) ≈ 40-50 pb de desviación típica en World ≈ 45 € por cada 10.000 €.
- **FX [R]:** usar spot_now / fixing 16:00 Londres de T-1, no el spot de las 22:00; la diferencia es ~10-15 pb en una cartera con ~65 % en USD. Para el Nasdaq 100 con cobertura el FX es casi irrelevante (carry ~1 pb/día).
- **Precisión esperada [R] del retorno «equivalente ahora»:** World 10-30 pb, EM 30-70 pb, Small Cap 20-50 pb. Tracking difference diaria de un fondo indexado: 0,1-0,5 pb. Saltos de hasta 10-15 pb en días ex-dividendo con ETF de distribución.
- **Backtest [R]:** capturas a 09:30, 11:00, 15:00, 17:30 y 22:00 CET; comparar con el NAV de T; métricas sesgo, MAE, RMSE, cobertura de banda y error en €. Banda total de cartera con σ = sqrt(wᵀΣw), no sumando bandas.
- **Calendario:** si una región está cerrada, su retorno es 0. Si el fondo no valora hoy, la estimación no se actualiza. Developed World no valora si Londres, Irlanda o Nueva York están cerrados. Ojo a los desfases de horario de verano entre EE. UU. y Europa (marzo y octubre/noviembre).

## 5. Presentación
Etiqueta ESTIMACIÓN con fecha/hora y fórmula, color distinto del dato oficial y, al lado, «Último VL oficial a [fecha]». Mostrar rango («≈ 12.340 € (12.250-12.430)»), antigüedad de cada dato, y degradar u ocultar la estimación si faltan datos. Nunca la estimación en la misma tabla que el NAV oficial.

## 6. Dudas abiertas
1. Cobertura de divisa del Nasdaq 100 (T-03). 2. Corte, valuation point, swing y fair value de iShares EM; swing y fair value de iShares World (T-03). 3. Cortes y publicación de NAV de MyInvestor/Andbank, y cortes propios de MyInvestor. 4. Frecuencia de holdings de iShares IE y Vanguard. 5. Tickers EUR de IEEM/IQQE y de ETFs no verificados (EEM, QQQ, CNDX). 6. Base USD o EUR del fondo Vanguard. 7. Límites y fiabilidad del cron de GitHub Actions, y bloqueo de Yahoo desde sus IP (T-02).
