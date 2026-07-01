import json
from pathlib import Path

CRM_PATH = Path.home() / ".geo-prospects" / "prospects.json"
PROPOSALS_DIR = Path.home() / ".geo-prospects" / "proposals"
AUDITS_DIR = Path.home() / ".geo-prospects" / "audits"

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
    avg_score = (
        round(sum(p.get("geo_score", 0) for p in prospects) / total) if total else 0
    )
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
