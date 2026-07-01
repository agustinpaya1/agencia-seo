from pydantic import BaseModel

class AuditRequest(BaseModel):
    url: str
