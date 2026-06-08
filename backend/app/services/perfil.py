from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cliente, Persona, Pais


async def get_perfil(db: AsyncSession, persona_id: int) -> dict | None:
    persona = await db.get(Persona, persona_id)
    if persona is None:
        return None

    pais = None
    cliente = await db.get(Cliente, persona_id)
    if cliente and cliente.numero_pais:
        pais = await db.get(Pais, cliente.numero_pais)

    return {
        "identificador": persona.identificador,
        "documento": persona.documento,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "nombre_usuario": persona.nombre_usuario,
        "email": persona.email,
        "direccion": persona.direccion,
        "altura": persona.altura,
        "departamento": persona.departamento,
        "localidad": persona.localidad,
        "ciudad": persona.ciudad,
        "estado": persona.estado,
        "url_foto_doc_frente": persona.url_foto_doc_frente,
        "url_foto_doc_dorso": persona.url_foto_doc_dorso,
        "fecha_actualizacion_foto_dni": persona.fecha_actualizacion_foto_dni,
        "url_foto_perfil": persona.url_foto_perfil,
        "pais": {
            "numero": pais.numero,
            "nombre": pais.nombre,
            "nombre_corto": pais.nombre_corto,
            "capital": pais.capital,
            "nacionalidad": pais.nacionalidad,
            "idiomas": pais.idiomas,
        } if pais else None,
    }


async def update_perfil(
    db: AsyncSession,
    persona_id: int,
    **kwargs,
) -> dict | None:
    persona = await db.get(Persona, persona_id)
    if persona is None:
        return None

    updatable = [
        "nombre", "apellido", "email", "nombre_usuario",
        "direccion", "altura", "departamento", "localidad", "ciudad",
        "url_foto_perfil", "url_foto_doc_frente", "url_foto_doc_dorso",
    ]
    fotos_actualizadas = False

    for field in updatable:
        if field in kwargs and kwargs[field] is not None:
            setattr(persona, field, kwargs[field])
            if field in ("url_foto_doc_frente", "url_foto_doc_dorso"):
                fotos_actualizadas = True

    if "numero_pais" in kwargs and kwargs["numero_pais"] is not None:
        cliente = await db.get(Cliente, persona_id)
        if cliente:
            cliente.numero_pais = kwargs["numero_pais"]

    if fotos_actualizadas:
        persona.fecha_actualizacion_foto_dni = date.today()

    await db.commit()

    return await get_perfil(db, persona_id)
