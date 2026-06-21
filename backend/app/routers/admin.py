from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.schemas.admin import SolicitudActualizarCliente, SolicitudCrearSubastador
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


@router.get("/multas")
async def listar_multas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    pagada: Literal["si", "no"] | None = Query(None),
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_multas(db, pagina, cantidad, pagada)


@router.post("/subastadores", status_code=status.HTTP_201_CREATED)
async def crear_subastador(
    body: SolicitudCrearSubastador,
    user: dict = Depends(require_role("empleado")),
    db: AsyncSession = Depends(get_db),
):
    return await service.crear_subastador(db, body.model_dump(by_alias=False))
