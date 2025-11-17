from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 1730000000
    owned_by: str = "ohra"
