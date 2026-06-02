import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.api_key:
            return await call_next(request)

        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-Api-Key", "")
        if not secrets.compare_digest(api_key, settings.api_key):
            return JSONResponse(
                status_code=403,
                content={
                    "codigo": "API_KEY_INVALIDA",
                    "mensaje": "API key inválida o ausente.",
                },
            )

        return await call_next(request)
