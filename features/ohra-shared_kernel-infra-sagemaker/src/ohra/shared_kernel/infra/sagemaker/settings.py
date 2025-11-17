from pydantic import BaseModel, Field


class SageMakerSettings(BaseModel):
    embedding_endpoint: str = Field(default="")
    embedding_dimension: int = Field(default=768)
    region: str = Field(default="us-west-2")
