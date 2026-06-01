import math
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Asistente,
    Catalogo,
    ChequeCertificado,
    Cliente,
    ItemCatalogo,
    MedioDePago,
    Multa,
    Producto,
    Pujo,
    Subasta,
)


async def crear_puja(
    db: AsyncSession,
    subasta_id: int,
    item_id: int,
    comprador_id: int,
    importe: Decimal,
    medio_pago_id: int,
) -> dict:
    # 1. Verificar subasta existe y está abierta
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."},
        )
    if subasta.estado != "abierta":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "PUJA_ITEM_INACTIVO", "mensaje": "La subasta no está abierta."},
        )

    # 2. Verificar item existe y pertenece a la subasta
    item = await db.get(ItemCatalogo, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Ítem no encontrado."},
        )
    catalogo = await db.get(Catalogo, item.catalogo)
    if catalogo is None or catalogo.subasta != subasta_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Ítem no pertenece a esta subasta."},
        )

    # 3. Verificar item activo (es el turno actual)
    if item.subastado == "si":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "PUJA_ITEM_INACTIVO", "mensaje": "El ítem ya fue subastado."},
        )

    # 4. Verificar asistencia (conectado por WS)
    asistente = await db.scalar(
        select(Asistente).where(
            Asistente.cliente == comprador_id,
            Asistente.subasta == subasta_id,
        )
    )
    if asistente is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "SIN_PERMISO",
                "mensaje": "Debe conectarse a la subasta por WebSocket antes de pujar.",
            },
        )

    # 5. Verificar categoría
    cliente = await db.get(Cliente, comprador_id)
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo": "SIN_PERMISO", "mensaje": "Usuario no es un comprador."},
        )

    categorias_orden = ["comun", "especial", "plata", "oro", "platino"]
    categoria_cliente_idx = categorias_orden.index(cliente.categoria) if cliente.categoria else 0
    categoria_subasta_idx = categorias_orden.index(subasta.categoria) if subasta.categoria else 0

    if categoria_cliente_idx < categoria_subasta_idx:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "CATEGORIA_INSUFICIENTE",
                "mensaje": f"Su categoría ({cliente.categoria}) no permite participar en subastas de categoría {subasta.categoria}.",
            },
        )

    # 6. Verificar medio de pago verificado
    medio_pago = await db.get(MedioDePago, medio_pago_id)
    if medio_pago is None or medio_pago.cliente != comprador_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo": "SIN_PERMISO", "mensaje": "Medio de pago no encontrado."},
        )
    if medio_pago.verificado != "si":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "MEDIO_PAGO_NO_VERIFICADO",
                "mensaje": "El medio de pago debe estar verificado.",
            },
        )
    if medio_pago.activo != "si":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo": "MEDIO_PAGO_INACTIVO", "mensaje": "El medio de pago está desactivado."},
        )

    # 7. Verificar cheque certificado
    if medio_pago.tipo == "chequeCertificado":
        cheque = await db.get(ChequeCertificado, medio_pago_id)
        if cheque and cheque.monto_disponible < importe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "codigo": "PUJA_CHEQUE_SIN_FONDOS",
                    "mensaje": f"El cheque certificado no tiene fondos suficientes. Disponible: {cheque.monto_disponible}",
                },
            )

    # 8. Verificar sin multas impagas
    multa_impaga = await db.scalar(
        select(Multa).where(
            Multa.cliente == comprador_id,
            Multa.pagada == "no",
        )
    )
    if multa_impaga:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "MULTA_IMPAGA",
                "mensaje": "Tiene multas impagas. Debe pagarlas antes de pujar.",
            },
        )

    # 9. Obtener última oferta
    ultima_puja = await db.scalar(
        select(Pujo)
        .where(Pujo.item == item_id)
        .order_by(Pujo.importe.desc())
    )

    precio_base = item.precio_base
    ultima_oferta = ultima_puja.importe if ultima_puja else Decimal("0")

    # 10. Calcular límites
    # Si no hay pujas previas, la primera puja debe ser al menos el precio base
    if ultima_oferta == 0:
        puja_minima = precio_base
    else:
        puja_minima = ultima_oferta + (precio_base * Decimal("0.01"))

    # Límite máximo solo para comun, especial, plata
    puja_maxima = None
    if subasta.categoria in ["comun", "especial", "plata"]:
        if ultima_oferta == 0:
            puja_maxima = precio_base + (precio_base * Decimal("0.20"))
        else:
            puja_maxima = ultima_oferta + (precio_base * Decimal("0.20"))

    # 11. Validar monto
    if importe < puja_minima:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "PUJA_MONTO_INSUFICIENTE",
                "mensaje": f"El monto debe ser al menos {puja_minima}.",
                "pujaMinima": str(puja_minima),
                "pujaMaxima": str(puja_maxima) if puja_maxima else None,
            },
        )

    if puja_maxima and importe > puja_maxima:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "PUJA_MONTO_EXCEDIDO",
                "mensaje": f"El monto no puede superar {puja_maxima}.",
                "pujaMinima": str(puja_minima),
                "pujaMaxima": str(puja_maxima),
            },
        )

    # 12. Crear puja
    puja = Pujo(
        asistente=asistente.identificador,
        item=item_id,
        importe=importe,
        ganador="no",
    )
    db.add(puja)
    await db.commit()
    await db.refresh(puja)

    # 13. Enriquecer respuesta
    producto = await db.get(Producto, item.producto)

    return {
        "identificador": puja.identificador,
        "idCliente": comprador_id,
        "idItem": item_id,
        "importe": str(puja.importe),
        "ganador": puja.ganador,
        "realizadaEn": puja.realizada_en.isoformat() if puja.realizada_en else None,
        "subasta": {
            "identificador": subasta.identificador,
            "nombre": subasta.nombre,
            "fecha": subasta.fecha.isoformat() if subasta.fecha else None,
            "categoria": subasta.categoria,
            "moneda": subasta.moneda,
        },
        "producto": {
            "identificador": producto.identificador if producto else None,
            "descripcionCatalogo": producto.descripcion_catalogo if producto else None,
        },
    }


async def historial_pujas(
    db: AsyncSession,
    subasta_id: int,
    item_id: int,
    pagina: int,
    cantidad: int,
) -> dict:
    # Verificar item pertenece a subasta
    item = await db.get(ItemCatalogo, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Ítem no encontrado."},
        )
    catalogo = await db.get(Catalogo, item.catalogo)
    if catalogo is None or catalogo.subasta != subasta_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Ítem no pertenece a esta subasta."},
        )

    # Contar total
    total = await db.scalar(
        select(func.count())
        .select_from(Pujo)
        .where(Pujo.item == item_id)
    )
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    # Obtener pujas
    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(Pujo)
        .where(Pujo.item == item_id)
        .order_by(Pujo.realizada_en.asc())
        .offset(offset)
        .limit(cantidad)
    )
    pujas = result.scalars().all()

    # Enriquecer respuesta
    subasta = await db.get(Subasta, subasta_id)
    producto = await db.get(Producto, item.producto)

    datos = []
    for puja in pujas:
        asistente = await db.get(Asistente, puja.asistente)
        datos.append({
            "identificador": puja.identificador,
            "idCliente": asistente.cliente if asistente else None,
            "idItem": puja.item,
            "importe": str(puja.importe),
            "ganador": puja.ganador,
            "realizadaEn": puja.realizada_en.isoformat() if puja.realizada_en else None,
            "subasta": {
                "identificador": subasta.identificador if subasta else None,
                "nombre": subasta.nombre if subasta else None,
                "fecha": subasta.fecha.isoformat() if subasta and subasta.fecha else None,
                "categoria": subasta.categoria if subasta else None,
                "moneda": subasta.moneda if subasta else None,
            },
            "producto": {
                "identificador": producto.identificador if producto else None,
                "descripcionCatalogo": producto.descripcion_catalogo if producto else None,
            },
        })

    return {
        "datos": datos,
        "meta": {
            "pagina": pagina,
            "cantidad": cantidad,
            "total": total,
            "totalPaginas": total_paginas,
        },
    }


async def item_actual(db: AsyncSession, subasta_id: int) -> dict:
    # Verificar subasta
    subasta = await db.get(Subasta, subasta_id)
    if subasta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Subasta no encontrada."},
        )

    # Obtener catálogo
    catalogo = await db.scalar(
        select(Catalogo).where(Catalogo.subasta == subasta_id)
    )
    if catalogo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Catálogo no encontrado."},
        )

    # Obtener item actual (primero no subastado)
    item = await db.scalar(
        select(ItemCatalogo)
        .where(
            ItemCatalogo.catalogo == catalogo.identificador,
            ItemCatalogo.subastado != "si",
        )
        .order_by(ItemCatalogo.orden.asc())
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "No hay ítems activos en esta subasta."},
        )

    # Obtener mejor oferta
    ultima_puja = await db.scalar(
        select(Pujo)
        .where(Pujo.item == item.identificador)
        .order_by(Pujo.importe.desc())
    )

    precio_base = item.precio_base
    ultima_oferta = ultima_puja.importe if ultima_puja else Decimal("0")

    # Calcular límites
    if ultima_oferta == 0:
        puja_minima = precio_base
    else:
        puja_minima = ultima_oferta + (precio_base * Decimal("0.01"))

    puja_maxima = None
    if subasta.categoria in ["comun", "especial", "plata"]:
        if ultima_oferta == 0:
            puja_maxima = precio_base + (precio_base * Decimal("0.20"))
        else:
            puja_maxima = ultima_oferta + (precio_base * Decimal("0.20"))

    # Obtener producto
    producto = await db.get(Producto, item.producto)

    # Calcular finalizaEn (por ahora null, se implementa con WebSockets)
    finaliza_en = None
    if item.iniciado_en and subasta.duracion_item_minutos:
        from datetime import timedelta
        finaliza_en = item.iniciado_en + timedelta(minutes=subasta.duracion_item_minutos)

    return {
        "idItem": item.identificador,
        "descripcionProducto": producto.descripcion_catalogo if producto else None,
        "precioBase": str(precio_base),
        "mejorOferta": str(ultima_oferta) if ultima_oferta > 0 else None,
        "pujaMinima": str(puja_minima),
        "pujaMaxima": str(puja_maxima) if puja_maxima else None,
        "finalizaEn": finaliza_en.isoformat() if finaliza_en else None,
    }
