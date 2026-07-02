@AGENTS.md
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