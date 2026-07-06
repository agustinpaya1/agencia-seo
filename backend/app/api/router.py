from fastapi import APIRouter, Depends

from ..dependencies import get_shared_dependency
from .endpoints import audit, leads

api_router = APIRouter()

api_router.include_router(
    audit.router, prefix="/audit", tags=["Auditoría"], dependencies=[Depends(get_shared_dependency)]
)

api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["Leads"],
    dependencies=[Depends(get_shared_dependency)],
)
