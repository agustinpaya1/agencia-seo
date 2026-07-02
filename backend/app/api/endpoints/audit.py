from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
import uuid
from datetime import datetime
from ...models.audit import AuditRequest
from ...dependencies import get_prospects_collection
from ...services.audit import mock_audit_background

router = APIRouter()

@router.post("", status_code=202)
async def start_audit(data: AuditRequest, background_tasks: BackgroundTasks, collection = Depends(get_prospects_collection)):
    """Starts a new GEO audit for a given URL"""
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]

    p = {
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
    
    result = await collection.insert_one(p)
    inserted_id = result.inserted_id

    # Spawn background task
    background_tasks.add_task(mock_audit_background, inserted_id, domain, collection)

    p["id"] = str(inserted_id)
    p.pop("_id", None)

    return {"message": "Audit started", "prospect": p}
