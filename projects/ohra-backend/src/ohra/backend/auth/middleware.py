from starlette.requests import Request
from typing import Optional

from ohra.backend.auth.use_case import AuthUseCase


async def validate_auth(request: Request, auth_use_case: AuthUseCase) -> Optional[str]:
    x_openwebui_user_email = request.headers.get("X-OpenWebUI-User-Email")
    authorization = request.headers.get("Authorization")

    if x_openwebui_user_email:
        user = await auth_use_case.get_user_by_email(email=x_openwebui_user_email)
        if not user:
            return None
        return user.id

    if authorization:
        api_key = authorization.removeprefix("Bearer ")
        user = await auth_use_case.validate_api_key(api_key)
        if user:
            return user.id

    return None
