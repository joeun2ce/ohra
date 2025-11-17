from ohra.backend.rag.rest.fastapi import router as rag_router
from ohra.backend.auth.rest.fastapi import router as auth_router


def setup_routes(app):
    app.include_router(rag_router)
    app.include_router(auth_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
