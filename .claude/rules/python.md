---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Python
- Type hints en funciones públicas; `pathlib` para rutas; nada de rutas absolutas personales.
- Configuración por fichero (`configs/*.yaml`) o argumentos, no constantes enterradas en el código.
- Cada módulo nuevo en `src/` lleva su test en `tests/` con el mismo nombre (`test_<módulo>.py`).
- Logs con `logging`, no `print`, fuera de scripts de exploración.
