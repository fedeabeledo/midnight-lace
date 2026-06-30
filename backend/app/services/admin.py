import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clientes import Cliente
from app.models.medios_pago import (
    ChequeCertificado,
    CuentaBancaria,
    MedioDePago,
    TarjetaCredito,
)
from app.models.productos import Foto, Producto
from app.models.multas import Multa
from app.models.personas import Persona, Empleado
from app.models.subastadores import Subastador
from app.services.notificaciones import crear_y_push


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


def _serializar_persona_minima(persona: Persona) -> dict:
    return {
        "identificador": persona.identificador,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "email": persona.email,
    }


async def _detalle_medio(db: AsyncSession, medio: MedioDePago) -> dict | None:
    if medio.tipo == "cuentaBancaria":
        cuenta = await db.scalar(
            select(CuentaBancaria).where(CuentaBancaria.medio_pago == medio.identificador)
        )
        if cuenta:
            return {
                "nombreBanco": cuenta.nombre_banco,
                "numeroCuenta": cuenta.numero_cuenta,
                "idPais": cuenta.pais,
            }
    if medio.tipo == "tarjetaCredito":
        tarjeta = await db.scalar(
            select(TarjetaCredito).where(TarjetaCredito.medio_pago == medio.identificador)
        )
        if tarjeta:
            return {
                "ultimosCuatroDigitos": tarjeta.ultimos_cuatro_digitos,
                "nombreTitular": tarjeta.nombre_titular,
                "fechaVencimiento": tarjeta.fecha_vencimiento.isoformat() if tarjeta.fecha_vencimiento else None,
                "red": tarjeta.red,
                "esInternacional": tarjeta.es_internacional,
            }
    if medio.tipo == "chequeCertificado":
        cheque = await db.scalar(
            select(ChequeCertificado).where(ChequeCertificado.medio_pago == medio.identificador)
        )
        if cheque:
            return {
                "montoGarantizado": str(cheque.monto_garantizado),
                "montoDisponible": str(cheque.monto_disponible),
                "fechaEntrega": cheque.fecha_entrega.isoformat() if cheque.fecha_entrega else None,
            }
    return None




async def listar_medios_pago(
    db: AsyncSession,
    pagina: int,
    cantidad: int,
    verificado: str | None = None,
) -> dict:
    filtros = [MedioDePago.activo == "si"]
    if verificado is not None:
        filtros.append(MedioDePago.verificado == verificado)

    total = await db.scalar(select(func.count()).select_from(MedioDePago).where(*filtros))
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1
    offset = (pagina - 1) * cantidad

    result = await db.execute(
        select(MedioDePago, Persona)
        .join(Persona, Persona.identificador == MedioDePago.cliente)
        .where(*filtros)
        .order_by(MedioDePago.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )

    datos = []
    for medio, persona in result.all():
        datos.append({
            "identificador": medio.identificador,
            "tipo": medio.tipo,
            "moneda": medio.moneda,
            "verificado": medio.verificado,
            "activo": medio.activo,
            "cliente": _serializar_persona_minima(persona),
            "detalle": await _detalle_medio(db, medio),
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


async def listar_productos_admin(
    db: AsyncSession,
    pagina: int,
    cantidad: int,
    estado: str | None = None,
) -> dict:
    filtros = []
    if estado is not None:
        filtros.append(Producto.estado_producto == estado)

    total = await db.scalar(select(func.count()).select_from(Producto).where(*filtros))
    total_paginas = math.ceil(total / cantidad) if total > 0 else 1
    offset = (pagina - 1) * cantidad

    result = await db.execute(
        select(Producto, Persona)
        .join(Persona, Persona.identificador == Producto.duenio)
        .where(*filtros)
        .order_by(Producto.identificador.desc())
        .offset(offset)
        .limit(cantidad)
    )
    filas = result.all()
    producto_ids = [producto.identificador for producto, _ in filas]

    fotos_por_producto: dict[int, list[dict]] = {}
    if producto_ids:
        fotos_result = await db.execute(select(Foto).where(Foto.producto.in_(producto_ids)))
        for foto in fotos_result.scalars().all():
            fotos_por_producto.setdefault(foto.producto, []).append({
                "identificador": foto.identificador,
                "foto": foto.foto,
                "orden": foto.orden,
            })

    datos = []
    for producto, persona in filas:
        datos.append({
            "identificador": producto.identificador,
            "nombre": producto.nombre,
            "fecha": producto.fecha.isoformat() if producto.fecha else None,
            "descripcionCatalogo": producto.descripcion_catalogo,
            "descripcionCompleta": producto.descripcion_completa,
            "precioBase": str(producto.precio_base),
            "moneda": producto.moneda,
            "estadoProducto": producto.estado_producto,
            "declaracionPropiedad": producto.declaracion_propiedad,
            "duenio": _serializar_persona_minima(persona),
            "fotos": sorted(
                fotos_por_producto.get(producto.identificador, []),
                key=lambda item: item["orden"],
            ),
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
        await crear_y_push(db, cliente_id, "cuenta_verificada", {
            "idCliente": cliente_id,
            "categoria": resultado.get("categoria") or categoria,
            "aprobado": True,
        })
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
