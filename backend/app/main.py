import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

load_dotenv()

from .api.router import api_router  # noqa: E402
from .services.persistence import ensure_indexes  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncMongoClient(uri, server_api=ServerApi("1", strict=True, deprecation_errors=True))
    app.state.mongo_client = client
    app.state.db = client[os.getenv("MONGODB_DB", "agencia_seo_dev")]
    # Indexes exist before the app takes traffic: unique snapshot per domain,
    # audits history, and the retry_at partial index for a future retry job.
    await ensure_indexes(app.state.db)
    try:
        yield
    finally:
        await client.close()


app = FastAPI(title="GEO-SEO CRM API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
