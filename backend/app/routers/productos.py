import json
import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import Duenio
from app.schemas.productos import ProductoResponse, SeguroResponse, SolicitudAceptarCondiciones
from app.services import productos as productos_service
from app.services.auth import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/productos", tags=["Productos"])


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    user: dict = Depends(require_role("comprador")),
    db: AsyncSession = Depends(get_db),
    descripcionCompleta: str = Form(..., max_length=2000),
    declaracionPropiedad: bool = Form(...),
    precioBase: float = Form(..., gt=0.01),
    foto1: UploadFile = File(...),
    foto2: UploadFile = File(...),
    foto3: UploadFile = File(...),
    foto4: UploadFile = File(...),
    foto5: UploadFile = File(...),
    foto6: UploadFile = File(...),
    foto7: UploadFile | None = File(None),
    foto8: UploadFile | None = File(None),
    detallesArtisticos: str | None = Form(None),
    componentes: str | None = Form(None),
):
    if not declaracionPropiedad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": "La declaración de propiedad debe ser verdadera."},
        )

    if precioBase <= 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "ERROR_VALIDACION", "mensaje": "El precio base debe ser mayor a 0.01."},
        )

    duenio = await db.get(Duenio, user["identificador"])
    if duenio is None:
        duenio = Duenio(
            identificador=user["identificador"],
            verificador=1,  # Midnight Lace
        )
        db.add(duenio)
        await db.flush()

    ts = int(time.time())
    fotos_urls = []
    for i, f in enumerate([foto1, foto2, foto3, foto4, foto5, foto6, foto7, foto8], start=1):
        if f is not None:
            content = await f.read()
            url = save_upload(content, f"producto_{user['identificador']}_{ts}_{i}.jpg")
            fotos_urls.append(url)

    detalle_data = None
    if detallesArtisticos:
        try:
            detalle_data = json.loads(detallesArtisticos)
        except json.JSONDecodeError:
            pass

    componentes_data = None
    if componentes:
        try:
            componentes_data = json.loads(componentes)
        except json.JSONDecodeError:
            pass

    producto = await productos_service.crear_producto(
        db=db,
        duenio_id=user["identificador"],
        descripcion_completa=descripcionCompleta,
        declaracion_propiedad=declaracionPropiedad,
        precio_base=precioBase,
        fotos=fotos_urls,
        detalles_artisticos=detalle_data,
        componentes=componentes_data,
    )

    resultado = await productos_service.verificar_producto(db, producto["identificador"])
    if resultado == "asignado":
        logger.info(f"[PRODUCTO] Producto {producto['identificador']} del dueño {user['identificador']} APROBADO y asignado.")
    elif resultado == "rechazado":
        logger.info(f"[PRODUCTO] Producto {producto['identificador']} del dueño {user['identificador']} RECHAZADO.")

    producto = await productos_service.get_producto(db, producto["identificador"], user["identificador"])
    return producto


@router.get("", response_model=dict)
async def listar_productos(
    pagina: int = Query(1, ge=1),
    cantidad: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    return await productos_service.listar_productos_duenio(
        db, user["identificador"], pagina, cantidad, estado
    )


@router.get("/{id}", response_model=ProductoResponse)
async def ver_producto(
    id: int,
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    producto = await productos_service.get_producto(db, id, user["identificador"])
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Producto no encontrado."},
        )
    return producto


@router.get("/{id}/seguro", response_model=SeguroResponse)
async def ver_seguro(
    id: int,
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    seguro = await productos_service.get_seguro(db, id, user["identificador"])
    if seguro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Seguro no encontrado para este producto."},
        )
    return seguro


@router.patch("/{id}/aceptar-condiciones", response_model=ProductoResponse)
async def aceptar_condiciones(
    id: int,
    body: SolicitudAceptarCondiciones,
    user: dict = Depends(require_role("duenio")),
    db: AsyncSession = Depends(get_db),
):
    try:
        producto = await productos_service.aceptar_condiciones(db, id, user["identificador"], body.acepta)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "ESTADO_INVALIDO", "mensaje": str(e)},
        )
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Producto no encontrado."},
        )
    return producto
