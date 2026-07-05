import json
import logging
import math
import random
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ws_manager
from app.models import (
    Catalogo,
    ItemCatalogo,
    Producto,
    Foto,
    DetalleArtistico,
    ComponenteProducto,
    Deposito,
    Duenio,
    Subastador,
    Seguro,
    Notificacion,
    Subasta,
)

logger = logging.getLogger(__name__)

MOTIVOS_RECHAZO = [
    "Documentación incompleta o ilegible.",
    "Las fotos no permiten verificar el estado del artículo.",
    "El bien no cumple con los estándares de calidad requeridos.",
    "No se pudo verificar la autenticidad del artículo.",
    "El artículo presenta daños no declarados.",
    "La declaración de propiedad no pudo ser validada.",
    "Falta documentación complementaria del origen del bien.",
    "El artículo no encaja en las próximas subastas programadas.",
]


async def crear_producto(
    db: AsyncSession,
    duenio_id: int,
    nombre: str,
    estado: str,
    descripcion_catalogo: str,
    descripcion_completa: str,
    declaracion_propiedad: bool,
    precio_base: Decimal,
    fotos: list[str],
    moneda: str = "ARS",
    detalles_artisticos: dict | None = None,
    componentes: list[dict] | None = None,
) -> dict:
    producto = Producto(
        estado=estado,
        fecha=date.today(),
        disponible="no",
        nombre=nombre,
        descripcion_catalogo=descripcion_catalogo,
        descripcion_completa=descripcion_completa,
        precio_base=precio_base,
        moneda=moneda,
        revisor=1,  # Midnight Lace
        duenio=duenio_id,
        declaracion_propiedad=declaracion_propiedad,
        fecha_ingreso=date.today(),
        estado_producto="pendiente",
    )
    db.add(producto)
    await db.flush()

    for i, url_foto in enumerate(fotos, start=1):
        db.add(Foto(producto=producto.identificador, foto=url_foto, orden=i))

    if detalles_artisticos:
        db.add(DetalleArtistico(
            producto=producto.identificador,
            artista=detalles_artisticos.get("artista", ""),
            fecha_obra=detalles_artisticos.get("fechaObra"),
            historia=detalles_artisticos.get("historia"),
        ))

    if componentes:
        for c in componentes:
            db.add(ComponenteProducto(
                producto=producto.identificador,
                descripcion=c.get("descripcion", ""),
                cantidad=c.get("cantidad", 1),
            ))

    await db.commit()
    return await _serializar_producto(db, producto, moneda=moneda)


async def verificar_producto(db: AsyncSession, producto_id: int) -> str | None:
    producto = await db.get(Producto, producto_id)
    if producto is None or producto.estado_producto != "pendiente":
        return None

    aprobado = random.random() < 0.70

    if aprobado:
        result = await db.execute(select(Subastador.identificador).order_by(Subastador.identificador))
        subastadores = [r[0] for r in result.all()]
        if subastadores:
            producto.subastador_asignado = subastadores[0]

        # Asignar depósito aleatorio
        result = await db.execute(select(Deposito.identificador))
        depositos = [r[0] for r in result.all()]
        if depositos:
            producto.deposito = random.choice(depositos)

        # Crear y asignar seguro (2% del precio base)
        result = await db.execute(select(Seguro))
        seguros = result.scalars().all()
        if seguros:
            seguro_elegido = random.choice(seguros)
            importe_seguro = producto.precio_base * Decimal("0.02")
            poliza = Seguro(
                nro_poliza=f"POL-{producto.identificador:06d}",
                compania=seguro_elegido.compania,
                poliza_combinada=random.choice(["si", "no"]),
                importe=importe_seguro,
            )
            db.add(poliza)
            await db.flush()
            producto.seguro = poliza.nro_poliza

        producto.estado_producto = "asignado"
        await db.commit()

        logger.info(f"[VERIFICACION] Producto {producto_id} APROBADO — seguro: {producto.seguro}, depósito: {producto.deposito}")
        return "asignado"
    else:
        producto.estado_producto = "rechazado"
        await db.flush()

        motivo = random.choice(MOTIVOS_RECHAZO)
        datos_rechazo = {"idProducto": producto_id, "motivo": motivo}
        db.add(Notificacion(
            persona=producto.duenio,
            tipo="producto_rechazado",
            detalle=json.dumps(datos_rechazo),
        ))
        await db.commit()
        await ws_manager.send_to_user(producto.duenio, {"evento": "producto_rechazado", "datos": datos_rechazo})

        logger.info(f"[VERIFICACION] Producto {producto_id} RECHAZADO — motivo: {motivo}")
        return "rechazado"


async def listar_productos_duenio(
    db: AsyncSession, duenio_id: int, pagina: int, cantidad: int, estado: str | None = None
) -> dict:
    query = select(Producto).where(Producto.duenio == duenio_id)
    count_query = select(func.count()).select_from(Producto).where(Producto.duenio == duenio_id)

    if estado:
        query = query.where(Producto.estado_producto == estado)
        count_query = count_query.where(Producto.estado_producto == estado)

    total = await db.scalar(count_query)
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        query.order_by(Producto.identificador.desc()).offset(offset).limit(cantidad)
    )
    productos = result.scalars().all()

    if not productos:
        return {
            "datos": [],
            "meta": {"pagina": pagina, "cantidad": cantidad, "total": total, "total_paginas": total_paginas},
        }

    producto_ids = [p.identificador for p in productos]
    fotos_result = await db.execute(
        select(Foto).where(Foto.producto.in_(producto_ids))
    )
    fotos_por_producto: dict[int, list[dict]] = {}
    for f in fotos_result.scalars().all():
        fotos_por_producto.setdefault(f.producto, []).append({
            "identificador": f.identificador,
            "foto": f.foto,
            "orden": f.orden,
        })
    for fotos in fotos_por_producto.values():
        fotos.sort(key=lambda x: x["orden"])

    detalles_result = await db.execute(
        select(DetalleArtistico).where(DetalleArtistico.producto.in_(producto_ids))
    )
    detalles_por_producto: dict[int, dict] = {}
    for d in detalles_result.scalars().all():
        detalles_por_producto[d.producto] = {
            "artista": d.artista,
            "fechaObra": d.fecha_obra,
            "historia": d.historia,
        }

    datos = []
    for p in productos:
        datos.append(_serializar_producto_lista(
            p,
            fotos_por_producto.get(p.identificador, []),
            detalles_por_producto.get(p.identificador),
        ))

    return {
        "datos": datos,
        "meta": {"pagina": pagina, "cantidad": cantidad, "total": total, "total_paginas": total_paginas},
    }


async def get_producto(db: AsyncSession, producto_id: int, duenio_id: int) -> dict | None:
    producto = await db.get(Producto, producto_id)
    if producto is None:
        return None
    if producto.duenio != duenio_id and producto.estado_producto not in ["asignado", "en_subasta", "subastado", "vendido"]:
        return None
    return await _serializar_producto(db, producto)


async def get_seguro(db: AsyncSession, producto_id: int, duenio_id: int) -> dict | None:
    producto = await db.get(Producto, producto_id)
    if producto is None or producto.duenio != duenio_id:
        return None

    if producto.seguro is None:
        return None

    seguro = await db.get(Seguro, producto.seguro)
    if seguro is None:
        return None

    return {
        "nroPoliza": seguro.nro_poliza,
        "compania": seguro.compania,
        "polizaCombinada": seguro.poliza_combinada,
        "importe": str(seguro.importe),
    }


async def aceptar_condiciones(
    db: AsyncSession, producto_id: int, duenio_id: int, acepta: bool
) -> dict | None:
    producto = await db.get(Producto, producto_id)
    if producto is None or producto.duenio != duenio_id:
        return None

    if producto.estado_producto != "pendiente_confirmacion":
        raise ValueError("El producto no está pendiente de confirmación.")

    if acepta:
        producto.estado_producto = "en_subasta"
        datos_en_subasta = {"idProducto": producto_id}
        db.add(Notificacion(
            persona=duenio_id,
            tipo="producto_en_subasta",
            detalle=json.dumps(datos_en_subasta),
        ))
        await db.commit()
        await ws_manager.send_to_user(duenio_id, {"evento": "producto_en_subasta", "datos": datos_en_subasta})
    else:
        item = await db.scalar(select(ItemCatalogo).where(ItemCatalogo.producto == producto_id))
        if item is not None:
            await db.delete(item)
        producto.estado_producto = "asignado"
        datos_devolucion = {"idProducto": producto_id}
        db.add(Notificacion(
            persona=duenio_id,
            tipo="devolucion_producto",
            detalle=json.dumps(datos_devolucion),
        ))
        await db.commit()
        await ws_manager.send_to_user(duenio_id, {"evento": "devolucion_producto", "datos": datos_devolucion})

    return await _serializar_producto(db, producto)


async def get_condiciones(db: AsyncSession, producto_id: int, duenio_id: int) -> dict | None:
    producto = await db.get(Producto, producto_id)
    if producto is None or producto.duenio != duenio_id:
        return None
    if producto.estado_producto != "pendiente_confirmacion":
        raise ValueError("El producto no está pendiente de confirmación.")
    item = await db.scalar(select(ItemCatalogo).where(ItemCatalogo.producto == producto_id))
    if item is None:
        raise ValueError("Item de catálogo no encontrado.")
    catalogo = await db.get(Catalogo, item.catalogo)
    subasta = await db.get(Subasta, catalogo.subasta) if catalogo else None
    return {
        "precioBase": str(item.precio_base),
        "comision": str(item.comision),
        "fecha": subasta.fecha.isoformat() if subasta and subasta.fecha else None,
        "hora": subasta.hora.isoformat() if subasta and subasta.hora else None,
        "lugar": subasta.ubicacion if subasta else None,
    }


async def _serializar_producto(db: AsyncSession, producto: Producto, moneda: str | None = None) -> dict:
    # Fotos
    result = await db.execute(
        select(Foto).where(Foto.producto == producto.identificador).order_by(Foto.orden)
    )
    fotos = [
        {"identificador": f.identificador, "foto": f.foto, "orden": f.orden}
        for f in result.scalars().all()
    ]

    # Detalle artistico
    result = await db.execute(
        select(DetalleArtistico).where(DetalleArtistico.producto == producto.identificador)
    )
    detalle = result.scalar_one_or_none()
    detalle_data = None
    if detalle:
        detalle_data = {
            "artista": detalle.artista,
            "fechaObra": detalle.fecha_obra,
            "historia": detalle.historia,
        }

    # Componentes
    result = await db.execute(
        select(ComponenteProducto).where(ComponenteProducto.producto == producto.identificador)
    )
    componentes = [
        {"identificador": c.identificador, "descripcion": c.descripcion, "cantidad": c.cantidad}
        for c in result.scalars().all()
    ]

    # Seguro
    seguro_data = None
    if producto.seguro:
        seguro = await db.get(Seguro, producto.seguro)
        if seguro:
            seguro_data = {
                "nroPoliza": seguro.nro_poliza,
                "compania": seguro.compania,
                "polizaCombinada": seguro.poliza_combinada,
                "importe": str(seguro.importe),
            }

    # Depósito
    deposito_data = None
    if producto.deposito:
        deposito = await db.get(Deposito, producto.deposito)
        if deposito:
            deposito_data = {
                "identificador": deposito.identificador,
                "nombre": deposito.nombre,
                "direccion": deposito.direccion,
            }

    # Motivo de rechazo (si el producto fue rechazado)
    motivo_rechazo = None
    if producto.estado_producto == "rechazado":
        result = await db.execute(
            select(Notificacion)
            .where(
                Notificacion.persona == producto.duenio,
                Notificacion.tipo == "producto_rechazado",
                Notificacion.detalle.ilike(f'%\"idProducto\": {producto.identificador}%'),
            )
            .order_by(Notificacion.identificador.desc())
            .limit(1)
        )
        notif = result.scalar_one_or_none()
        if notif:
            try:
                detalle = json.loads(notif.detalle)
                motivo_rechazo = detalle.get("motivo", "Sin motivo especificado.")
            except (json.JSONDecodeError, KeyError):
                pass

    return {
        "identificador": producto.identificador,
        "nombre": producto.nombre,
        "estado": producto.estado,
        "fecha": producto.fecha,
        "disponible": producto.disponible,
        "descripcionCatalogo": producto.descripcion_catalogo,
        "descripcionCompleta": producto.descripcion_completa,
        "precioBase": str(producto.precio_base),
        "moneda": moneda or producto.moneda,
        "estadoProducto": producto.estado_producto,
        "declaracionPropiedad": producto.declaracion_propiedad,
        "fotos": fotos,
        "detalleArtistico": detalle_data,
        "componentes": componentes,
        "seguro": seguro_data,
        "deposito": deposito_data,
        "motivoRechazo": motivo_rechazo,
    }


def _serializar_producto_lista(
    producto: Producto,
    fotos: list[dict],
    detalle_artistico: dict | None = None,
) -> dict:
    return {
        "identificador": producto.identificador,
        "nombre": producto.nombre,
        "estado": producto.estado,
        "fecha": producto.fecha,
        "disponible": producto.disponible,
        "descripcionCatalogo": producto.descripcion_catalogo,
        "descripcionCompleta": producto.descripcion_completa,
        "precioBase": str(producto.precio_base),
        "moneda": producto.moneda,
        "estadoProducto": producto.estado_producto,
        "declaracionPropiedad": producto.declaracion_propiedad,
        "fotos": fotos,
        "detalleArtistico": detalle_artistico,
    }
