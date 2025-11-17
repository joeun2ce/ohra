from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    name: str
    key: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime


class APIKeyListResponse(BaseModel):
    keys: List[APIKeyResponse]
