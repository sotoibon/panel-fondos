# Experimentos

Línea base: «sin cambio» (último NAV oficial) y «solo ETF proxy» — métrica principal: MAE del retorno diario frente al NAV oficial de T, en pb (E-000, pendiente de medir en T-10).

| ID | Fecha | Hipótesis | Config / commit | Métricas | vs. baseline | Conclusión |
|---|---|---|---|---|---|---|
| E-000 | pendiente | Línea base | `configs/funds.yaml` | sesgo, MAE, RMSE, cobertura 90 %, error en € | — | — |

## Notas por experimento
### E-000
- Se mide en T-10 con semilla fija y configuración registrada. Hasta entonces, las cifras en pb de `docs/INVESTIGACION.md` son hipótesis.
