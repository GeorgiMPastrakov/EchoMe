from uuid import UUID
from pydantic import BaseModel


class VoiceRead(BaseModel):
    id: UUID
    label: str
    filename: str
