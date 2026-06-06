from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.api_key_middleware import ApiKeyMiddleware
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
        swagger_ui_parameters={"persistAuthorization": True},
    )

    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    from app.routers import auth, interno, medios_pago, paises, perfil, productos, pujas, subastas, subastador, ws

    app.include_router(auth.router)
    app.include_router(interno.router)
    app.include_router(paises.router)
    app.include_router(perfil.router)
    app.include_router(medios_pago.router)
    app.include_router(productos.router)
    app.include_router(pujas.router)
    app.include_router(subastas.router)
    app.include_router(subastador.router)
    app.include_router(ws.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
