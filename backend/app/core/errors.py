from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errores = []
        for err in exc.errors():
            msg = err["msg"]
            if msg.startswith("Value error, "):
                msg = msg[13:]
            loc = " → ".join(str(l) for l in err["loc"] if l != "__root__")
            errores.append(f"{loc}: {msg}" if loc else msg)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "codigo": "ERROR_VALIDACION",
                "mensaje": "Datos inválidos o incompletos.",
                "detalle": errores,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "codigo": "ERROR",
                "mensaje": exc.detail,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "codigo": "ERROR_VALIDACION",
                "mensaje": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "codigo": "ERROR_INTERNO",
                "mensaje": "Error interno del servidor.",
            },
        )
