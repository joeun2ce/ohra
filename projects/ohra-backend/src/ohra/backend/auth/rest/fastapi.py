from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body, status

from ohra.backend.container import OhraContainer
from ohra.backend.auth.use_case import AuthUseCase
from ohra.backend.auth.dependencies import get_current_user_id
from ..dtos.request import APIKeyCreateRequest, APIKeyRevokeRequest, WebhookRequest
from ..dtos.response import APIKeyResponse, UserResponse

router = APIRouter(prefix="/v1", tags=["auth"])

get_auth_use_case = Provide[OhraContainer.auth.auth_use_case]


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_api_key(
    *,
    use_case: AuthUseCase = Depends(get_auth_use_case),
    user_id: str = Depends(get_current_user_id),
    payload: APIKeyCreateRequest = Body(),
) -> APIKeyResponse:
    result = await use_case.create_api_key(user_id=user_id, request=payload)
    return APIKeyResponse(
        id=result.id,
        user_id=result.user_id,
        name=result.name,
        key=getattr(result, "key", None),
        expires_at=result.expires_at,
        is_active=result.is_active,
        created_at=result.created_at,
    )


@router.post(
    "/api-keys/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def revoke_api_key(
    *,
    use_case: AuthUseCase = Depends(get_auth_use_case),
    user_id: str = Depends(get_current_user_id),
    payload: APIKeyRevokeRequest = Body(),
):
    await use_case.revoke_api_key(api_key_id=payload.api_key_id, user_id=user_id)


@router.post("/webhook", response_model=UserResponse)
@inject
async def webhook_handler(
    *,
    use_case: AuthUseCase = Depends(get_auth_use_case),
    payload: WebhookRequest = Body(),
) -> UserResponse:
    result = await use_case.handle_webhook(payload)
    return UserResponse(
        id=result.id,
        email=result.email,
        name=result.name,
        is_active=result.is_active,
        is_admin=result.is_admin,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
