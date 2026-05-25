import math

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.paises import Pais
from app.schemas.paises import MetaPaginacion, PaginaPaises, PaisResponse

router = APIRouter(prefix="/v1/paises", tags=["Países"])


@router.get("", response_model=PaginaPaises)
async def listar_paises(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count()).select_from(Pais))
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(Pais).order_by(Pais.numero).offset(offset).limit(cantidad)
    )
    paises = result.scalars().all()

    return PaginaPaises(
        datos=[PaisResponse.model_validate(p) for p in paises],
        meta=MetaPaginacion(
            pagina=pagina, cantidad=cantidad, total=total, total_paginas=total_paginas
        ),
    )


@router.get(
    "/{id}",
    response_model=PaisResponse,
    responses={
        404: {
            "description": "País no encontrado",
            "content": {
                "application/json": {
                    "example": {"codigo": "NO_ENCONTRADO", "mensaje": "País no encontrado."}
                }
            },
        }
    },
)
async def obtener_pais(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    pais = await db.get(Pais, id)
    if pais is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "País no encontrado."},
        )
    return PaisResponse.model_validate(pais)
