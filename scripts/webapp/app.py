#!/usr/bin/env python3
"""
GEO-SEO CRM — REST API (Flask)
Usage:
    pip install flask flask-cors
    python app.py
    API will run on http://localhost:5050
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import threading

from flask import Flask, request, send_file, abort, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Next.js

CRM_PATH = Path.home() / ".geo-prospects" / "prospects.json"
PROPOSALS_DIR = Path.home() / ".geo-prospects" / "proposals"
AUDITS_DIR = Path.home() / ".geo-prospects" / "audits"

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
    if score >= 80: return "good"
    if score >= 60: return "moderate"
    if score >= 40: return "poor"
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

@app.route("/api/prospects", methods=["GET"])
def get_prospects():
    prospects = load_prospects()
    status_filter = request.args.get("status", "")
    sort = request.args.get("sort", "score")

    filtered = [p for p in prospects if not status_filter or p.get("status") == status_filter]

    if sort == "score":
        filtered.sort(key=lambda x: x.get("geo_score", 0))
    elif sort == "company":
        filtered.sort(key=lambda x: x.get("company", "").lower())
    elif sort == "mrr":
        filtered.sort(key=lambda x: x.get("monthly_value", 0), reverse=True)

    stats = crm_stats(prospects)
    
    return jsonify({
        "prospects": filtered,
        "stats": stats
    })

@app.route("/api/prospects/<pid>", methods=["GET"])
def get_prospect_detail(pid):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        abort(404)

    p["has_pdf"] = find_pdf(p) is not None
    return jsonify(p)

@app.route("/api/prospects/<pid>/note", methods=["POST"])
def add_note(pid):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        abort(404)

    data = request.json
    text = data.get("text", "").strip() if data else ""
    if text:
        if "notes" not in p:
            p["notes"] = []
        p["notes"].append({
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "text": text,
        })
        p["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        save_prospects(prospects)

    return jsonify(p)

@app.route("/api/prospects/<pid>/status", methods=["PUT"])
def update_status(pid):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        abort(404)

    data = request.json
    new_status = data.get("status", "").strip() if data else ""
    valid_statuses = ["lead", "audit", "proposal", "active", "churned", "lost"]
    if new_status in valid_statuses:
        p["status"] = new_status
        p["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        save_prospects(prospects)

    return jsonify(p)

@app.route("/api/prospects/<pid>/pdf", methods=["GET"])
def download_pdf(pid):
    prospects = load_prospects()
    p = next((x for x in prospects if x.get("id") == pid), None)
    if not p:
        abort(404)

    pdf_path = find_pdf(p)
    if not pdf_path:
        abort(404)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=pdf_path.name,
        mimetype="application/pdf",
    )

@app.route("/api/audit", methods=["POST"])
def start_audit():
    """Starts a new GEO audit for a given URL (Phase 2 Stub)"""
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

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
        "notes": [{"date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "text": "Auditoría iniciada automáticamente."}]
    }
    prospects.append(p)
    save_prospects(prospects)
    
    # In Phase 2, this will spawn a background thread calling `geo audit` or the underlying scripts directly.
    def mock_audit_background(pid):
        import time
        time.sleep(5) # Simulate work
        ps = load_prospects()
        target = next((x for x in ps if x.get("id") == pid), None)
        if target:
            target["geo_score"] = 45 # mock result
            target["status"] = "proposal"
            
            # Create a dummy PDF to avoid 404s in the UI
            dummy_pdf_path = PROPOSALS_DIR / f"{domain}_{pid}.pdf"
            dummy_pdf_path.write_text("Dummy PDF content for testing")
            
            save_prospects(ps)
            
    threading.Thread(target=mock_audit_background, args=(new_id,)).start()

    return jsonify({"message": "Audit started", "prospect": p}), 202

# ── Run ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5050)
