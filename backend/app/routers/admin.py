from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.schemas.admin import (
    SolicitudActualizarCliente,
    SolicitudCrearSubastador,
    SolicitudVerificarCliente,
    SolicitudVerificarProducto,
)
from app.services import admin as service

router = APIRouter(prefix="/v1/admin", tags=["Admin"])


@router.get("/clientes")
async def listar_clientes(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    admitido: Literal["si", "no"] | None = Query(None),
    categoria: str | None = Query(None),
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_clientes(db, pagina, cantidad, admitido, categoria)


@router.get("/clientes/{id}")
async def ver_cliente(
    id: int,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    resultado = await service.ver_cliente(db, id)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Cliente no encontrado."},
        )
    return resultado


@router.patch("/clientes/{id}")
async def actualizar_cliente(
    id: int,
    body: SolicitudActualizarCliente,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    datos = body.model_dump(exclude_none=True)
    if not datos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"codigo": "SIN_CAMBIOS", "mensaje": "No se enviaron campos a actualizar."},
        )
    resultado = await service.actualizar_cliente(db, id, datos)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Cliente no encontrado."},
        )
    return resultado




@router.get("/medios-pago")
async def listar_medios_pago(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    verificado: Literal["si", "no"] | None = Query(None),
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_medios_pago(db, pagina, cantidad, verificado)


@router.get("/productos")
async def listar_productos(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_productos_admin(db, pagina, cantidad, estado)


@router.get("/multas")
async def listar_multas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    pagada: Literal["si", "no"] | None = Query(None),
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_multas(db, pagina, cantidad, pagada)


@router.post("/clientes/{id}/verificar")
async def verificar_cliente(
    id: int,
    body: SolicitudVerificarCliente,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    resultado = await service.verificar_cliente_admin(db, id, body.aprobado, body.categoria)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Cliente no encontrado o ya procesado."},
        )
    return resultado


@router.post("/productos/{id}/verificar")
async def verificar_producto(
    id: int,
    body: SolicitudVerificarProducto,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    resultado = await service.verificar_producto_admin(db, id, body.aprobado, body.motivo)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Producto no encontrado o ya procesado."},
        )
    return {"estado": resultado}


@router.post("/subastadores", status_code=status.HTTP_201_CREATED)
async def crear_subastador(
    body: SolicitudCrearSubastador,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.crear_subastador(db, body.model_dump(by_alias=False))


@router.delete("/subastas/{id}")
async def eliminar_subasta(
    id: int,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    eliminada = await service.eliminar_subasta(db, id)
    if not eliminada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."},
        )
    return {"mensaje": "Subasta eliminada"}
