from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from ...models.prospects import NoteRequest, StatusRequest
from ...services.core import load_prospects, save_prospects, crm_stats, find_pdf

router = APIRouter()

@router.get("")
def get_prospects(status: str = "", sort: str = "score"):
    prospects = load_prospects()

    filtered = [p for p in prospects if not status or p.get("status") == status]

    if sort == "score":
        filtered.sort(key=lambda x: x.get("geo_score", 0))
    elif sort == "company":
        filtered.sort(key=lambda x: x.get("company", "").lower())
    elif sort == "mrr":
        filtered.sort(key=lambda x: x.get("monthly_value", 0), reverse=True)

    stats = crm_stats(prospects)

    return {"prospects": filtered, "stats": stats}

@router.get("/{pid}")
def get_prospect_detail(pid: str):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    p["has_pdf"] = find_pdf(p) is not None
    return p

@router.post("/{pid}/note")
def add_note(pid: str, data: NoteRequest):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    text = data.text.strip()
    if text:
        if "notes" not in p:
            p["notes"] = []
        p["notes"].append(
            {
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "text": text,
            }
        )
        p["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        save_prospects(prospects)

    return p

@router.put("/{pid}/status")
def update_status(pid: str, data: StatusRequest):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    new_status = data.status.strip()
    valid_statuses = ["lead", "audit", "proposal", "active", "churned", "lost"]
    if new_status in valid_statuses:
        p["status"] = new_status
        p["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        save_prospects(prospects)

    return p

@router.get("/{pid}/pdf")
def download_pdf(pid: str):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    pdf_path = find_pdf(p)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path=pdf_path, filename=pdf_path.name, media_type="application/pdf"
    )
