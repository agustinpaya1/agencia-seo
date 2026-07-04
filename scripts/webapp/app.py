import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="GEO-SEO CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CRM_PATH = Path.home() / ".geo-prospects" / "prospects.json"
PROPOSALS_DIR = Path.home() / ".geo-prospects" / "proposals"
AUDITS_DIR = Path.home() / ".geo-prospects" / "audits"

# ── Models ─────────────────────────────────────────────────────────────


class NoteRequest(BaseModel):
    text: str


class StatusRequest(BaseModel):
    status: str


class AuditRequest(BaseModel):
    url: str


# ── Helpers ────────────────────────────────────────────────────────────


def init_dirs():
    CRM_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    if not CRM_PATH.exists():
        with open(CRM_PATH, "w") as f:
            json.dump([], f)


init_dirs()


def load_prospects() -> list[dict]:
    if not CRM_PATH.exists():
        return []
    with open(CRM_PATH) as f:
        return json.load(f)


def save_prospects(prospects: list[dict]):
    with open(CRM_PATH, "w") as f:
        json.dump(prospects, f, indent=2, ensure_ascii=False)


def score_tier(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 60:
        return "moderate"
    if score >= 40:
        return "poor"
    return "critical"


def crm_stats(prospects: list[dict]) -> dict:
    total = len(prospects)
    active = [p for p in prospects if p.get("status") == "active"]
    proposals = [p for p in prospects if p.get("status") == "proposal"]
    mrr = sum(p.get("monthly_value", 0) for p in active)
    pipeline = sum(p.get("monthly_value", 0) for p in proposals)
    avg_score = round(sum(p.get("geo_score", 0) for p in prospects) / total) if total else 0
    return {
        "total": total,
        "active": len(active),
        "mrr": mrr,
        "pipeline": pipeline,
        "avg_score": avg_score,
        "avg_tier": score_tier(avg_score),
    }


def find_pdf(prospect: dict) -> Path | None:
    domain = prospect.get("domain", "")
    for f in sorted(PROPOSALS_DIR.glob(f"{domain}*.pdf"), reverse=True):
        return f
    return None


# ── API Routes ─────────────────────────────────────────────────────────


@app.get("/api/prospects")
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


@app.get("/api/prospects/{pid}")
def get_prospect_detail(pid: str):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    p["has_pdf"] = find_pdf(p) is not None
    return p


@app.post("/api/prospects/{pid}/note")
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


@app.put("/api/prospects/{pid}/status")
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


@app.get("/api/prospects/{pid}/pdf")
def download_pdf(pid: str):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    pdf_path = find_pdf(p)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(path=pdf_path, filename=pdf_path.name, media_type="application/pdf")


def mock_audit_background(pid: str, domain: str):
    import time

    time.sleep(5)  # Simulate work
    ps = load_prospects()
    target = next((x for x in ps if x.get("id") == pid), None)
    if target:
        target["geo_score"] = 45  # mock result
        target["status"] = "proposal"

        # Create a dummy PDF to avoid 404s in the UI
        dummy_pdf_path = PROPOSALS_DIR / f"{domain}_{pid}.pdf"
        dummy_pdf_path.write_text("Dummy PDF content for testing")

        save_prospects(ps)


@app.post("/api/audit", status_code=202)
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


if __name__ == "__main__":
    import os

    import uvicorn

    debug = os.environ.get("DEBUG", "false").lower() == "true"
    uvicorn.run("app:app", host="127.0.0.1", port=5050, reload=debug)
