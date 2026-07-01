from fastapi import Header, HTTPException

async def get_shared_dependency():
    """
    Shared dependency to validate API keys, DB sessions, etc.
    """
    pass
