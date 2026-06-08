from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})
        schema["components"]["securitySchemes"]["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Api-Key",
        }
        # Inyectar ApiKeyAuth en CADA endpoint (los que ya tienen HTTPBearer lo mantienen, los que no, lo reciben).
        # Esto es necesario porque FastAPI solo inyecta HTTPBearer en los endpoints con Depends(get_current_user),
        # pero el middleware requiere X-Api-Key en TODOS los endpoints (excepto los exempts que no aparecen en swagger).
        for path, methods in schema.get("paths", {}).items():
            for method, op in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                existing = op.get("security", [])
                has_apikey = any("ApiKeyAuth" in s for s in existing)
                if not has_apikey:
                    existing.append({"ApiKeyAuth": []})
                op["security"] = existing
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    @app.get("/health")
    async def estado():
        return {"status": "ok"}

    return app


app = create_app()
