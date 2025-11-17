from pydantic import BaseModel, Field
from typing import List, Optional, Union

from .schemas import ChatMessage


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = Field(default="Qwen/Qwen3-4B-Instruct-2507")
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2000, gt=0)
    stream: Optional[bool] = False
    user: Optional[str] = None


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = Field(default="ohra-embedding")
    user: Optional[str] = None


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=-1, le=5)
    comment: str = Field(default="")
