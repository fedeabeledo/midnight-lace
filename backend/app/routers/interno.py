from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import auth as auth_service
from app.services import productos as productos_service

router = APIRouter(prefix="/v1/interno", tags=["Interno"])


class SolicitudVerificacion(BaseModel):
    email: EmailStr


class SolicitudVerificacionProducto(BaseModel):
    id_producto: int


@router.post("/verificacion-cliente")
async def verificacion_cliente(
    body: SolicitudVerificacion,
    db: AsyncSession = Depends(get_db),
):
    persona_id = await auth_service.get_persona_id_por_email(db, body.email)
    if persona_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "No hay registro pendiente para ese email."},
        )

    ya_verificado = await auth_service.cliente_ya_verificado(db, persona_id)
    if ya_verificado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "YA_VERIFICADO", "mensaje": "Este cliente ya fue verificado anteriormente."},
        )

    token = await auth_service.verificar_cliente(db, persona_id)
    if token is not None:
        print(f"[VERIFICACION] Cliente {persona_id} APROBADO. Token: {token}")
        print(f"[VERIFICACION] → Enviar email a {body.email} con link: http://localhost:8000/confirmar?token={token}")
        return {
            "aprobado": True,
            "token_confirmacion": token,
            "mensaje": "Cliente aprobado. Se envió email con link para setear clave.",
        }
    else:
        print(f"[VERIFICACION] Cliente {persona_id} RECHAZADO.")
        print(f"[VERIFICACION] → Enviar email a {body.email} notificando el rechazo.")
        return {
            "aprobado": False,
            "mensaje": "Cliente rechazado. Se envió email de notificación.",
        }


@router.post("/verificacion-producto")
async def verificacion_producto(
    body: SolicitudVerificacionProducto,
    db: AsyncSession = Depends(get_db),
):
    resultado = await productos_service.verificar_producto(db, body.id_producto)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": "Producto no encontrado o ya verificado."},
        )
    return {"estado": resultado}
