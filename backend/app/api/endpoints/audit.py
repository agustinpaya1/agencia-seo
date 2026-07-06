from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from ...dependencies import get_db, get_leads_collection
from ...models.audit import AuditRequest
from ...models.leads import STATUS_IN_PROGRESS
from ...services.audit import run_audit_background

router = APIRouter()


@router.post(
    "",
    status_code=202,
    operation_id="start_audit",
    summary="Inicia una auditoría GEO para una URL",
    description=(
        "Crea el lead con status `audit` y lanza la auditoría determinista como "
        "BackgroundTask del propio proceso (si el proceso se reinicia a mitad, la "
        "auditoría se pierde y el lead queda atascado en `audit`; se desbloquea a "
        "mano con PUT /api/leads/{lead_id}/status). Responde 202 inmediatamente "
        'con `{"message", "lead"}`; el resultado llega después al documento del '
        "lead (geo_score, tier, is_lead, last_audit_id). 409 si ya hay una "
        "auditoría en curso para ese dominio (garantizado por el índice único "
        "parcial sobre domain+status='audit'); 400 si la URL viene vacía. "
        "Estructura de respuesta provisional."
    ),
)
async def start_audit(
    data: AuditRequest,
    background_tasks: BackgroundTasks,
    leads=Depends(get_leads_collection),
    db=Depends(get_db),
):
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]

    # Fast-path guard: one audit in flight per domain. Not atomic on its own
    # (check-then-insert races) — the unique partial index on leads
    # (domain, status="audit"; see ensure_indexes) is the real defense, caught
    # as DuplicateKeyError on the insert below. A crashed process can leave a
    # lead stuck in "audit" (services/audit.py known debt);
    # PUT /leads/{lead_id}/status unblocks it manually.
    ongoing = await leads.find_one({"domain": domain, "status": STATUS_IN_PROGRESS})
    if ongoing is not None:
        raise HTTPException(status_code=409, detail=f"Ya hay una auditoría en curso para {domain}")

    lead = {
        "company": domain.capitalize(),
        "domain": domain,
        "status": STATUS_IN_PROGRESS,
        "geo_score": 0,
        "monthly_value": 0,
        "audit_date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "notes": [
            {
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "text": "Auditoría iniciada automáticamente.",
            }
        ],
    }

    try:
        result = await leads.insert_one(lead)
    except DuplicateKeyError:
        # Lost the race: another request inserted the in-flight lead between
        # our find_one and this insert.
        raise HTTPException(status_code=409, detail=f"Ya hay una auditoría en curso para {domain}")
    inserted_id = result.inserted_id

    # Spawn background task
    background_tasks.add_task(run_audit_background, inserted_id, domain, db)

    lead["id"] = str(inserted_id)
    lead.pop("_id", None)

    return {"message": "Audit started", "lead": lead}
