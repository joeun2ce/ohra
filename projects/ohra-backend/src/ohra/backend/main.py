from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from ohra.backend.container import OhraContainer
from ohra.backend.endpoint.rest.fastapi import setup_routes
from ohra.backend.lifespan import lifespan
from ohra.backend.settings import Settings
from ohra.shared_kernel.domain.exception import BaseMsgException
from ohra.shared_kernel.infra.fastapi.exception_handlers.base import custom_exception_handler
from ohra.shared_kernel.infra.fastapi.middlewares.correlation_id import CorrelationIdMiddleware
from ohra.shared_kernel.infra.fastapi.middlewares.session import SessionMiddleware
from ohra.shared_kernel.infra.fastapi.middlewares.auth import AuthMiddleware
from ohra.shared_kernel.infra.fastapi.utils.responses import MsgSpecJSONResponse
from ohra.backend.auth.middleware import validate_auth

container = OhraContainer()
settings: Settings = container.settings.provided()


def create_app() -> FastAPI:
    auth_use_case = container.auth.auth_use_case()

    middleware = [
        Middleware(CorrelationIdMiddleware),
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=settings.cors.allow_methods,
            allow_headers=settings.cors.allow_headers,
        ),
        Middleware(SessionMiddleware, secret_key=settings.session.secret_key),
        Middleware(
            AuthMiddleware,
            auth_validator=lambda req: validate_auth(req, auth_use_case),
            excluded_paths=[
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/v1/openapi.json",
                "/v1/webhook",
            ],
        ),
        Middleware(GZipMiddleware),
    ]

    app = FastAPI(
        title=settings.fastapi.title,
        description=settings.fastapi.description,
        contact=settings.fastapi.contact,
        summary=settings.fastapi.summary,
        middleware=middleware,
        lifespan=lifespan,
        docs_url=settings.fastapi.docs_url,
        redoc_url=settings.fastapi.redoc_url,
        openapi_url=settings.fastapi.openapi_url,
        default_response_class=MsgSpecJSONResponse,
        exception_handlers={
            BaseMsgException: custom_exception_handler,
        },
    )

    app.container = container  # type: ignore
    app.settings = settings  # type: ignore

    setup_routes(app)

    return app


app = create_app()
