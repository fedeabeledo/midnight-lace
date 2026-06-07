from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.services import auth as auth_service
from app.services import productos as productos_service
from app.services import ws as ws_service

router = APIRouter(prefix="/v1/interno", tags=["Interno"])


class SolicitudVerificacion(BaseModel):
    email: EmailStr


class SolicitudVerificacionProducto(BaseModel):
    id_producto: int


class SolicitudCierreItem(BaseModel):
    id_subasta: int


class SolicitudCierreSubasta(BaseModel):
    id_subasta: int


class SolicitudVerificacionCondiciones(BaseModel):
    id_subasta: int


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

    resultado = await auth_service.verificar_cliente(db, persona_id)
    if resultado["aprobado"]:
        codigo = resultado["codigo"]
        print(f"[VERIFICACION] Cliente {persona_id} APROBADO. Código: {codigo}")
        print(f"[VERIFICACION] → Enviar email a {body.email} con código: {codigo}")
        return {
            "aprobado": True,
            "codigo_confirmacion": codigo,
            "mensaje": "Cliente aprobado. Se envió email con código para setear clave.",
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


@router.post("/cierre-item")
async def cierre_item(
    body: SolicitudCierreItem,
    db: AsyncSession = Depends(get_db),
):
    try:
        events = await ws_service.cerrar_item(db, body.id_subasta)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": str(e)},
        )

    for event in events:
        await ws_manager.broadcast(body.id_subasta, event)

    return {"eventos": events}


@router.post("/cierre-subasta")
async def cierre_subasta(
    body: SolicitudCierreSubasta,
    db: AsyncSession = Depends(get_db),
):
    try:
        events = await ws_service.cerrar_subasta(db, body.id_subasta)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": str(e)},
        )

    for event in events:
        await ws_manager.broadcast(body.id_subasta, event)

    return {"eventos": events}


@router.post("/verificacion-condiciones")
async def verificacion_condiciones(
    body: SolicitudVerificacionCondiciones,
    db: AsyncSession = Depends(get_db),
):
    try:
        resultado = await ws_service.verificacion_condiciones(db, body.id_subasta)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": str(e)},
        )
    return resultado
