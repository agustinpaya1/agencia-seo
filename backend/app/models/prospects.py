from pydantic import BaseModel

class NoteRequest(BaseModel):
    text: str

class StatusRequest(BaseModel):
    status: str
