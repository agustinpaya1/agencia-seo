from fastapi import APIRouter, Depends
from .endpoints import audit, prospects
from ..dependencies import get_shared_dependency

api_router = APIRouter()

api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["Auditoría"],
    dependencies=[Depends(get_shared_dependency)]
)

api_router.include_router(
    prospects.router,
    prefix="/prospects",
    tags=["Prospects"],
    dependencies=[Depends(get_shared_dependency)]
)
