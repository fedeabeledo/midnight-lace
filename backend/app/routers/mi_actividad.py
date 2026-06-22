from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.schemas.mi_actividad import SolicitudMarcarLeida, SolicitudPagarCompra, SolicitudPagarMulta, SolicitudRetiro
from app.services import mi_actividad as svc

router = APIRouter(prefix="/v1/mi", tags=["Mi Actividad"])


@router.get("/subastas")
async def listar_subastas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.listar_subastas(db, user["identificador"], pagina, cantidad)


@router.get("/pujas")
async def listar_pujas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    idItem: int | None = Query(None),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.listar_pujas(db, user["identificador"], pagina, cantidad, idItem)


@router.get("/compras")
async def listar_compras(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.listar_compras(db, user["identificador"], pagina, cantidad)


@router.patch("/compras/{id}")
async def actualizar_retiro(
    id: int,
    body: SolicitudRetiro,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.actualizar_retiro(db, id, user["identificador"], body.retiraPersonalmente)


@router.post("/compras/{id}/pagar")
async def pagar_compra(
    id: int,
    body: SolicitudPagarCompra,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.pagar_compra(db, id, user["identificador"], body.idMedioPago)


@router.get("/multas")
async def listar_multas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.listar_multas(db, user["identificador"], pagina, cantidad)


@router.post("/multas/{id}/pagar")
async def pagar_multa(
    id: int,
    body: SolicitudPagarMulta,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.pagar_multa(db, id, user["identificador"], body.idMedioPago)


@router.get("/metricas")
async def obtener_metricas(
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.obtener_metricas(db, user["identificador"])


@router.get("/notificaciones")
async def listar_notificaciones(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    leida: str | None = Query(None, pattern="^(si|no)$"),
    user: dict = Depends(require_role("comprador", "duenio")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.listar_notificaciones(db, user["identificador"], pagina, cantidad, leida)


@router.patch("/notificaciones/{id}")
async def marcar_leida(
    id: int,
    body: SolicitudMarcarLeida,
    user: dict = Depends(require_role("comprador", "duenio")),
    db: AsyncSession = Depends(get_db),
):
    return await svc.marcar_leida(db, id, user["identificador"], body.leida)
