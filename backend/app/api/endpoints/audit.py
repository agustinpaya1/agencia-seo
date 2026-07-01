from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
from datetime import datetime
from ...models.audit import AuditRequest
from ...services.core import load_prospects, save_prospects
from ...services.audit import mock_audit_background

router = APIRouter()

@router.post("", status_code=202)
def start_audit(data: AuditRequest, background_tasks: BackgroundTasks):
    """Starts a new GEO audit for a given URL"""
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]

    # Create a new prospect in 'audit' status
    prospects = load_prospects()
    new_id = str(uuid.uuid4())[:8]
    p = {
        "id": new_id,
        "company": domain.capitalize(),
        "domain": domain,
        "status": "audit",
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
    prospects.append(p)
    save_prospects(prospects)

    # Spawn background task
    background_tasks.add_task(mock_audit_background, new_id, domain)

    return {"message": "Audit started", "prospect": p}
