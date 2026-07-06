from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pymongo import ReturnDocument

from ...dependencies import get_leads_collection
from ...models.leads import LeadNoteRequest, LeadStatusRequest
from ...services.core import crm_stats, find_pdf

router = APIRouter()


@router.get(
    "",
    operation_id="list_leads",
    summary="Lista los leads del CRM (tope 100, sin paginación)",
    description=(
        'Devuelve `{"leads": [...], "stats": {...}}`. `status` filtra por igualdad '
        "exacta contra el campo homónimo del documento; `sort` acepta `score` "
        "(geo_score ascendente), `company` (alfabético) o `mrr` (monthly_value "
        "descendente) — cualquier otro valor devuelve el orden natural de Mongo. "
        "`stats` son agregados CRM (total, active, mrr, pipeline, avg_score, "
        "avg_tier) calculados sobre los documentos devueltos. Estructura "
        "provisional: corta en 100 documentos y no hay paginación todavía."
    ),
)
async def list_leads(
    status: str = "", sort: str = "score", collection=Depends(get_leads_collection)
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

    leads = []
    for doc in docs:
        doc["id"] = str(doc.pop("_id"))
        leads.append(doc)

    stats = crm_stats(leads)

    return {"leads": leads, "stats": stats}


@router.get(
    "/{lead_id}",
    operation_id="get_lead_detail",
    summary="Detalle de un lead",
    description=(
        "Devuelve el documento crudo del lead (con `_id` expuesto como `id`) más "
        "`has_pdf`: si existe una propuesta PDF pre-generada en el filesystem "
        "(`~/.geo-prospects/proposals/{domain}*.pdf`). 400 si el id no es un "
        "ObjectId válido, 404 si no existe."
    ),
)
async def get_lead_detail(lead_id: str, collection=Depends(get_leads_collection)):
    try:
        obj_id = ObjectId(lead_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    lead = await collection.find_one({"_id": obj_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead["id"] = str(lead.pop("_id"))
    lead["has_pdf"] = find_pdf(lead) is not None
    return lead


@router.post(
    "/{lead_id}/note",
    operation_id="add_lead_note",
    summary="Añade una nota CRM al lead",
    description=(
        "Hace `$push` de `{date, text}` (fecha generada en el servidor) al array "
        "`notes` del lead y actualiza `updated_at`. Devuelve el documento "
        "actualizado. 400 si el texto viene vacío, 404 si el lead no existe."
    ),
)
async def add_lead_note(
    lead_id: str, data: LeadNoteRequest, collection=Depends(get_leads_collection)
):
    try:
        obj_id = ObjectId(lead_id)
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
            raise HTTPException(status_code=404, detail="Lead not found")
        result["id"] = str(result.pop("_id"))
        return result
    raise HTTPException(status_code=400, detail="Note text is required")


@router.put(
    "/{lead_id}/status",
    operation_id="update_lead_status",
    summary="Cambia la etapa del lead en el pipeline",
    description=(
        "Acepta exactamente uno de: `lead`, `audit`, `proposal`, `active`, "
        "`churned`, `lost`, `completed` (aquí `lead` es la etapa CRM inicial, no "
        "la entidad ni el flag `is_lead` del motor). Actualiza `status` y "
        "`updated_at` y devuelve el documento actualizado. 400 fuera de la "
        "whitelist, 404 si el lead no existe. También sirve para desbloquear a "
        "mano un lead atascado en `audit` tras un crash del proceso."
    ),
)
async def update_lead_status(
    lead_id: str, data: LeadStatusRequest, collection=Depends(get_leads_collection)
):
    try:
        obj_id = ObjectId(lead_id)
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
            raise HTTPException(status_code=404, detail="Lead not found")
        result["id"] = str(result.pop("_id"))
        return result
    raise HTTPException(status_code=400, detail="Invalid status")


@router.get(
    "/{lead_id}/pdf",
    operation_id="download_lead_pdf",
    summary="Descarga la propuesta PDF del lead",
    description=(
        "Sirve un PDF pre-generado desde el filesystem "
        "(`~/.geo-prospects/proposals/{domain}*.pdf`, el más reciente por nombre); "
        "este endpoint NO genera el PDF. 404 si el lead no existe o si no hay "
        "ningún PDF para su dominio."
    ),
)
async def download_lead_pdf(lead_id: str, collection=Depends(get_leads_collection)):
    try:
        obj_id = ObjectId(lead_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    lead = await collection.find_one({"_id": obj_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead["id"] = str(lead.pop("_id"))
    pdf_path = find_pdf(lead)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(path=pdf_path, filename=pdf_path.name, media_type="application/pdf")
