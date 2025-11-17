from pydantic import BaseModel, Field


class QdrantSettings(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=6333)
    collection_name: str = Field(default="ohra_documents")
