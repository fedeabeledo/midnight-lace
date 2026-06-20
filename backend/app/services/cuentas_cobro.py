import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cuentas_cobro import CuentaCobro


def _serializar(c: CuentaCobro) -> dict:
    return {
        "identificador": c.identificador,
        "nombreBanco": c.nombre_banco,
        "numeroCuenta": c.numero_cuenta,
        "moneda": c.moneda,
        "idPais": c.pais,
        "activa": c.activa,
    }


async def listar_cuentas(
    db: AsyncSession, duenio_id: int, pagina: int, cantidad: int
) -> dict:
    total = await db.scalar(
        select(func.count()).select_from(CuentaCobro).where(
            CuentaCobro.duenio == duenio_id,
            CuentaCobro.activa == "si",
        )
    )
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1
    offset = (pagina - 1) * cantidad

    result = await db.execute(
        select(CuentaCobro)
        .where(CuentaCobro.duenio == duenio_id, CuentaCobro.activa == "si")
        .order_by(CuentaCobro.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    cuentas = result.scalars().all()

    return {
        "datos": [_serializar(c) for c in cuentas],
        "meta": {
            "pagina": pagina,
            "cantidad": cantidad,
            "total": total,
            "totalPaginas": total_paginas,
        },
    }


async def crear_cuenta(
    db: AsyncSession, duenio_id: int, datos: dict
) -> dict:
    cuenta = CuentaCobro(
        duenio=duenio_id,
        nombre_banco=datos["nombre_banco"],
        numero_cuenta=datos["numero_cuenta"],
        moneda=datos["moneda"],
        pais=datos.get("id_pais"),
        activa="si",
    )
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    return _serializar(cuenta)


async def desactivar_cuenta(
    db: AsyncSession, cuenta_id: int, duenio_id: int
) -> bool:
    cuenta = await db.get(CuentaCobro, cuenta_id)
    if cuenta is None or cuenta.duenio != duenio_id or cuenta.activa == "no":
        return False
    cuenta.activa = "no"
    await db.commit()
    return True
