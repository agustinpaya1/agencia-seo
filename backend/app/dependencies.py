from fastapi import Request

from .services.persistence import leads_collection_name


async def get_shared_dependency():
    """
    Shared dependency to validate API keys, DB sessions, etc.
    """
    pass


def get_db(request: Request):
    """The whole Mongo database handle.

    Persistence fans one audit out over several collections (``audit_runs`` +
    the ``audit_reports_*`` category collections) and owns their names, so
    endpoints hand the ``db`` down instead of injecting collections one by one.
    """
    return request.app.state.db


def get_leads_collection(request: Request):
    return request.app.state.db[leads_collection_name()]
