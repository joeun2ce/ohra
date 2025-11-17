from pydantic import BaseModel
from typing import Dict, Any


class RetrievedDocument(BaseModel):
    id: int
    score: float
    metadata: Dict[str, Any]

    @property
    def content(self) -> str:
        return self.metadata.get("content", "")

    @property
    def title(self) -> str:
        return self.metadata.get("title", "Unknown")
