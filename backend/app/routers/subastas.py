from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.services import subastas as subastas_service

router = APIRouter(prefix="/v1/subastas", tags=["Subastas"])


@router.get("")
async def listar_subastas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    categoria: str | None = Query(None),
    moneda: str | None = Query(None),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    return await subastas_service.listar_subastas(
        db, pagina, cantidad, estado=estado, categoria=categoria, moneda=moneda
    )


@router.get("/{id}")
async def ver_subasta(
    id: int,
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    result = await subastas_service.get_subasta(db, id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."},
        )
    return result


@router.get("/{id}/catalogo")
async def ver_catalogo(
    id: int,
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
):
    result = await subastas_service.get_catalogo(db, id, pagina, cantidad)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta o catálogo no encontrado."},
        )
    return result
