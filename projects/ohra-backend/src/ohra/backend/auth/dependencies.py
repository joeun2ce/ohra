from fastapi import Request, HTTPException, status


async def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user_id


async def get_current_user_id_optional(request: Request) -> str | None:
    return getattr(request.state, "user_id", None)
