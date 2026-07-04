# Agencia SEO — agent instructions

GEO-SEO CRM: FastAPI backend (`backend/app`) + Next.js frontend (`frontend/`).
The deterministic audit engine lives in `backend/app/audit_engine/` — its
design and casuística are documented in
`docs/motor-auditoria-determinista.md`; read it before touching that package.

## Commands

Use the Makefile targets, not loose `poetry`/`pytest`/`ruff` invocations:

```
make install   # dependencies (Python + any project-level JS deps)
make test      # pytest
make lint      # ruff check
make format    # ruff check --fix (imports) + ruff format
make run       # fastapi dev server
```

## Conventions

- No LLM anywhere in the audit engine's scoring path — every number must
  trace back to a formula or a checklist (see docs/motor-auditoria-determinista.md,
  principio 0).
- Submodules in `audit_engine/` split pure/sync scoring from async I/O
  shells (see `schema_org.py` and `technical.py` for the established shape).
