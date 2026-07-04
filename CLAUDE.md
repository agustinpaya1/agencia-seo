@AGENTS.md

## Comandos: usa siempre los targets del Makefile

Por defecto, usa `make install` / `make test` / `make lint` / `make format` /
`make run` en vez de invocar `poetry`, `pytest`, `ruff`, etc. sueltos — el
Makefile es la fuente de verdad del toolchain (ver `pyproject.toml`).

Si necesitas algo que el Makefile no cubre todavía:
- Si es evidente que hace falta como target permanente (p. ej. un paso de
  setup que cualquiera que clone el repo también necesitará), añádelo tú
  mismo al Makefile en vez de dejarlo como comando suelto en el cierre.
- Si es dudoso o puntual, no toques el Makefile: dilo en el bloque "Qué debo
  revisar yo" del cierre y pregunta antes de añadirlo.

## Convención de tests: espejo del árbol del paquete

Los tests reflejan la estructura del paquete: `backend/app/<pkg>/<mod>.py` se
prueba en `tests/<pkg>/test_<mod>.py` (p. ej. `backend/app/audit_engine/
schema_org.py` → `tests/audit_engine/test_schema_org.py`). El `pythonpath` de
`pyproject.toml` ya hace importable `backend.app...` desde `tests/`.

Al añadir un módulo nuevo, crea su test espejo en la ruta equivalente en vez de
agrupar pruebas de varios módulos en un mismo archivo. Para submódulos con la
forma pura/async (ver AGENTS.md), cubre las dos capas: la función pura con
fixtures y sin red, y el shell async mockeando la I/O (red/Playwright/CLI).

## Al terminar cualquier tarea, cierra siempre con tres bloques

1. **Arquitectura y decisiones** — qué construiste, cómo se conecta con lo que
   ya existía, y qué decisiones tomaste que no estaban explícitas en el prompt
   (con el motivo).
2. **Qué debo revisar yo** — archivos/líneas concretas donde poner atención,
   no "revisa todo". Prioriza donde tomaste una decisión discutible.
3. **Verificación manual** — comandos exactos para comprobarlo yo mismo. Si
   aplica, cómo levantar el servidor y qué endpoint/escenario probar. Si la
   tarea todavía no se puede verificar end-to-end (ej. un submódulo aislado
   sin enganchar a ningún endpoint todavía), dilo explícitamente en vez de
   inventar un paso que no aplica.