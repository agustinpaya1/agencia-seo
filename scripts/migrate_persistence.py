#!/usr/bin/env python
"""One-pass dev migration to the split persistence schema (2026-07).

* ``prospects``  -> ``leads`` (straight copy, ``_id`` preserved).
* ``audits``     -> ``audit_runs`` + one doc per category in the
  ``audit_reports_*`` collections, via the same pure builder production uses
  (``audit_run_documents``). The legacy ``_id`` is preserved as the run ``_id``
  so every ``leads.last_audit_id`` keeps pointing at a real document; the raw
  ``fetch.html``/``headers``/``robots_txt`` are dropped on the way (they were
  the corte-A debt).

Deliberately NOT a production migrator: one pass, no retries, aborts if any
target collection already has documents, and it does NOT drop the legacy
collections — it prints the mongosh commands for when you have validated the
result. Indexes are not created here either: ``ensure_indexes`` runs in the
app lifespan, so the next ``make run`` creates them.

Run with the backend stopped:

    poetry run python scripts/migrate_persistence.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import backend.app.*
load_dotenv()

from backend.app.audit_engine.models import AuditResult  # noqa: E402
from backend.app.services.persistence import (  # noqa: E402
    AUDIT_RUNS_COLLECTION,
    CATEGORY_COLLECTIONS,
    audit_run_documents,
    leads_collection_name,
)

LEGACY_AUDITS = "audits"


def main() -> int:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = MongoClient(uri)
    db = client[os.getenv("MONGODB_DB", "agencia_seo_dev")]

    legacy_leads = os.getenv("MONGODB_COLLECTION", "prospects")  # the old env var, on purpose
    leads_name = leads_collection_name()
    targets = [leads_name, AUDIT_RUNS_COLLECTION, *CATEGORY_COLLECTIONS.values()]

    # Idempotence guard: one pass means one pass.
    dirty = [name for name in targets if db[name].count_documents({}) > 0]
    if dirty:
        print(f"ABORT: colecciones destino no vacías: {', '.join(dirty)}")
        print("Vacíalas (o renómbralas) si de verdad quieres re-ejecutar la migración.")
        return 1

    # 1. prospects -> leads, _id preserved.
    prospects = list(db[legacy_leads].find())
    if prospects:
        db[leads_name].insert_many(prospects)
    print(f"{legacy_leads} -> {leads_name}: {len(prospects)} documentos")

    # 2. audits -> audit_runs + audit_reports_*, run _id preserved.
    audits = list(db[LEGACY_AUDITS].find())
    per_category: dict[str, int] = dict.fromkeys(CATEGORY_COLLECTIONS, 0)
    for doc in audits:
        old_id = doc.pop("_id")
        lead_id = doc.pop("prospect_id", None)  # may be missing in the oldest audits
        result = AuditResult.model_validate(doc)  # coerces enums + naive BSON dates
        run_doc, category_docs = audit_run_documents(result, lead_id=lead_id, run_id=old_id)
        for name, cat_doc in category_docs.items():  # categories first, run last
            db[CATEGORY_COLLECTIONS[name]].insert_one(cat_doc)
            per_category[name] += 1
        db[AUDIT_RUNS_COLLECTION].insert_one(run_doc)
    print(f"{LEGACY_AUDITS} -> {AUDIT_RUNS_COLLECTION}: {len(audits)} runs")
    for name, count in per_category.items():
        print(f"  {CATEGORY_COLLECTIONS[name]}: {count} documentos")

    # 3. Integrated verification.
    problems: list[str] = []
    if db[leads_name].count_documents({}) != db[legacy_leads].count_documents({}):
        problems.append(f"counts de {leads_name} y {legacy_leads} no cuadran")
    if db[AUDIT_RUNS_COLLECTION].count_documents({}) != db[LEGACY_AUDITS].count_documents({}):
        problems.append(f"counts de {AUDIT_RUNS_COLLECTION} y {LEGACY_AUDITS} no cuadran")
    for run in db[AUDIT_RUNS_COLLECTION].find():
        for key in ("html", "headers", "robots_txt"):
            if key in run.get("fetch", {}):
                problems.append(f"run {run['_id']}: fetch.{key} no debería haberse persistido")
        for name, ref in run.get("reports", {}).items():
            found = db[CATEGORY_COLLECTIONS[name]].find_one({"_id": ref["id"]})
            if found is None:
                problems.append(f"run {run['_id']}: reports.{name}.id apunta a un doc inexistente")
            elif found["audit_id"] != run["_id"]:
                problems.append(f"run {run['_id']}: audit_id de reports.{name} no cuadra")
    for name, collection_name in CATEGORY_COLLECTIONS.items():
        expected = db[AUDIT_RUNS_COLLECTION].count_documents({f"reports.{name}": {"$exists": True}})
        if db[collection_name].count_documents({}) != expected:
            problems.append(f"{collection_name}: count != runs que referencian '{name}'")

    if problems:
        print("\nVERIFICACIÓN FALLIDA:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nVerificación OK. Las colecciones viejas quedan intactas; cuando valides:")
    print(f"  mongosh> use {db.name}")
    print(f"  mongosh> db.{LEGACY_AUDITS}.drop()")
    print(f"  mongosh> db.{legacy_leads}.drop()")
    print("Arranca el backend (make run) para que ensure_indexes cree los índices nuevos.")
    print("Ojo: la env var MONGODB_COLLECTION ya no se lee; la nueva es MONGODB_LEADS_COLLECTION.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
