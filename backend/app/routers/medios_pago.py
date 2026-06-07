from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.medios_pago import (
    MedioDePagoResponse,
    SolicitudAgregarMedioDePago,
)
from app.services import medios_pago as medios_service

router = APIRouter(prefix="/v1/medios-de-pago", tags=["Medios de pago"])


@router.get("")
async def listar_medios(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await medios_service.listar_medios(db, user["identificador"], pagina, cantidad)


@router.post("", status_code=status.HTTP_201_CREATED)
async def agregar_medio(
    body: SolicitudAgregarMedioDePago,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    detalle = body.detalle.model_dump(by_alias=False)
    return await medios_service.crear_medio(
        db, user["identificador"], body.tipo, body.moneda, detalle
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar_medio(
    id: int,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    ok = await medios_service.desactivar_medio(db, id, user["identificador"])
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Medio de pago no encontrado."},
        )


@router.post("/{id}/verificar")
async def verificar_medio(
    id: int,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    resultado = await medios_service.verificar_medio(db, id, user["identificador"])
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Medio de pago no encontrado."},
        )
    return resultado
