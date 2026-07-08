from pathlib import Path

# Pre-generated proposal PDFs live outside the repo, one file per lead domain.
PROPOSALS_DIR = Path.home() / ".geo-leads" / "proposals"


def init_dirs():
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)


init_dirs()


def score_tier(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 60:
        return "moderate"
    if score >= 40:
        return "poor"
    return "critical"


def crm_stats(leads: list[dict]) -> dict:
    total = len(leads)
    active = [lead for lead in leads if lead.get("status") == "active"]
    proposals = [lead for lead in leads if lead.get("status") == "proposal"]
    mrr = sum(lead.get("monthly_value", 0) for lead in active)
    pipeline = sum(lead.get("monthly_value", 0) for lead in proposals)
    avg_score = round(sum(lead.get("geo_score", 0) for lead in leads) / total) if total else 0
    return {
        "total": total,
        "active": len(active),
        "mrr": mrr,
        "pipeline": pipeline,
        "avg_score": avg_score,
        "avg_tier": score_tier(avg_score),
    }


def find_pdf(lead: dict) -> Path | None:
    domain = lead.get("domain", "")
    for f in sorted(PROPOSALS_DIR.glob(f"{domain}*.pdf"), reverse=True):
        return f
    return None
