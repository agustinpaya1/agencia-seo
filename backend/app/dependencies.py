import os
from fastapi import Header, HTTPException, Request

async def get_shared_dependency():
    """
    Shared dependency to validate API keys, DB sessions, etc.
    """
    pass

def get_prospects_collection(request: Request):
    return request.app.state.db[os.getenv("MONGODB_COLLECTION", "prospects")]
