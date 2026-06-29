import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clientes import Cliente
from app.models.multas import Multa
from app.models.personas import Persona, Empleado
from app.models.subastadores import Subastador


def _serializar_cliente(persona: Persona, cliente: Cliente) -> dict:
    return {
        "identificador": persona.identificador,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "email": persona.email,
        "estado": persona.estado,
        "admitido": cliente.admitido,
        "categoria": cliente.categoria,
    }


def _serializar_multa(m: Multa) -> dict:
    return {
        "identificador": m.identificador,
        "cliente": m.cliente,
        "importe": str(m.importe),
        "pagada": m.pagada,
        "fechaEmision": m.fecha_emision.isoformat() if m.fecha_emision else None,
        "fechaVencimiento": m.fecha_vencimiento.isoformat() if m.fecha_vencimiento else None,
    }


async def listar_clientes(
    db: AsyncSession,
    pagina: int,
    cantidad: int,
    admitido: str | None = None,
    categoria: str | None = None,
) -> dict:
    filtros = []
    if admitido is not None:
        filtros.append(Cliente.admitido == admitido)
    if categoria is not None:
        filtros.append(Cliente.categoria == categoria)

    total = await db.scalar(
        select(func.count()).select_from(Cliente).where(*filtros)
    )
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1
    offset = (pagina - 1) * cantidad

    result = await db.execute(
        select(Persona, Cliente)
        .join(Cliente, Cliente.identificador == Persona.identificador)
        .where(*filtros)
        .order_by(Persona.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    filas = result.all()

    return {
        "datos": [_serializar_cliente(p, c) for p, c in filas],
        "meta": {
            "pagina": pagina,
            "cantidad": cantidad,
            "total": total,
            "totalPaginas": total_paginas,
        },
    }


async def ver_cliente(db: AsyncSession, cliente_id: int) -> dict | None:
    result = await db.execute(
        select(Persona, Cliente)
        .join(Cliente, Cliente.identificador == Persona.identificador)
        .where(Persona.identificador == cliente_id)
    )
    fila = result.first()
    if fila is None:
        return None

    persona, cliente = fila
    data = _serializar_cliente(persona, cliente)

    multas_result = await db.execute(
        select(Multa).where(Multa.cliente == cliente_id).order_by(Multa.identificador.desc())
    )
    data["multas"] = [_serializar_multa(m) for m in multas_result.scalars().all()]
    return data


async def actualizar_cliente(
    db: AsyncSession, cliente_id: int, datos: dict
) -> dict | None:
    result = await db.execute(
        select(Persona, Cliente)
        .join(Cliente, Cliente.identificador == Persona.identificador)
        .where(Persona.identificador == cliente_id)
    )
    fila = result.first()
    if fila is None:
        return None

    persona, cliente = fila
    if datos.get("admitido") is not None:
        cliente.admitido = datos["admitido"]
    if datos.get("categoria") is not None:
        cliente.categoria = datos["categoria"]

    await db.commit()
    await db.refresh(persona)
    await db.refresh(cliente)
    return _serializar_cliente(persona, cliente)


async def listar_multas(
    db: AsyncSession, pagina: int, cantidad: int, pagada: str | None = None
) -> dict:
    filtros = []
    if pagada is not None:
        filtros.append(Multa.pagada == pagada)

    total = await db.scalar(
        select(func.count()).select_from(Multa).where(*filtros)
    )
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1
    offset = (pagina - 1) * cantidad

    result = await db.execute(
        select(Multa)
        .where(*filtros)
        .order_by(Multa.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    multas = result.scalars().all()

    return {
        "datos": [_serializar_multa(m) for m in multas],
        "meta": {
            "pagina": pagina,
            "cantidad": cantidad,
            "total": total,
            "totalPaginas": total_paginas,
        },
    }


async def verificar_cliente_admin(
    db: AsyncSession, cliente_id: int, aprobado: bool, categoria: str | None
) -> dict | None:
    from app.services import auth as auth_service
    from app.services import email as email_service
    persona = await db.get(Persona, cliente_id)
    if persona is None:
        return None
    resultado = await auth_service.verificar_cliente(db, cliente_id, aprobado, categoria)
    if resultado is None:
        return None
    if aprobado:
        await email_service.send_email(persona.email, "registro", codigo=resultado["codigo"])
    else:
        await email_service.send_email(
            persona.email, "rechazo",
            motivo="Tu solicitud no cumple los requisitos de verificación."
        )
    return resultado


async def verificar_producto_admin(
    db: AsyncSession, producto_id: int, aprobado: bool, motivo: str | None
) -> str | None:
    from app.services.productos import verificar_producto
    return await verificar_producto(db, producto_id, aprobado, motivo)


async def crear_subastador(db: AsyncSession, datos: dict) -> dict:
    persona = Persona(
        documento=datos["documento"],
        nombre=datos["nombre"],
        apellido=datos["apellido"],
        email=datos["email"],
        nombre_usuario=datos["nombre_usuario"],
        direccion="",
        altura="",
        localidad="",
        ciudad="",
        estado="activo",
        url_foto_doc_frente="n/a",
        url_foto_doc_dorso="n/a",
        hash_contrasenia=hash_password(datos["clave"]),
    )
    db.add(persona)
    await db.flush()

    db.add(Subastador(
        identificador=persona.identificador,
        matricula=datos.get("matricula"),
        region=datos.get("region"),
    ))
    await db.commit()
    await db.refresh(persona)

    return {
        "identificador": persona.identificador,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "email": persona.email,
        "estado": persona.estado,
    }
