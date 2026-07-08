# Agencia SEO — CRM GEO-SEO con motor de auditoría determinista

Monorepo del CRM de la agencia: un backend FastAPI con un **motor de auditoría
determinista** (cero LLM en el cálculo de ningún score) y un frontend Next.js
con el tablero de clientes potenciales, la vista de proyectos y el detalle de
cada lead con el progreso de su auditoría.

```
backend/app/            # API FastAPI
├── api/endpoints/      #   /api/audit, /api/leads
├── audit_engine/       #   motor determinista (ver docs/motor-auditoria-determinista.md)
├── models/             #   contratos pydantic (leads, auditoría)
└── services/           #   persistencia Mongo + runner de auditorías en background
frontend/               # Next.js 16 (App Router, Tailwind v4)
├── src/app/            #   rutas: /, /tablero, /proyectos, /leads/[id], ...
└── src/features/       #   leads (tablero, detalle, timeline), ui (primitivas)
tests/
├── backend/            # pytest — espejo de backend/app
└── frontend/           # vitest — espejo de frontend/src
docs/                   # diseño del motor y metodología de scoring
schema/                 # plantillas JSON-LD de referencia
```

## Comandos

Todo pasa por el Makefile (fuente de verdad del toolchain):

```bash
make install   # deps Python + Chromium (Playwright) + deps JS (raíz y frontend)
make test      # pytest (tests/backend) + vitest (tests/frontend)
make lint      # ruff check
make format    # ruff --fix + ruff format
make run       # servidor FastAPI en modo dev (puerto 8000)
```

El frontend se levanta con `npm --prefix frontend run dev` (puerto 3000) y
espera el backend en `http://127.0.0.1:8000` (configurable vía
`NEXT_PUBLIC_API_URL`).

## Requisitos

- Python 3.14 + Poetry
- Node.js (el frontend fija su config en `next.config.mjs` — no convertir a `.ts`)
- MongoDB en `mongodb://localhost:27017` (configurable vía `MONGODB_URI`;
  base de datos `agencia_seo_dev` vía `MONGODB_DB`)

## Datos en runtime

- **MongoDB** — colecciones `leads`, `audit_runs`, `audit_reports_*` y
  `performance_snapshots` (snapshots <48h de Core Web Vitals).
- **`~/.geo-leads/proposals/`** — PDFs de propuesta pre-generados, uno por
  dominio; el endpoint `/api/leads/{id}/pdf` solo los sirve, no los genera.

## Principio rector del motor

Ningún número del informe sale de un LLM: cada score se explica con una fórmula
o un checklist (pesos, umbrales de Core Web Vitals, validaciones JSON-LD…).
Antes de tocar `backend/app/audit_engine/`, leer
`docs/motor-auditoria-determinista.md`. Las instrucciones para agentes están en
`AGENTS.md` / `CLAUDE.md`.
