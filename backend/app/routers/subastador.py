from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.schemas.subastas import (
    CatalogoResponse,
    ItemCatalogoResponse,
    SolicitudAgregarItemCatalogo,
    SolicitudCambiarEstado,
    SolicitudCrearCatalogo,
    SolicitudCrearSubasta,
    SolicitudActualizarSubasta,
    SubastaResponse,
)
from app.services import subastas as subastas_service

router = APIRouter(prefix="/v1/subastador", tags=["Subastador"])


@router.get("/subastas")
async def listar_subastas(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    return await subastas_service.listar_subastas(
        db, pagina, cantidad, estado=estado, subastador_id=user["identificador"]
    )


@router.post("/subastas", response_model=SubastaResponse, status_code=status.HTTP_201_CREATED)
async def crear_subasta(
    body: SolicitudCrearSubasta,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    return await subastas_service.crear_subasta(
        db=db,
        subastador_id=user["identificador"],
        nombre=body.nombre,
        fecha=body.fecha,
        hora=body.hora,
        categoria=body.categoria,
        moneda=body.moneda,
        duracion_item_minutos=body.duracion_item_minutos,
        ubicacion=body.ubicacion,
        capacidad_asistentes=body.capacidad_asistentes,
        tiene_deposito=body.tiene_deposito,
        seguridad_propia=body.seguridad_propia,
    )


@router.patch("/subastas/{id}", response_model=SubastaResponse)
async def actualizar_subasta(
    id: int,
    body: SolicitudActualizarSubasta,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    kwargs = body.model_dump(exclude_none=True)
    try:
        result = await subastas_service.actualizar_subasta(db, id, user["identificador"], **kwargs)
    except ValueError as e:
        raise HTTPException(status_code=409, detail={"codigo": "ESTADO_INVALIDO", "mensaje": str(e)})
    if result is None:
        raise HTTPException(status_code=404, detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."})
    return result


@router.patch("/subastas/{id}/estado", response_model=SubastaResponse)
async def cambiar_estado(
    id: int,
    body: SolicitudCambiarEstado,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await subastas_service.cambiar_estado(db, id, user["identificador"], body.estado)
    except ValueError as e:
        raise HTTPException(status_code=409, detail={"codigo": "TRANSICION_INVALIDA", "mensaje": str(e)})
    if result is None:
        raise HTTPException(status_code=404, detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."})
    return result


@router.get("/subastas/{id}/registros")
async def get_registros(
    id: int,
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    result = await subastas_service.get_registros(db, id, user["identificador"], pagina, cantidad)
    if result is None:
        raise HTTPException(status_code=404, detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."})
    return result


@router.post("/catalogos", response_model=CatalogoResponse, status_code=status.HTTP_201_CREATED)
async def crear_catalogo(
    body: SolicitudCrearCatalogo,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await subastas_service.crear_catalogo(
            db, user["identificador"], body.descripcion, body.id_subasta
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"codigo": "ERROR_VALIDACION", "mensaje": str(e)})


@router.post("/catalogos/{id}/items", response_model=ItemCatalogoResponse, status_code=status.HTTP_201_CREATED)
async def agregar_item(
    id: int,
    body: SolicitudAgregarItemCatalogo,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await subastas_service.agregar_item_catalogo(
            db, id, user["identificador"], body.id_producto, body.orden, body.comision
        )
    except ValueError as e:
        code = "CONFLICTO" if "ya está" in str(e) else "ERROR_VALIDACION"
        http_code = 409 if "ya está" in str(e) else 400
        raise HTTPException(status_code=http_code, detail={"codigo": code, "mensaje": str(e)})


@router.delete("/catalogos/{idCatalogo}/items/{idItem}", status_code=status.HTTP_204_NO_CONTENT)
async def quitar_item(
    idCatalogo: int,
    idItem: int,
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ok = await subastas_service.quitar_item_catalogo(db, idCatalogo, idItem, user["identificador"])
    except ValueError as e:
        raise HTTPException(status_code=409, detail={"codigo": "ESTADO_INVALIDO", "mensaje": str(e)})
    if not ok:
        raise HTTPException(status_code=404, detail={"codigo": "NO_ENCONTRADO", "mensaje": "Ítem no encontrado."})


@router.get("/productos")
async def get_pool(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    user: dict = Depends(require_role("subastador")),
    db: AsyncSession = Depends(get_db),
):
    return await subastas_service.get_pool_productos(db, user["identificador"], pagina, cantidad, estado)
