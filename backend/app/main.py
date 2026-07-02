import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

from .api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncMongoClient(uri, server_api=ServerApi("1", strict=True, deprecation_errors=True))
    app.state.mongo_client = client
    app.state.db = client[os.getenv("MONGODB_DB", "agencia_seo_dev")]
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
