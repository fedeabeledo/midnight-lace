from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

from app.core.api_key_middleware import ApiKeyMiddleware
from app.core.errors import register_error_handlers

api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Midnight Lace API",
        version="1.0.0",
        description="API REST para Midnight Lace — casa de subastas de vestidos EGL.",
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
        dependencies=[Depends(api_key_header)],
    )

    app.add_middleware(ApiKeyMiddleware)

    register_error_handlers(app)

    from app.routers import auth, interno, medios_pago, paises, perfil, productos, pujas, subastas, subastador

    app.include_router(auth.router)
    app.include_router(interno.router)
    app.include_router(paises.router)
    app.include_router(perfil.router)
    app.include_router(medios_pago.router)
    app.include_router(productos.router)
    app.include_router(pujas.router)
    app.include_router(subastas.router)
    app.include_router(subastador.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
