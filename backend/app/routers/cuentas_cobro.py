from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.schemas.cuentas_cobro import SolicitudCrearCuentaCobro
from app.services import cuentas_cobro as service

router = APIRouter(prefix="/v1/duenio/cuentas-cobro", tags=["Cuentas de cobro"])


@router.get("")
async def listar_cuentas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_cuentas(db, user["identificador"], pagina, cantidad)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_cuenta(
    body: SolicitudCrearCuentaCobro,
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    return await service.crear_cuenta(db, user["identificador"], body.model_dump(by_alias=False))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar_cuenta(
    id: int,
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    ok = await service.desactivar_cuenta(db, id, user["identificador"])
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Cuenta de cobro no encontrada."},
        )
