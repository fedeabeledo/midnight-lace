from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.services import mi_actividad as mi_actividad_service
from app.services import ws as ws_service

router = APIRouter(prefix="/v1/interno", tags=["Interno"])


class SolicitudCierreItem(BaseModel):
    id_subasta: int


class SolicitudCierreSubasta(BaseModel):
    id_subasta: int


class SolicitudVerificacionCondiciones(BaseModel):
    id_subasta: int


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


@router.post("/verificar-vencimientos")
async def verificar_vencimientos(
    db: AsyncSession = Depends(get_db),
):
    return await mi_actividad_service.verificar_vencimientos(db)


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
