import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.core.ws_manager import ws_manager
from app.models import (
    Asistente,
    Multa,
    Notificacion,
    Persona,
    Pujo,
    RegistroDeSubasta,
    Subasta,
)
from app.services.pagos import procesar_pago


async def _token_fresco(db: AsyncSession, persona_id: int) -> dict:
    persona = await db.get(Persona, persona_id)
    multa = await db.scalar(
        select(Multa).where(
            Multa.cliente == persona_id,
            Multa.pagada == "no",
            Multa.fecha_vencimiento > datetime.now(timezone.utc),
        )
    )
    tiene_multa = multa is not None
    access_token = create_access_token({
        "sub": persona_id,
        "email": persona.email,
        "nombre": persona.nombre,
        "roles": [],
        "multaImpaga": tiene_multa,
    })
    refresh_token = create_refresh_token({"sub": persona_id})
    return {
        "tokenAcceso": access_token,
        "tokenRenovacion": refresh_token,
        "multaImpaga": tiene_multa,
    }


def _serializar_registro(r: RegistroDeSubasta) -> dict:
    return {
        "identificador": r.identificador,
        "subasta": r.subasta,
        "producto": r.producto,
        "importe": str(r.importe),
        "comision": str(r.comision),
        "costoEnvio": str(r.costo_envio),
        "moneda": r.moneda,
        "pagado": r.pagado,
        "retiraPersonalmente": r.retira_personalmente,
        "fechaPago": r.fecha_pago.isoformat() if r.fecha_pago else None,
        "fechaVencimiento": r.fecha_vencimiento.isoformat() if r.fecha_vencimiento else None,
    }


def _paginar(total: int, pagina: int, cantidad: int) -> dict:
    return {
        "pagina": pagina,
        "cantidad": cantidad,
        "total": total,
        "totalPaginas": math.ceil(total / cantidad) if total > 0 else 1,
    }


async def listar_subastas(db: AsyncSession, cliente_id: int, pagina: int, cantidad: int) -> dict:
    subq = select(Asistente.subasta).where(Asistente.cliente == cliente_id).distinct()
    total = await db.scalar(select(func.count()).select_from(subq.subquery()))
    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(Subasta)
        .where(Subasta.identificador.in_(subq))
        .order_by(Subasta.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    subastas = result.scalars().all()
    return {
        "datos": [
            {
                "identificador": s.identificador,
                "nombre": s.nombre,
                "fecha": s.fecha.isoformat() if s.fecha else None,
                "hora": s.hora.isoformat() if s.hora else None,
                "estado": s.estado,
                "categoria": s.categoria,
                "moneda": s.moneda,
            }
            for s in subastas
        ],
        "meta": _paginar(total, pagina, cantidad),
    }


async def listar_pujas(db: AsyncSession, cliente_id: int, pagina: int, cantidad: int, id_item: int | None) -> dict:
    base = (
        select(Pujo)
        .join(Asistente, Pujo.asistente == Asistente.identificador)
        .where(Asistente.cliente == cliente_id)
    )
    if id_item is not None:
        base = base.where(Pujo.item == id_item)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    offset = (pagina - 1) * cantidad
    result = await db.execute(base.order_by(Pujo.identificador.desc()).offset(offset).limit(cantidad))
    pujas = result.scalars().all()
    return {
        "datos": [
            {
                "identificador": p.identificador,
                "idItem": p.item,
                "importe": str(p.importe),
                "ganador": p.ganador,
                "realizadaEn": p.realizada_en.isoformat() if p.realizada_en else None,
            }
            for p in pujas
        ],
        "meta": _paginar(total, pagina, cantidad),
    }


async def listar_compras(db: AsyncSession, cliente_id: int, pagina: int, cantidad: int) -> dict:
    base = select(RegistroDeSubasta).where(RegistroDeSubasta.cliente == cliente_id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    offset = (pagina - 1) * cantidad
    result = await db.execute(base.order_by(RegistroDeSubasta.identificador.desc()).offset(offset).limit(cantidad))
    registros = result.scalars().all()
    return {
        "datos": [_serializar_registro(r) for r in registros],
        "meta": _paginar(total, pagina, cantidad),
    }


async def actualizar_retiro(db: AsyncSession, registro_id: int, cliente_id: int, retira_personalmente: bool) -> dict:
    registro = await db.get(RegistroDeSubasta, registro_id)
    if registro is None or registro.cliente != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Compra no encontrada."},
        )
    if registro.pagado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "YA_PAGADO", "mensaje": "La compra ya está pagada."},
        )
    registro.retira_personalmente = retira_personalmente
    await db.commit()
    return _serializar_registro(registro)


async def pagar_compra(db: AsyncSession, registro_id: int, cliente_id: int, medio_id: int) -> dict:
    registro = await db.get(RegistroDeSubasta, registro_id)
    if registro is None or registro.cliente != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Compra no encontrada."},
        )
    if registro.pagado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "YA_PAGADO", "mensaje": "La compra ya está pagada."},
        )
    now = datetime.now(timezone.utc)
    if registro.fecha_vencimiento and registro.fecha_vencimiento < now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "COMPRA_VENCIDA", "mensaje": "El plazo de pago venció."},
        )

    monto = registro.importe + registro.comision + registro.costo_envio

    try:
        await procesar_pago(db, cliente_id, medio_id, monto, registro.moneda)
    except HTTPException as e:
        if e.detail.get("codigo") == "PUJA_CHEQUE_SIN_FONDOS":
            importe_multa = registro.importe * Decimal("0.10")
            multa = Multa(
                cliente=cliente_id,
                registro_subasta=registro_id,
                importe=importe_multa,
                pagada="no",
                fecha_vencimiento=now + timedelta(hours=72),
            )
            db.add(multa)
            await db.flush()
            datos_multa = {
                "idMulta": multa.identificador,
                "idRegistroSubasta": registro_id,
                "importe": str(importe_multa),
            }
            db.add(Notificacion(persona=cliente_id, tipo="multa_generada", detalle=json.dumps(datos_multa)))
            await db.commit()
            await ws_manager.send_to_user(cliente_id, {"evento": "multa_generada", "datos": datos_multa})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"codigo": "PUJA_CHEQUE_SIN_FONDOS", "mensaje": "Fondos insuficientes. Se generó una multa.", "idMulta": multa.identificador},
            )
        raise

    registro.pagado = True
    registro.fecha_pago = now
    registro.medio_pago = medio_id
    datos_pago = {
        "idRegistroSubasta": registro_id,
        "importe": str(monto),
        "moneda": registro.moneda,
    }
    db.add(Notificacion(persona=cliente_id, tipo="compra_pagada", detalle=json.dumps(datos_pago)))
    await db.commit()
    await ws_manager.send_to_user(cliente_id, {"evento": "compra_pagada", "datos": datos_pago})

    tokens = await _token_fresco(db, cliente_id)
    return {
        "registro": _serializar_registro(registro),
        **tokens,
    }


async def listar_multas(db: AsyncSession, cliente_id: int, pagina: int, cantidad: int) -> dict:
    base = select(Multa).where(Multa.cliente == cliente_id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    offset = (pagina - 1) * cantidad
    result = await db.execute(base.order_by(Multa.identificador.desc()).offset(offset).limit(cantidad))
    multas = result.scalars().all()
    return {
        "datos": [
            {
                "identificador": m.identificador,
                "idRegistroSubasta": m.registro_subasta,
                "importe": str(m.importe),
                "pagada": m.pagada,
                "fechaEmision": m.fecha_emision.isoformat() if m.fecha_emision else None,
                "fechaVencimiento": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
            }
            for m in multas
        ],
        "meta": _paginar(total, pagina, cantidad),
    }


async def pagar_multa(db: AsyncSession, multa_id: int, cliente_id: int, medio_id: int) -> dict:
    multa = await db.get(Multa, multa_id)
    if multa is None or multa.cliente != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Multa no encontrada."},
        )
    if multa.pagada == "si":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "YA_PAGADO", "mensaje": "La multa ya está pagada."},
        )

    registro = await db.get(RegistroDeSubasta, multa.registro_subasta)
    moneda = registro.moneda if registro else "ARS"
    await procesar_pago(db, cliente_id, medio_id, multa.importe, moneda)

    multa.pagada = "si"
    datos_multa = {"idMulta": multa_id}
    db.add(Notificacion(persona=cliente_id, tipo="multa_pagada", detalle=json.dumps(datos_multa)))
    await db.commit()
    await ws_manager.send_to_user(cliente_id, {"evento": "multa_pagada", "datos": datos_multa})

    tokens = await _token_fresco(db, cliente_id)
    return {"idMulta": multa_id, **tokens}


async def obtener_metricas(db: AsyncSession, cliente_id: int) -> dict:
    total_pujas = await db.scalar(
        select(func.count()).select_from(Pujo)
        .join(Asistente, Pujo.asistente == Asistente.identificador)
        .where(Asistente.cliente == cliente_id)
    )
    pujas_ganadas = await db.scalar(
        select(func.count()).select_from(Pujo)
        .join(Asistente, Pujo.asistente == Asistente.identificador)
        .where(Asistente.cliente == cliente_id, Pujo.ganador == "si")
    )
    total_compras = await db.scalar(
        select(func.count()).select_from(RegistroDeSubasta)
        .where(RegistroDeSubasta.cliente == cliente_id)
    )
    compras_pagadas = await db.scalar(
        select(func.count()).select_from(RegistroDeSubasta)
        .where(RegistroDeSubasta.cliente == cliente_id, RegistroDeSubasta.pagado == True)
    )
    multas_impagas = await db.scalar(
        select(func.count()).select_from(Multa)
        .where(Multa.cliente == cliente_id, Multa.pagada == "no")
    )
    return {
        "totalPujas": total_pujas or 0,
        "pujasGanadas": pujas_ganadas or 0,
        "totalCompras": total_compras or 0,
        "comprasPagadas": compras_pagadas or 0,
        "multasImpagas": multas_impagas or 0,
    }


async def listar_notificaciones(
    db: AsyncSession, user_id: int, pagina: int, cantidad: int, leida: str | None
) -> dict:
    base = select(Notificacion).where(Notificacion.persona == user_id)
    if leida is not None:
        base = base.where(Notificacion.leida == leida)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    offset = (pagina - 1) * cantidad
    result = await db.execute(base.order_by(Notificacion.identificador.desc()).offset(offset).limit(cantidad))
    notifs = result.scalars().all()
    return {
        "datos": [
            {
                "identificador": n.identificador,
                "tipo": n.tipo,
                "leida": n.leida,
                "creadaEn": n.creada_en.isoformat() if n.creada_en else None,
                "detalle": json.loads(n.detalle) if n.detalle else {},
            }
            for n in notifs
        ],
        "meta": _paginar(total, pagina, cantidad),
    }


async def marcar_leida(db: AsyncSession, notif_id: int, user_id: int, leida: bool) -> dict:
    notif = await db.get(Notificacion, notif_id)
    if notif is None or notif.persona != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "NO_ENCONTRADO", "mensaje": "Notificación no encontrada."},
        )
    notif.leida = "si" if leida else "no"
    await db.commit()
    return {
        "identificador": notif.identificador,
        "tipo": notif.tipo,
        "leida": notif.leida,
        "creadaEn": notif.creada_en.isoformat() if notif.creada_en else None,
        "detalle": json.loads(notif.detalle) if notif.detalle else {},
    }


async def verificar_vencimientos(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Multa).where(Multa.pagada == "no", Multa.fecha_vencimiento < now)
    )
    multas_vencidas = result.scalars().all()

    bloqueados = set()
    for multa in multas_vencidas:
        if multa.cliente in bloqueados:
            continue
        persona = await db.get(Persona, multa.cliente)
        if persona and persona.estado == "activo":
            persona.estado = "inactivo"
            bloqueados.add(multa.cliente)
            datos = {"idCliente": multa.cliente}
            db.add(Notificacion(persona=multa.cliente, tipo="cuenta_bloqueada", detalle=json.dumps(datos)))

    if bloqueados:
        await db.commit()
        for cliente_id in bloqueados:
            await ws_manager.send_to_user(cliente_id, {"evento": "cuenta_bloqueada", "datos": {"idCliente": cliente_id}})

    return {"bloqueados": len(bloqueados)}
