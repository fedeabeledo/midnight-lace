from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.dependencies import require_role
from app.schemas.pujas import (
    EstadoPujaActualResponse,
    PujaResponse,
    SolicitudCrearPuja,
)
from app.services import pujas as pujas_service

router = APIRouter(prefix="/v1/subastas", tags=["Pujas"])


@router.get("/{idSubasta}/items/{idItem}/pujas")
async def historial_pujas(
    idSubasta: int,
    idItem: int,
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await pujas_service.historial_pujas(db, idSubasta, idItem, pagina, cantidad)


@router.post(
    "/{idSubasta}/items/{idItem}/pujas",
    response_model=PujaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_puja(
    idSubasta: int,
    idItem: int,
    body: SolicitudCrearPuja,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    resultado = await pujas_service.crear_puja(
        db,
        idSubasta,
        idItem,
        user["identificador"],
        body.importe,
        body.id_medio_de_pago,
    )

    broadcast_data = resultado.pop("_broadcast", None)
    if broadcast_data:
        await ws_manager.broadcast(idSubasta, {
            "evento": "nuevaPuja",
            "datos": broadcast_data,
        })

    return resultado


@router.get("/{id}/item-actual", response_model=EstadoPujaActualResponse)
async def item_actual(
    id: int,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await pujas_service.item_actual(db, id)
