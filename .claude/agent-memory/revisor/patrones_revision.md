---
name: patrones-revision
description: Patrones de error detectados en revisiones de panel-fondos (métricas de fiabilidad, workflows de Actions); revisar primero en cada diff
metadata:
  type: project
---

Patrones vistos en revisiones (fecha de primera aparición entre paréntesis):

- Métricas de puntualidad calculadas solo con la hora de arranque y asignación a slot: un retraso > slot se atribuye al slot siguiente y sale "a tiempo" (T-02, 2026-11-06). Pedir distribución de huecos entre ejecuciones consecutivas.
- Informes que mezclan ejecuciones `workflow_dispatch`/locales con las de `schedule` (T-02, 2026-11-06). Comprobar filtro por `event`.
- Marca de tiempo tomada tras el setup del job (checkout/uv sync) en vez de al inicio: infla el retraso medido (T-02, 2026-11-06).
- Bucle push/`pull --rebase` sobre un JSONL que solo se añade: un conflicto deja el rebase a medias y se pierde la línea (T-02, 2026-11-06).

**Why:** la revisión de T-02 encontró estos sesgos en la métrica de aceptación sin que los tests los cubrieran.
**How to apply:** en cualquier diff que mida fiabilidad/latencia o escriba datos desde Actions, comprobar estos cuatro puntos con una simulación rápida.
