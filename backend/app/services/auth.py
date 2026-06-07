import random
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Cliente, Duenio, Empleado, Subastador, Persona
from app.models.codigos_verificacion import CodigoVerificacion
from app.services import email as email_service

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

CODIGO_EXPIRACION_MINUTOS = 15
CODIGO_REENVIO_MINIMO_SEGUNDOS = 60


def save_upload(file_data: bytes, filename: str, subdir: str = "fotos") -> str:
    folder = UPLOADS_DIR / subdir
    folder.mkdir(exist_ok=True)
    path = folder / filename
    path.write_bytes(file_data)
    return str(path)


async def registrar_comprador(
    db: AsyncSession,
    documento: str,
    nombre: str,
    apellido: str,
    email: str,
    nombre_usuario: str,
    direccion: str,
    altura: str,
    localidad: str,
    ciudad: str,
    id_pais: int,
    foto_doc_frente: bytes,
    foto_doc_dorso: bytes,
    departamento: str | None = None,
    foto_perfil: bytes | None = None,
):
    existing = await db.scalar(
        select(Persona).where(
            (Persona.email == email) | (Persona.nombre_usuario == nombre_usuario)
        )
    )
    if existing is not None:
        return None  # evitar enumeración de usuarios

    url_frente = save_upload(
        foto_doc_frente, f"{email}_frente_{datetime.now(timezone.utc).timestamp():.0f}.jpg"
    )
    url_dorso = save_upload(
        foto_doc_dorso, f"{email}_dorso_{datetime.now(timezone.utc).timestamp():.0f}.jpg"
    )
    url_perfil = None
    if foto_perfil:
        url_perfil = save_upload(
            foto_perfil, f"{email}_perfil_{datetime.now(timezone.utc).timestamp():.0f}.jpg"
        )

    persona = Persona(
        documento=documento,
        nombre=nombre,
        apellido=apellido,
        email=email,
        nombre_usuario=nombre_usuario,
        direccion=direccion,
        altura=altura,
        departamento=departamento,
        localidad=localidad,
        ciudad=ciudad,
        estado="pendiente",
        url_foto_doc_frente=url_frente,
        url_foto_doc_dorso=url_dorso,
        url_foto_perfil=url_perfil,
    )
    db.add(persona)
    await db.flush()

    cliente = Cliente(
        identificador=persona.identificador,
        numero_pais=id_pais,
        admitido=None,
        categoria=None,
        verificador=1,  # Midnight Lace
    )
    db.add(cliente)
    await db.commit()
    return persona.identificador


async def get_persona_id_por_email(db: AsyncSession, email: str) -> int | None:
    persona = await db.scalar(select(Persona).where(Persona.email == email))
    return persona.identificador if persona else None


async def cliente_ya_verificado(db: AsyncSession, persona_id: int) -> bool:
    cliente = await db.get(Cliente, persona_id)
    if cliente is None:
        return False
    return cliente.admitido is not None


def _generar_codigo() -> str:
    return f"{random.randint(0, 999999):06d}"


async def _crear_codigo(db: AsyncSession, persona_id: int, tipo: str) -> str:
    await db.execute(
        update(CodigoVerificacion)
        .where(
            CodigoVerificacion.persona == persona_id,
            CodigoVerificacion.tipo == tipo,
            CodigoVerificacion.usado == "no",
        )
        .values(usado="si")
    )

    codigo = _generar_codigo()
    ahora = datetime.now(timezone.utc)
    codigo_row = CodigoVerificacion(
        persona=persona_id,
        codigo=codigo,
        tipo=tipo,
        creado_en=ahora,
        expira_en=ahora + timedelta(minutes=CODIGO_EXPIRACION_MINUTOS),
        usado="no",
    )
    db.add(codigo_row)
    await db.commit()
    return codigo


async def _obtener_codigo_valido(
    db: AsyncSession, persona_id: int, codigo: str, tipo: str
) -> CodigoVerificacion | None:
    ahora = datetime.now(timezone.utc)
    return await db.scalar(
        select(CodigoVerificacion).where(
            CodigoVerificacion.persona == persona_id,
            CodigoVerificacion.codigo == codigo,
            CodigoVerificacion.tipo == tipo,
            CodigoVerificacion.usado == "no",
            CodigoVerificacion.expira_en > ahora,
        )
    )


async def verificar_cliente(db: AsyncSession, persona_id: int) -> dict:
    """Verificación aleatoria. Retorna dict con aprobado y codigo si aprobado."""
    cliente = await db.get(Cliente, persona_id)
    persona = await db.get(Persona, persona_id)
    if cliente is None:
        raise ValueError("Cliente no encontrado.")

    if persona.email == "fedeabeledo01@gmail.com":
        aprobado = True
    elif persona.email == "fedeabeledo02@gmail.com":
        aprobado = False
    else:
        aprobado = random.random() < 0.70

    if aprobado:
        categorias = ["comun", "especial", "plata", "oro", "platino"]
        pesos = [0.35, 0.30, 0.20, 0.10, 0.05]
        categoria = random.choices(categorias, weights=pesos, k=1)[0]
        cliente.admitido = "si"
        cliente.categoria = categoria

        codigo = await _crear_codigo(db, persona_id, "registro")
        await db.commit()
        return {"aprobado": True, "codigo": codigo, "categoria": categoria}
    else:
        cliente.admitido = "no"
        cliente.categoria = "comun"

        persona = await db.get(Persona, persona_id)
        if persona:
            persona.estado = "inactivo"

        await db.commit()
        return {"aprobado": False, "codigo": None, "categoria": "comun"}


async def confirmar_cuenta(
    db: AsyncSession, codigo: str, clave: str, tipo: str
) -> dict | None:
    """Confirma registro (tipo='registro') o recuperacion de clave (tipo='recuperacion')."""
    codigo_row = await db.scalar(
        select(CodigoVerificacion).where(
            CodigoVerificacion.codigo == codigo,
            CodigoVerificacion.tipo == tipo,
        )
    )

    if codigo_row is None:
        return {"error": "CODIGO_INVALIDO"}

    ahora = datetime.now(timezone.utc)

    if codigo_row.usado == "si":
        return {"error": "CODIGO_USADO"}

    if codigo_row.expira_en < ahora:
        return {"error": "CODIGO_EXPIRADO"}

    persona = await db.get(Persona, codigo_row.persona)
    if persona is None:
        return {"error": "CODIGO_INVALIDO"}

    codigo_row.usado = "si"

    if tipo == "registro":
        if persona.estado == "pendiente":
            cliente = await db.get(Cliente, persona.identificador)
            if cliente is None or cliente.admitido != "si":
                return {"error": "CLIENTE_NO_ADMITIDO"}
            persona.estado = "activo"
        elif persona.estado != "activo":
            return {"error": "CLIENTE_INACTIVO"}
    else:  # recuperacion
        if persona.estado != "activo":
            return {"error": "CLIENTE_INACTIVO"}

    persona.hash_contrasenia = hash_password(clave)

    await db.execute(
        update(CodigoVerificacion)
        .where(
            CodigoVerificacion.persona == persona.identificador,
            CodigoVerificacion.tipo == tipo,
            CodigoVerificacion.usado == "no",
        )
        .values(usado="si")
    )

    await db.commit()

    return await _build_login_response(db, persona.identificador, persona.email, persona.nombre)


async def login(db: AsyncSession, email: str, clave: str) -> dict | None:
    persona = await db.scalar(select(Persona).where(Persona.email == email))
    if persona is None or persona.hash_contrasenia is None:
        return None

    if not verify_password(clave, persona.hash_contrasenia):
        return None

    if persona.estado != "activo":
        return None

    return await _build_login_response(db, persona.identificador, persona.email, persona.nombre)


async def renovar_token(db: AsyncSession, refresh_token: str) -> dict | None:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        return None

    if payload.get("type") != "refresh":
        return None

    persona_id = int(payload.get("sub"))
    persona = await db.get(Persona, persona_id)
    if persona is None or persona.estado != "activo":
        return None

    return await _build_login_response(db, persona_id, persona.email, persona.nombre)


async def cambiar_clave(db: AsyncSession, persona_id: int, clave_actual: str, clave_nueva: str) -> bool:
    persona = await db.get(Persona, persona_id)
    if persona is None or persona.hash_contrasenia is None:
        return False

    if not verify_password(clave_actual, persona.hash_contrasenia):
        return False

    persona.hash_contrasenia = hash_password(clave_nueva)
    await db.commit()
    return True


async def recuperar_clave(db: AsyncSession, email: str) -> bool:
    """Genera código de recuperación si el email existe. Retorna False si no existe."""
    persona = await db.scalar(select(Persona).where(Persona.email == email))
    if persona is None or persona.estado != "activo":
        return False

    codigo = await _crear_codigo(db, persona.identificador, "recuperacion")
    await email_service.send_email(email, "recuperacion", codigo=codigo)
    return True


async def reenviar_codigo(db: AsyncSession, email: str, tipo: str) -> dict:
    """Reenvía código. Retorna dict con info de rate limit."""
    persona = await db.scalar(select(Persona).where(Persona.email == email))

    if persona is None:
        return {"existe": False, "rate_limit": False}

    ahora = datetime.now(timezone.utc)
    ultimo_codigo = await db.scalar(
        select(CodigoVerificacion)
        .where(
            CodigoVerificacion.persona == persona.identificador,
            CodigoVerificacion.tipo == tipo,
        )
        .order_by(CodigoVerificacion.creado_en.desc())
    )

    if ultimo_codigo and (ahora - ultimo_codigo.creado_en).total_seconds() < CODIGO_REENVIO_MINIMO_SEGUNDOS:
        segundos_restantes = CODIGO_REENVIO_MINIMO_SEGUNDOS - int((ahora - ultimo_codigo.creado_en).total_seconds())
        return {"existe": True, "rate_limit": True, "segundos_restantes": segundos_restantes}

    nuevo_codigo = await _crear_codigo(db, persona.identificador, tipo)
    await email_service.send_email(email, tipo, codigo=nuevo_codigo)
    return {"existe": True, "rate_limit": False}


async def _build_login_response(
    db: AsyncSession, persona_id: int, email: str, nombre: str
) -> dict:
    roles = []
    if await db.scalar(select(Cliente).where(Cliente.identificador == persona_id)):
        roles.append("comprador")
    if await db.scalar(select(Duenio).where(Duenio.identificador == persona_id)):
        roles.append("duenio")
    if await db.scalar(select(Subastador).where(Subastador.identificador == persona_id)):
        roles.append("subastador")
    if await db.scalar(select(Empleado).where(Empleado.identificador == persona_id)):
        roles.append("empleado")

    from app.models.multas import Multa

    multa_impaga = await db.scalar(
        select(Multa).where(
            Multa.cliente == persona_id,
            Multa.pagada == "no",
            Multa.fecha_vencimiento > datetime.now(timezone.utc),
        )
    )
    tiene_multa = multa_impaga is not None

    access_token = create_access_token(
        {
            "sub": persona_id,
            "email": email,
            "nombre": nombre,
            "roles": roles,
            "multaImpaga": tiene_multa,
        }
    )
    refresh_token = create_refresh_token({"sub": persona_id})

    return {
        "token_acceso": access_token,
        "token_renovacion": refresh_token,
        "roles": roles,
        "multa_impaga": tiene_multa,
    }
