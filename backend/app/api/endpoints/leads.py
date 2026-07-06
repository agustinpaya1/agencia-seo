from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pymongo import ReturnDocument

from ...dependencies import get_prospects_collection
from ...models.prospects import NoteRequest, StatusRequest
from ...services.core import crm_stats, find_pdf

router = APIRouter()


@router.get("")
async def get_prospects(
    status: str = "", sort: str = "score", collection=Depends(get_prospects_collection)
):
    query = {}
    if status:
        query["status"] = status

    cursor = collection.find(query)

    if sort == "score":
        cursor = cursor.sort("geo_score", 1)
    elif sort == "company":
        cursor = cursor.sort("company", 1)
    elif sort == "mrr":
        cursor = cursor.sort("monthly_value", -1)

    docs = await cursor.to_list(length=100)

    prospects = []
    for doc in docs:
        doc["id"] = str(doc.pop("_id"))
        prospects.append(doc)

    stats = crm_stats(prospects)

    return {"prospects": prospects, "stats": stats}


@router.get("/{pid}")
async def get_prospect_detail(pid: str, collection=Depends(get_prospects_collection)):
    try:
        obj_id = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    p = await collection.find_one({"_id": obj_id})
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    p["id"] = str(p.pop("_id"))
    p["has_pdf"] = find_pdf(p) is not None
    return p


@router.post("/{pid}/note")
async def add_note(pid: str, data: NoteRequest, collection=Depends(get_prospects_collection)):
    try:
        obj_id = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    text = data.text.strip()
    if text:
        new_note = {
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "text": text,
        }
        result = await collection.find_one_and_update(
            {"_id": obj_id},
            {
                "$push": {"notes": new_note},
                "$set": {"updated_at": datetime.now().strftime("%Y-%m-%d")},
            },
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Prospect not found")
        result["id"] = str(result.pop("_id"))
        return result
    raise HTTPException(status_code=400, detail="Note text is required")


@router.put("/{pid}/status")
async def update_status(
    pid: str, data: StatusRequest, collection=Depends(get_prospects_collection)
):
    try:
        obj_id = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    new_status = data.status.strip()
    valid_statuses = ["lead", "audit", "proposal", "active", "churned", "lost", "completed"]

    if new_status in valid_statuses:
        result = await collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": {"status": new_status, "updated_at": datetime.now().strftime("%Y-%m-%d")}},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Prospect not found")
        result["id"] = str(result.pop("_id"))
        return result
    raise HTTPException(status_code=400, detail="Invalid status")


@router.get("/{pid}/pdf")
async def download_pdf(pid: str, collection=Depends(get_prospects_collection)):
    try:
        obj_id = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    p = await collection.find_one({"_id": obj_id})
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    p["id"] = str(p.pop("_id"))
    pdf_path = find_pdf(p)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(path=pdf_path, filename=pdf_path.name, media_type="application/pdf")
