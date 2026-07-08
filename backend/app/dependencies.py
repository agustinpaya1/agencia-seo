import os

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


def get_pagespeed_api_key() -> str | None:
    """
    Extrae la API key de Lighthouse del entorno.
    Devuelve None si no está configurada, permitiendo que la app no crashee
    (la API de Google permite algunas llamadas sin key, aunque con rate limit estricto).
    """
    return os.getenv("PAGESPEED_API_KEY")
