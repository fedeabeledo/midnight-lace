import random
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Cliente, Duenio, Empleado, Subastador, Persona

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


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
        foto_doc_frente, f"{email}_frente_{datetime.utcnow().timestamp():.0f}.jpg"
    )
    url_dorso = save_upload(
        foto_doc_dorso, f"{email}_dorso_{datetime.utcnow().timestamp():.0f}.jpg"
    )
    url_perfil = None
    if foto_perfil:
        url_perfil = save_upload(
            foto_perfil, f"{email}_perfil_{datetime.utcnow().timestamp():.0f}.jpg"
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


async def verificar_cliente(db: AsyncSession, persona_id: int) -> str | None:
    """Verificación aleatoria. Retorna token de confirmación si aprobado, None si rechazado."""
    cliente = await db.get(Cliente, persona_id)
    if cliente is None:
        raise ValueError("Cliente no encontrado.")

    # Random approval (70% chance)
    aprobado = random.random() < 0.70

    if aprobado:
        categorias = ["comun", "especial", "plata", "oro", "platino"]
        pesos = [0.35, 0.30, 0.20, 0.10, 0.05]
        categoria = random.choices(categorias, weights=pesos, k=1)[0]
        cliente.admitido = "si"
        cliente.categoria = categoria

        token = create_access_token(
            {"sub": persona_id, "type": "confirmation"},
            expires_delta=timedelta(hours=24),
            token_type="confirmation",
        )
        await db.commit()
        return token
    else:
        cliente.admitido = "no"
        cliente.categoria = "comun"

        persona = await db.get(Persona, persona_id)
        if persona:
            persona.estado = "inactivo"

        await db.commit()
        return None


async def confirmar_cuenta(
    db: AsyncSession, token: str, clave: str
) -> dict | None:
    """Confirma la cuenta (registro inicial o recuperacion de clave)."""
    try:
        payload = decode_token(token)
    except Exception:
        return None

    if payload.get("type") != "confirmation":
        return None

    persona_id = int(payload.get("sub"))
    persona = await db.get(Persona, persona_id)
    if persona is None:
        return None

    if persona.estado == "pendiente":
        cliente = await db.get(Cliente, persona_id)
        if cliente is None or cliente.admitido != "si":
            return None
        persona.estado = "activo"

    elif persona.estado != "activo":
        return None

    persona.hash_contrasenia = hash_password(clave)
    await db.commit()

    return await _build_login_response(db, persona_id, persona.email, persona.nombre)


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


async def recuperar_clave(db: AsyncSession, email: str):
    """Siempre retorna success para evitar enumeración de usuarios."""
    persona = await db.scalar(select(Persona).where(Persona.email == email))
    if persona is not None:
        # En producción: enviar email con token de confirmación
        token = create_access_token(
            {"sub": persona.identificador},
            expires_delta=timedelta(hours=1),
            token_type="confirmation",
        )
        # Log para testing
        print(f"[RECUPERAR CLAVE] Token para {email}: {token}")
    # Siempre 202


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
