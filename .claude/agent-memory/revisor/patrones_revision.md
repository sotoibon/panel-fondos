---
name: patrones-revision
description: Patrones de error detectados en revisiones de panel-fondos (métricas de fiabilidad, workflows de Actions, extracción de datos de folletos PDF); revisar primero en cada diff
metadata:
  type: project
---

Patrones vistos en revisiones (fecha de primera aparición entre paréntesis):

- Métricas de puntualidad calculadas solo con la hora de arranque y asignación a slot: un retraso > slot se atribuye al slot siguiente y sale "a tiempo" (T-02, 2026-11-06). Pedir distribución de huecos entre ejecuciones consecutivas.
- Informes que mezclan ejecuciones `workflow_dispatch`/locales con las de `schedule` (T-02, 2026-11-06). Comprobar filtro por `event`.
- Marca de tiempo tomada tras el setup del job (checkout/uv sync) en vez de al inicio: infla el retraso medido (T-02, 2026-11-06).
- Bucle push/`pull --rebase` sobre un JSONL que solo se añade: un conflicto deja el rebase a medias y se pierde la línea (T-02, 2026-11-06).

- Tareas de documentación: un punto queda «parcial / no leído» cuando un `pdftotext | grep` del PDF entero lo resuelve (T-03: «swing» tiene 0 apariciones en el folleto BISF). Hacer siempre la búsqueda de texto completo.
- Etiquetas de fuente: se marca [F] un documento que no está en la lista de páginas comprobadas, y se cita «apartado» sin página (T-03, 2026-11-06).
- Resúmenes de definiciones que omiten la cláusula operativa (p. ej. «si el mercado cierra, se usa el valor del día anterior») que es justo la que necesita el motor (T-03).

- Colectores: el `except` del orquestador solo captura la excepción propia del parser, pero `date()`/`float()`/`fromtimestamp` lanzan ValueError/TypeError y tumban todos los fondos (T-04, 2026-11-06). Simular fecha imposible y timestamp nulo.
- Caché que guarda toda respuesta 200 antes de validar el parseo: una página de consentimiento o error queda servida durante el TTL (T-04).
- Un mismo fixture servido para dos entidades (dos fondos iShares) en el test: no detecta IDs cruzados en la config (T-04).
- Docstrings/código citan una decisión D-0xx que aún no existe en DECISIONES.md, y SPEC/ROADMAP siguen nombrando la fuente descartada (T-04).

**Why:** la revisión de T-02 encontró estos sesgos en la métrica de aceptación sin que los tests los cubrieran.
**How to apply:** en cualquier diff que mida fiabilidad/latencia o escriba datos desde Actions, comprobar estos cuatro puntos con una simulación rápida.
