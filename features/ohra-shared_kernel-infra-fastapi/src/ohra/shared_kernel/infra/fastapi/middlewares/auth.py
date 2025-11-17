from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from typing import Callable, Optional, List


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_validator: Callable[[Request], Optional[str]],
        excluded_paths: List[str],
    ):
        super().__init__(app)
        self.auth_validator = auth_validator
        self.excluded_paths = excluded_paths

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        user_id = await self.auth_validator(request)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required. Provide a valid API key."},
            )

        request.state.user_id = user_id
        return await call_next(request)
