import time
from .core import load_prospects, save_prospects, PROPOSALS_DIR

def mock_audit_background(pid: str, domain: str):
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
