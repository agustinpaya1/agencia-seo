import asyncio

from .core import PROPOSALS_DIR


async def mock_audit_background(inserted_id, domain: str, collection):
    await asyncio.sleep(5)  # Simulate work

    await collection.update_one(
        {"_id": inserted_id}, {"$set": {"status": "completed", "geo_score": 85}}
    )

    # Create a dummy PDF to avoid 404s in the UI
    dummy_pdf_path = PROPOSALS_DIR / f"{domain}_{inserted_id}.pdf"
    dummy_pdf_path.write_text("Dummy PDF content for testing")
