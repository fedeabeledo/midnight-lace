import json
import math
from datetime import date, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ws_manager
from app.models import (
    Catalogo,
    Foto,
    ItemCatalogo,
    Notificacion,
    Persona,
    Producto,
    RegistroDeSubasta,
    Subasta,
)


def _parse_hora(hora: str) -> time:
    parts = hora.split(":")
    return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


async def crear_subasta(
    db: AsyncSession,
    subastador_id: int,
    nombre: str,
    fecha: date,
    hora: str,
    categoria: str,
    moneda: str,
    duracion_item_minutos: int,
    ubicacion: str,
    capacidad_asistentes: int | None = None,
    tiene_deposito: str | None = None,
    seguridad_propia: str | None = None,
    foto_principal: str | None = None,
) -> dict:
    subasta = Subasta(
        nombre=nombre,
        fecha=fecha,
        hora=_parse_hora(hora),
        estado="programada",
        subastador=subastador_id,
        ubicacion=ubicacion,
        capacidad_asistentes=capacidad_asistentes,
        tiene_deposito=tiene_deposito,
        seguridad_propia=seguridad_propia,
        categoria=categoria,
        moneda=moneda,
        duracion_item_minutos=duracion_item_minutos,
        foto_principal=foto_principal,
    )
    db.add(subasta)
    await db.commit()
    return _serialize_subasta(subasta)


async def listar_subastas(
    db: AsyncSession,
    pagina: int,
    cantidad: int,
    estado: str | None = None,
    categoria: str | None = None,
    moneda: str | None = None,
    subastador_id: int | None = None,
) -> dict:
    query = select(Subasta)
    count_q = select(func.count()).select_from(Subasta)

    if subastador_id is not None:
        query = query.where(Subasta.subastador == subastador_id)
        count_q = count_q.where(Subasta.subastador == subastador_id)
    if estado:
        query = query.where(Subasta.estado == estado)
        count_q = count_q.where(Subasta.estado == estado)
    if categoria:
        query = query.where(Subasta.categoria == categoria)
        count_q = count_q.where(Subasta.categoria == categoria)
    if moneda:
        query = query.where(Subasta.moneda == moneda)
        count_q = count_q.where(Subasta.moneda == moneda)

    total = await db.scalar(count_q)
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        query.order_by(Subasta.identificador.desc()).offset(offset).limit(cantidad)
    )
    subastas = result.scalars().all()

    return {
        "datos": [_serialize_subasta(s) for s in subastas],
        "meta": {"pagina": pagina, "cantidad": cantidad, "total": total, "total_paginas": total_paginas},
    }


async def get_subasta(db: AsyncSession, subasta_id: int) -> dict | None:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        return None
    return _serialize_subasta(subasta)


async def actualizar_subasta(
    db: AsyncSession, subasta_id: int, subastador_id: int, **kwargs
) -> dict | None:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None or subasta.subastador != subastador_id:
        return None
    if subasta.estado != "programada":
        raise ValueError("Solo se puede modificar una subasta en estado 'programada'.")

    field_map = {
        "fecha": "fecha",
        "hora": "hora",
        "ubicacion": "ubicacion",
        "capacidad_asistentes": "capacidad_asistentes",
        "tiene_deposito": "tiene_deposito",
        "seguridad_propia": "seguridad_propia",
        "duracion_item_minutos": "duracion_item_minutos",
    }
    for key, attr in field_map.items():
        if key in kwargs and kwargs[key] is not None:
            val = kwargs[key]
            if key == "hora":
                val = _parse_hora(val)
            setattr(subasta, attr, val)

    await db.commit()
    return _serialize_subasta(subasta)


async def cambiar_estado(
    db: AsyncSession, subasta_id: int, subastador_id: int, nuevo_estado: str
) -> dict | None:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None or subasta.subastador != subastador_id:
        return None

    transiciones = {
        "programada": ["abierta"],
        "abierta": ["cerrada"],
    }
    permitidos = transiciones.get(subasta.estado, [])
    if nuevo_estado not in permitidos:
        raise ValueError(
            f"Transición inválida: '{subasta.estado}' → '{nuevo_estado}'."
        )

    subasta.estado = nuevo_estado
    await db.commit()
    return _serialize_subasta(subasta)


async def get_registros(
    db: AsyncSession, subasta_id: int, subastador_id: int, pagina: int, cantidad: int
) -> dict | None:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None or subasta.subastador != subastador_id:
        return None

    count_q = select(func.count()).select_from(RegistroDeSubasta).where(
        RegistroDeSubasta.subasta == subasta_id
    )
    total = await db.scalar(count_q)
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(RegistroDeSubasta)
        .where(RegistroDeSubasta.subasta == subasta_id)
        .order_by(RegistroDeSubasta.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    registros = result.scalars().all()

    MIDNIGHT_LACE_ID = 1
    datos = []
    for r in registros:
        no_vendido = (r.cliente == MIDNIGHT_LACE_ID and r.importe == Decimal("0"))
        datos.append({
            "identificador": r.identificador,
            "idSubasta": r.subasta,
            "idDuenio": r.duenio,
            "idProducto": r.producto,
            "idCliente": None if no_vendido else r.cliente,
            "vendido": not no_vendido,
            "importe": str(r.importe),
            "comision": str(r.comision),
            "costoEnvio": str(r.costo_envio),
            "moneda": r.moneda,
            "retiraPersonalmente": r.retira_personalmente,
            "pagado": r.pagado,
        })

    return {
        "datos": datos,
        "meta": {"pagina": pagina, "cantidad": cantidad, "total": total, "total_paginas": total_paginas},
    }


async def crear_catalogo(
    db: AsyncSession, subastador_id: int, descripcion: str, subasta_id: int
) -> dict:
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None or subasta.subastador != subastador_id:
        raise ValueError("Subasta no encontrada o no pertenece al subastador.")

    catalogo = Catalogo(
        descripcion=descripcion,
        subasta=subasta_id,
        responsable=1,  # Midnight Lace
    )
    db.add(catalogo)
    await db.commit()

    return {
        "identificador": catalogo.identificador,
        "descripcion": catalogo.descripcion,
        "idSubasta": catalogo.subasta,
        "idSubastador": subastador_id,
        "items": [],
    }


async def agregar_item_catalogo(
    db: AsyncSession,
    catalogo_id: int,
    subastador_id: int,
    producto_id: int,
    orden: int,
    comision: Decimal,
) -> dict:
    catalogo = await db.get(Catalogo, catalogo_id)
    if catalogo is None:
        raise ValueError("Catálogo no encontrado.")

    subasta = await db.get(Subasta, catalogo.subasta)
    if subasta is None or subasta.subastador != subastador_id:
        raise ValueError("Catálogo no pertenece al subastador.")

    producto = await db.get(Producto, producto_id)
    if producto is None:
        raise ValueError("Producto no encontrado.")

    if producto.estado_producto != "asignado":
        raise ValueError("El producto debe estar en estado 'asignado'.")

    if producto.subastador_asignado != subastador_id:
        raise ValueError("El producto no está en el pool de este subastador.")

    existe = await db.scalar(
        select(ItemCatalogo).where(
            ItemCatalogo.catalogo == catalogo_id,
            ItemCatalogo.producto == producto_id,
        )
    )
    if existe:
        raise ValueError("El producto ya está en este catálogo.")

    item = ItemCatalogo(
        catalogo=catalogo_id,
        producto=producto_id,
        orden=orden,
        precio_base=producto.precio_base,
        comision=comision,
        subastado="no",
    )
    db.add(item)

    producto.estado_producto = "pendiente_confirmacion"

    datos_notif = {
        "idProducto": producto_id,
        "idCatalogo": catalogo_id,
        "precioBase": str(producto.precio_base),
        "comision": str(comision),
        "fecha": subasta.fecha.isoformat() if subasta.fecha else None,
        "hora": subasta.hora.isoformat() if subasta.hora else None,
        "lugar": subasta.ubicacion,
    }
    db.add(Notificacion(
        persona=producto.duenio,
        tipo="producto_aceptado",
        detalle=json.dumps(datos_notif),
    ))

    await db.commit()
    await ws_manager.send_to_user(producto.duenio, {"evento": "producto_aceptado", "datos": datos_notif})

    return {
        "identificador": item.identificador,
        "idProducto": producto_id,
        "descripcionProducto": producto.descripcion_completa,
        "precioBase": str(item.precio_base),
        "orden": item.orden,
        "comision": str(item.comision),
        "subastado": item.subastado,
        "iniciadoEn": item.iniciado_en,
        "finalizadoEn": item.finalizado_en,
    }


async def quitar_item_catalogo(
    db: AsyncSession, catalogo_id: int, item_id: int, subastador_id: int
) -> bool:
    catalogo = await db.get(Catalogo, catalogo_id)
    if catalogo is None:
        return False

    subasta = await db.get(Subasta, catalogo.subasta)
    if subasta is None or subasta.subastador != subastador_id:
        return False

    if subasta.estado != "programada":
        raise ValueError("Solo se puede quitar ítems mientras la subasta esté 'programada'.")

    item = await db.get(ItemCatalogo, item_id)
    if item is None or item.catalogo != catalogo_id:
        return False

    producto = await db.get(Producto, item.producto)
    if producto:
        producto.estado_producto = "asignado"

    await db.delete(item)
    await db.commit()
    return True


async def get_catalogo(
    db: AsyncSession, subasta_id: int, pagina: int, cantidad: int
) -> dict | None:
    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )
    if catalogo is None:
        return None

    count_q = select(func.count()).select_from(ItemCatalogo).where(
        ItemCatalogo.catalogo == catalogo.identificador
    )
    total = await db.scalar(count_q)
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(ItemCatalogo)
        .where(ItemCatalogo.catalogo == catalogo.identificador)
        .order_by(ItemCatalogo.orden)
        .offset(offset)
        .limit(cantidad)
    )
    items = result.scalars().all()

    items_data = []
    for item in items:
        producto = await db.get(Producto, item.producto)
        items_data.append({
            "identificador": item.identificador,
            "idProducto": item.producto,
            "descripcionProducto": producto.descripcion_completa if producto else None,
            "precioBase": str(item.precio_base),
            "orden": item.orden,
            "comision": str(item.comision),
            "subastado": item.subastado,
            "iniciadoEn": item.iniciado_en,
            "finalizadoEn": item.finalizado_en,
        })

    subasta = await db.get(Subasta, subasta_id)
    return {
        "identificador": catalogo.identificador,
        "descripcion": catalogo.descripcion,
        "idSubasta": catalogo.subasta,
        "idSubastador": subasta.subastador if subasta else None,
        "items": items_data,
    }


async def get_pool_productos(
    db: AsyncSession, subastador_id: int, pagina: int, cantidad: int, estado: str | None = None
) -> dict:
    query = select(Producto).where(Producto.subastador_asignado == subastador_id)
    count_q = select(func.count()).select_from(Producto).where(Producto.subastador_asignado == subastador_id)

    if estado:
        query = query.where(Producto.estado_producto == estado)
        count_q = count_q.where(Producto.estado_producto == estado)

    total = await db.scalar(count_q)
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        query.order_by(Producto.identificador.desc()).offset(offset).limit(cantidad)
    )
    productos = result.scalars().all()

    producto_ids = [p.identificador for p in productos]
    duenio_ids = [p.duenio for p in productos]

    fotos_por_producto: dict[int, list[dict]] = {}
    if producto_ids:
        fotos_result = await db.execute(
            select(Foto).where(Foto.producto.in_(producto_ids))
        )
        for f in fotos_result.scalars().all():
            fotos_por_producto.setdefault(f.producto, []).append({
                "identificador": f.identificador,
                "foto": f.foto,
                "orden": f.orden,
            })
        for fotos in fotos_por_producto.values():
            fotos.sort(key=lambda x: x["orden"])

    personas_por_id = {}
    if duenio_ids:
        personas_result = await db.execute(
            select(Persona).where(Persona.identificador.in_(duenio_ids))
        )
        personas_por_id = {p.identificador: p for p in personas_result.scalars().all()}

    datos = []
    for p in productos:
        persona = personas_por_id.get(p.duenio)
        datos.append({
            "identificador": p.identificador,
            "nombre": p.nombre,
            "descripcionCatalogo": p.descripcion_catalogo,
            "descripcionCompleta": p.descripcion_completa,
            "precioBase": str(p.precio_base),
            "moneda": p.moneda,
            "estadoProducto": p.estado_producto,
            "duenio": p.duenio,
            "publicadoPor": persona.nombre_usuario if persona else None,
            "fotos": fotos_por_producto.get(p.identificador, []),
        })

    return {
        "datos": datos,
        "meta": {"pagina": pagina, "cantidad": cantidad, "total": total, "total_paginas": total_paginas},
    }


def _serialize_subasta(s: Subasta) -> dict:
    return {
        "identificador": s.identificador,
        "nombre": s.nombre,
        "fecha": s.fecha,
        "hora": str(s.hora) if s.hora else None,
        "estado": s.estado,
        "idSubastador": s.subastador,
        "ubicacion": s.ubicacion,
        "capacidadAsistentes": s.capacidad_asistentes,
        "tieneDeposito": s.tiene_deposito,
        "seguridadPropia": s.seguridad_propia,
        "categoria": s.categoria,
        "moneda": s.moneda,
        "duracionItemMinutos": s.duracion_item_minutos,
        "fotoPrincipal": s.foto_principal,
    }
