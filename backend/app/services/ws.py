import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.ws_manager import ws_manager
from app.models import (
    Asistente,
    Catalogo,
    ItemCatalogo,
    Notificacion,
    Producto,
    Pujo,
    RegistroDeSubasta,
    Subasta,
)

logger = logging.getLogger(__name__)

MIDNIGHT_LACE_ID = 1


def _schedule_timer(subasta_id: int, duracion_minutos: int):
    async def _delayed():
        await asyncio.sleep(duracion_minutos * 60)
        await _auto_cerrar_item(subasta_id)

    task = asyncio.create_task(_delayed())
    ws_manager.start_item_timer(subasta_id, task)


async def _auto_cerrar_item(subasta_id: int):
    try:
        async with async_session() as db:
            subasta = await db.get(Subasta, subasta_id)
            if subasta is None or subasta.estado != "abierta":
                return
            events = await cerrar_item(db, subasta_id)
            for event in events:
                await ws_manager.broadcast(subasta_id, event)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error auto-cerrando item subasta {subasta_id}: {e}")


async def iniciar_primer_item(db: AsyncSession, subasta_id: int) -> dict | None:
    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )
    if catalogo is None:
        return None

    item = await db.scalar(
        select(ItemCatalogo)
        .where(
            ItemCatalogo.catalogo == catalogo.identificador,
            ItemCatalogo.subastado != "si",
        )
        .order_by(ItemCatalogo.orden.asc())
    )
    if item is None:
        return None

    now = datetime.now(timezone.utc)
    item.iniciado_en = now

    producto = await db.get(Producto, item.producto)
    if producto:
        producto.estado_producto = "en_subasta"

    await db.commit()

    subasta = await db.get(Subasta, subasta_id)
    finaliza_en = now + timedelta(minutes=subasta.duracion_item_minutos)

    _schedule_timer(subasta_id, subasta.duracion_item_minutos)

    return {
        "idItem": item.identificador,
        "descripcionProducto": producto.descripcion_catalogo if producto else None,
        "precioBase": str(item.precio_base),
        "finalizaEn": finaliza_en.isoformat(),
    }


async def cerrar_item(db: AsyncSession, subasta_id: int) -> list[dict]:
    ws_manager.cancel_item_timer(subasta_id)

    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        raise ValueError("Subasta no encontrada.")

    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )
    if catalogo is None:
        raise ValueError("Catálogo no encontrado.")

    item = await db.scalar(
        select(ItemCatalogo)
        .where(
            ItemCatalogo.catalogo == catalogo.identificador,
            ItemCatalogo.subastado != "si",
        )
        .order_by(ItemCatalogo.orden.asc())
    )
    if item is None:
        raise ValueError("No hay ítems activos.")

    now = datetime.now(timezone.utc)
    item.subastado = "si"
    item.finalizado_en = now

    ganadora = await db.scalar(
        select(Pujo)
        .where(Pujo.item == item.identificador)
        .order_by(Pujo.importe.desc())
    )

    events = []
    producto = await db.get(Producto, item.producto)

    if ganadora:
        ganadora.ganador = "si"

        asistente = await db.get(Asistente, ganadora.asistente)
        cliente_id = asistente.cliente if asistente else MIDNIGHT_LACE_ID

        registro = RegistroDeSubasta(
            subasta=subasta_id,
            duenio=producto.duenio if producto else MIDNIGHT_LACE_ID,
            producto=item.producto,
            cliente=cliente_id,
            importe=ganadora.importe,
            comision=item.comision,
            moneda=subasta.moneda,
        )
        db.add(registro)

        if producto:
            producto.estado_producto = "vendido"

        db.add(Notificacion(
            persona=producto.duenio if producto else MIDNIGHT_LACE_ID,
            tipo="producto_vendido",
            detalle=json.dumps({
                "idProducto": item.producto,
                "idItem": item.identificador,
                "idCliente": cliente_id,
                "importe": str(ganadora.importe),
                "idSubasta": subasta_id,
            }),
        ))

        events.append({
            "evento": "pujaGanadora",
            "datos": {
                "idItem": item.identificador,
                "idCliente": cliente_id,
                "importe": str(ganadora.importe),
            },
        })
    else:
        db.add(RegistroDeSubasta(
            subasta=subasta_id,
            duenio=producto.duenio if producto else MIDNIGHT_LACE_ID,
            producto=item.producto,
            cliente=MIDNIGHT_LACE_ID,
            importe=Decimal("0"),
            comision=item.comision,
            moneda=subasta.moneda,
        ))

        db.add(Notificacion(
            persona=producto.duenio if producto else MIDNIGHT_LACE_ID,
            tipo="producto_no_vendido",
            detalle=json.dumps({
                "idProducto": item.producto,
                "idItem": item.identificador,
                "idSubasta": subasta_id,
                "motivo": "sin_pujas",
            }),
        ))

    siguiente = await db.scalar(
        select(ItemCatalogo)
        .where(
            ItemCatalogo.catalogo == catalogo.identificador,
            ItemCatalogo.subastado != "si",
            ItemCatalogo.orden > item.orden,
        )
        .order_by(ItemCatalogo.orden.asc())
    )

    if siguiente:
        siguiente.iniciado_en = now

        siguiente_producto = await db.get(Producto, siguiente.producto)
        if siguiente_producto:
            siguiente_producto.estado_producto = "en_subasta"

        finaliza_en = now + timedelta(minutes=subasta.duracion_item_minutos)

        events.append({
            "evento": "cambioItem",
            "datos": {
                "itemAnterior": {
                    "idItem": item.identificador,
                    "vendido": ganadora is not None,
                },
                "itemActual": {
                    "idItem": siguiente.identificador,
                    "descripcionProducto": siguiente_producto.descripcion_catalogo if siguiente_producto else None,
                    "precioBase": str(siguiente.precio_base),
                    "finalizaEn": finaliza_en.isoformat(),
                },
            },
        })

        await db.commit()
        _schedule_timer(subasta_id, subasta.duracion_item_minutos)
    else:
        subasta.estado = "cerrada"
        await db.commit()

        events.append({
            "evento": "cambioItem",
            "datos": {
                "itemAnterior": {
                    "idItem": item.identificador,
                    "vendido": ganadora is not None,
                },
                "itemActual": None,
            },
        })

        events.append({
            "evento": "subastaFinalizada",
            "datos": {"idSubasta": subasta_id},
        })

    return events


async def cerrar_subasta(db: AsyncSession, subasta_id: int) -> list[dict]:
    ws_manager.cancel_item_timer(subasta_id)

    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        raise ValueError("Subasta no encontrada.")

    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )

    if catalogo:
        result = await db.execute(
            select(ItemCatalogo).where(
                ItemCatalogo.catalogo == catalogo.identificador,
                ItemCatalogo.subastado != "si",
            )
        )
        for it in result.scalars().all():
            it.subastado = "si"
            it.finalizado_en = datetime.now(timezone.utc)

    subasta.estado = "cerrada"
    await db.commit()

    return [{
        "evento": "subastaFinalizada",
        "datos": {"idSubasta": subasta_id},
    }]


async def verificacion_condiciones(db: AsyncSession, subasta_id: int) -> dict:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        raise ValueError("Subasta no encontrada.")

    errores = []

    if subasta.estado != "programada":
        errores.append(f"Estado actual '{subasta.estado}' no permite abrir.")

    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )
    if catalogo is None:
        errores.append("No existe catálogo para esta subasta.")
    else:
        item_count = await db.scalar(
            select(func.count())
            .select_from(ItemCatalogo)
            .where(ItemCatalogo.catalogo == catalogo.identificador)
        )
        if item_count == 0:
            errores.append("El catálogo no tiene ítems.")

    return {
        "idSubasta": subasta_id,
        "apta": len(errores) == 0,
        "errores": errores,
    }
