from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Midnight Lace API",
        version="1.0.0",
        description="API REST para Midnight Lace — casa de subastas de vestidos EGL.",
        lifespan=lifespan,
    )

    register_error_handlers(app)

    from app.routers import auth, interno, paises

    app.include_router(auth.router)
    app.include_router(interno.router)
    app.include_router(paises.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
