from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Union


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)


class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    expires_in_days: Optional[int] = Field(default=None, gt=0)


class APIKeyRevokeRequest(BaseModel):
    api_key_id: str


class WebhookUserData(BaseModel):
    id: Optional[str] = None
    email: str
    name: Optional[str] = None
    nickname: Optional[str] = None
    role: Optional[str] = None


class WebhookRequest(BaseModel):
    user: Union[str, WebhookUserData]

    def get_user_data(self) -> WebhookUserData:
        if isinstance(self.user, str):
            import json

            return WebhookUserData(**json.loads(self.user))
        return self.user
