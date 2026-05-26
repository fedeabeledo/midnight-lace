import math
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    MedioDePago,
    CuentaBancaria,
    TarjetaCredito,
    ChequeCertificado,
)


async def listar_medios(
    db: AsyncSession, cliente_id: int, pagina: int, cantidad: int
) -> dict:
    total = await db.scalar(
        select(func.count()).select_from(MedioDePago).where(
            MedioDePago.cliente == cliente_id
        )
    )
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1

    offset = (pagina - 1) * cantidad
    result = await db.execute(
        select(MedioDePago)
        .where(MedioDePago.cliente == cliente_id)
        .order_by(MedioDePago.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    medios = result.scalars().all()

    datos = []
    for m in medios:
        datos.append(await _serializar_medio(db, m))

    return {
        "datos": datos,
        "meta": {
            "pagina": pagina,
            "cantidad": cantidad,
            "total": total,
            "total_paginas": total_paginas,
        },
    }


async def crear_medio(
    db: AsyncSession,
    cliente_id: int,
    tipo: str,
    moneda: str,
    detalle: dict,
) -> dict:
    medio = MedioDePago(
        cliente=cliente_id,
        tipo=tipo,
        moneda=moneda,
        verificado="no",
        activo="si",
    )
    db.add(medio)
    await db.flush()

    if tipo == "cuentaBancaria":
        db.add(CuentaBancaria(
            medio_pago=medio.identificador,
            nombre_banco=detalle["nombre_banco"],
            numero_cuenta=detalle["numero_cuenta"],
            pais=detalle.get("id_pais"),
        ))
    elif tipo == "tarjetaCredito":
        db.add(TarjetaCredito(
            medio_pago=medio.identificador,
            ultimos_cuatro_digitos=detalle["ultimos_cuatro_digitos"],
            nombre_titular=detalle["nombre_titular"],
            fecha_vencimiento=detalle["fecha_vencimiento"],
            red=detalle.get("red"),
            es_internacional=detalle.get("es_internacional", "no"),
        ))
    elif tipo == "chequeCertificado":
        db.add(ChequeCertificado(
            medio_pago=medio.identificador,
            monto_garantizado=detalle["monto_garantizado"],
            monto_disponible=detalle["monto_disponible"],
            fecha_entrega=detalle["fecha_entrega"],
        ))

    await db.commit()
    return await _serializar_medio(db, medio)


async def desactivar_medio(
    db: AsyncSession, medio_id: int, cliente_id: int
) -> bool:
    medio = await db.get(MedioDePago, medio_id)
    if medio is None or medio.cliente != cliente_id:
        return False
    medio.activo = "no"
    await db.commit()
    return True


async def verificar_medio(db: AsyncSession, medio_id: int, empleado_id: int) -> dict | None:
    medio = await db.get(MedioDePago, medio_id)
    if medio is None:
        return None

    medio.verificado = "si"

    if medio.tipo == "chequeCertificado":
        result = await db.execute(
            select(ChequeCertificado).where(ChequeCertificado.medio_pago == medio_id)
        )
        cheque = result.scalar_one_or_none()
        if cheque:
            cheque.verificado_por = empleado_id

    await db.commit()
    return await _serializar_medio(db, medio)


async def _serializar_medio(db: AsyncSession, medio: MedioDePago) -> dict:
    detalle = None

    if medio.tipo == "cuentaBancaria":
        result = await db.execute(
            select(CuentaBancaria).where(CuentaBancaria.medio_pago == medio.identificador)
        )
        cb = result.scalar_one_or_none()
        if cb:
            detalle = {
                "nombreBanco": cb.nombre_banco,
                "numeroCuenta": cb.numero_cuenta,
                "idPais": cb.pais,
            }

    elif medio.tipo == "tarjetaCredito":
        result = await db.execute(
            select(TarjetaCredito).where(TarjetaCredito.medio_pago == medio.identificador)
        )
        tc = result.scalar_one_or_none()
        if tc:
            detalle = {
                "ultimosCuatroDigitos": tc.ultimos_cuatro_digitos,
                "nombreTitular": tc.nombre_titular,
                "fechaVencimiento": tc.fecha_vencimiento.isoformat() if tc.fecha_vencimiento else None,
                "red": tc.red,
                "esInternacional": tc.es_internacional,
            }

    elif medio.tipo == "chequeCertificado":
        result = await db.execute(
            select(ChequeCertificado).where(ChequeCertificado.medio_pago == medio.identificador)
        )
        ch = result.scalar_one_or_none()
        if ch:
            detalle = {
                "montoGarantizado": float(ch.monto_garantizado),
                "montoDisponible": float(ch.monto_disponible),
                "fechaEntrega": ch.fecha_entrega.isoformat(),
            }

    return {
        "identificador": medio.identificador,
        "tipo": medio.tipo,
        "moneda": medio.moneda,
        "verificado": medio.verificado,
        "activo": medio.activo,
        "detalle": detalle,
    }
