import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import hash_password
from app.models import (
    Cliente,
    Deposito,
    Empleado,
    Pais,
    Persona,
    Seguro,
    Subastador,
)


PAISES = [
    {"numero": 1, "nombre": "Afganistán", "nombre_corto": "AFG", "capital": "Kabul", "nacionalidad": "afgano/a", "idiomas": "Pastún, Darí"},
    {"numero": 2, "nombre": "Alemania", "nombre_corto": "DEU", "capital": "Berlín", "nacionalidad": "alemán/a", "idiomas": "Alemán"},
    {"numero": 3, "nombre": "Arabia Saudita", "nombre_corto": "SAU", "capital": "Riad", "nacionalidad": "saudí", "idiomas": "Árabe"},
    {"numero": 4, "nombre": "Australia", "nombre_corto": "AUS", "capital": "Camberra", "nacionalidad": "australiano/a", "idiomas": "Inglés"},
    {"numero": 5, "nombre": "Bélgica", "nombre_corto": "BEL", "capital": "Bruselas", "nacionalidad": "belga", "idiomas": "Neerlandés, Francés, Alemán"},
    {"numero": 6, "nombre": "Bolivia", "nombre_corto": "BOL", "capital": "Sucre", "nacionalidad": "boliviano/a", "idiomas": "Español, Quechua, Aimara"},
    {"numero": 7, "nombre": "Brasil", "nombre_corto": "BRA", "capital": "Brasilia", "nacionalidad": "brasileño/a", "idiomas": "Portugués"},
    {"numero": 8, "nombre": "Canadá", "nombre_corto": "CAN", "capital": "Ottawa", "nacionalidad": "canadiense", "idiomas": "Inglés, Francés"},
    {"numero": 9, "nombre": "Chile", "nombre_corto": "CHL", "capital": "Santiago", "nacionalidad": "chileno/a", "idiomas": "Español"},
    {"numero": 10, "nombre": "China", "nombre_corto": "CHN", "capital": "Pekín", "nacionalidad": "chino/a", "idiomas": "Chino Mandarín"},
    {"numero": 11, "nombre": "Colombia", "nombre_corto": "COL", "capital": "Bogotá", "nacionalidad": "colombiano/a", "idiomas": "Español"},
    {"numero": 12, "nombre": "Corea del Sur", "nombre_corto": "KOR", "capital": "Seúl", "nacionalidad": "surcoreano/a", "idiomas": "Coreano"},
    {"numero": 13, "nombre": "Ecuador", "nombre_corto": "ECU", "capital": "Quito", "nacionalidad": "ecuatoriano/a", "idiomas": "Español"},
    {"numero": 14, "nombre": "Egipto", "nombre_corto": "EGY", "capital": "El Cairo", "nacionalidad": "egipcio/a", "idiomas": "Árabe"},
    {"numero": 15, "nombre": "España", "nombre_corto": "ESP", "capital": "Madrid", "nacionalidad": "español/a", "idiomas": "Español"},
    {"numero": 16, "nombre": "Estados Unidos", "nombre_corto": "USA", "capital": "Washington D.C.", "nacionalidad": "estadounidense", "idiomas": "Inglés"},
    {"numero": 17, "nombre": "Francia", "nombre_corto": "FRA", "capital": "París", "nacionalidad": "francés/a", "idiomas": "Francés"},
    {"numero": 18, "nombre": "India", "nombre_corto": "IND", "capital": "Nueva Delhi", "nacionalidad": "indio/a", "idiomas": "Hindi, Inglés"},
    {"numero": 19, "nombre": "Italia", "nombre_corto": "ITA", "capital": "Roma", "nacionalidad": "italiano/a", "idiomas": "Italiano"},
    {"numero": 20, "nombre": "Japón", "nombre_corto": "JPN", "capital": "Tokio", "nacionalidad": "japonés/a", "idiomas": "Japonés"},
    {"numero": 21, "nombre": "México", "nombre_corto": "MEX", "capital": "Ciudad de México", "nacionalidad": "mexicano/a", "idiomas": "Español"},
    {"numero": 22, "nombre": "Países Bajos", "nombre_corto": "NLD", "capital": "Ámsterdam", "nacionalidad": "neerlandés/a", "idiomas": "Neerlandés"},
    {"numero": 23, "nombre": "Paraguay", "nombre_corto": "PRY", "capital": "Asunción", "nacionalidad": "paraguayo/a", "idiomas": "Español, Guaraní"},
    {"numero": 24, "nombre": "Perú", "nombre_corto": "PER", "capital": "Lima", "nacionalidad": "peruano/a", "idiomas": "Español"},
    {"numero": 25, "nombre": "Reino Unido", "nombre_corto": "GBR", "capital": "Londres", "nacionalidad": "británico/a", "idiomas": "Inglés"},
    {"numero": 26, "nombre": "Rusia", "nombre_corto": "RUS", "capital": "Moscú", "nacionalidad": "ruso/a", "idiomas": "Ruso"},
    {"numero": 27, "nombre": "Sudáfrica", "nombre_corto": "ZAF", "capital": "Pretoria", "nacionalidad": "sudafricano/a", "idiomas": "Inglés, Afrikáans, Zulú"},
    {"numero": 28, "nombre": "Suecia", "nombre_corto": "SWE", "capital": "Estocolmo", "nacionalidad": "sueco/a", "idiomas": "Sueco"},
    {"numero": 29, "nombre": "Uruguay", "nombre_corto": "URY", "capital": "Montevideo", "nacionalidad": "uruguayo/a", "idiomas": "Español"},
    {"numero": 30, "nombre": "Venezuela", "nombre_corto": "VEN", "capital": "Caracas", "nacionalidad": "venezolano/a", "idiomas": "Español"},
]


async def seed():
    async with async_session() as db:  # type: AsyncSession
        # Países
        for p in PAISES:
            existe = await db.get(Pais, p["numero"])
            if existe is None:
                db.add(Pais(**p))
        await db.flush()

        # Usuario Midnight Lace (ID 1) — empresa
        existe_ml = await db.get(Persona, 1)
        if existe_ml is None:
            db.add(
                Persona(
                    identificador=1,
                    documento="00000000",
                    nombre="Midnight",
                    apellido="Lace",
                    email="contacto@midnightlace.com",
                    nombre_usuario="midnight_lace",
                    direccion="Alsina",
                    altura="451",
                    localidad="CABA",
                    ciudad="CABA",
                    url_foto_doc_frente="n/a",
                    url_foto_doc_dorso="n/a",
                    estado="activo",
                    hash_contrasenia="n/a",
                )
            )
            await db.flush()

        existe_emp = await db.get(Empleado, 1)
        if existe_emp is None:
            db.add(Empleado(identificador=1, cargo="Midnight Lace"))
            await db.flush()

        existe_cli = await db.get(Cliente, 1)
        if existe_cli is None:
            db.add(Cliente(identificador=1, admitido="si", categoria="platino", verificador=1))
            await db.flush()

        # Resetear secuencia de personas después de insertar ID 1 manualmente
        await db.execute(text("SELECT setval('personas_identificador_seq', GREATEST(1, (SELECT COALESCE(MAX(identificador), 0) FROM personas)))"))

        await db.flush()

        # Subastador de prueba (para que verificacion-producto tenga a quien asignar)
        existe_sub = await db.scalar(select(Persona).where(Persona.email == "subastador@midnightlace.com"))
        if existe_sub is None:
            db.add(Persona(
                documento="11111111",
                nombre="Martillero",
                apellido="Público",
                email="subastador@midnightlace.com",
                nombre_usuario="subastador_ml",
                direccion="Corrientes",
                altura="800",
                localidad="CABA",
                ciudad="CABA",
                url_foto_doc_frente="n/a",
                url_foto_doc_dorso="n/a",
                estado="activo",
                hash_contrasenia=hash_password("sub123"),
            ))
            await db.flush()
            sub_persona = await db.scalar(select(Persona).where(Persona.email == "subastador@midnightlace.com"))
            db.add(Subastador(identificador=sub_persona.identificador, matricula="ML-001", region="CABA"))
            await db.flush()

        # Depósitos
        depos = await db.scalar(text("SELECT COUNT(*) FROM depositos"))
        if depos == 0:
            db.add_all([
                Deposito(nombre="Depósito Central", direccion="Av. Rivadavia 1500, CABA"),
                Deposito(nombre="Depósito Norte", direccion="Panamericana Km 35, Pilar"),
                Deposito(nombre="Depósito Sur", direccion="Av. Calchaquí 4500, Quilmes"),
                Deposito(nombre="Depósito Oeste", direccion="Ruta 7 Km 22, Luján"),
                Deposito(nombre="Depósito Puerto", direccion="Av. España 1200, Puerto Madero"),
            ])
            await db.flush()

        # Seguros (pólizas disponibles)
        segs = await db.scalar(text("SELECT COUNT(*) FROM seguros"))
        if segs == 0:
            db.add_all([
                Seguro(nro_poliza="POL-2026-001", compania="La Segunda Seguros", poliza_combinada="si", importe=500000),
                Seguro(nro_poliza="POL-2026-002", compania="Sancor Seguros", poliza_combinada="no", importe=750000),
                Seguro(nro_poliza="POL-2026-003", compania="Federación Patronal", poliza_combinada="si", importe=300000),
                Seguro(nro_poliza="POL-2026-004", compania="Zurich Seguros", poliza_combinada="no", importe=1000000),
                Seguro(nro_poliza="POL-2026-005", compania="Mapfre Seguros", poliza_combinada="si", importe=450000),
                Seguro(nro_poliza="POL-2026-006", compania="Allianz Seguros", poliza_combinada="no", importe=600000),
                Seguro(nro_poliza="POL-2026-007", compania="Galeno Seguros", poliza_combinada="si", importe=850000),
                Seguro(nro_poliza="POL-2026-008", compania="Prudential Seguros", poliza_combinada="no", importe=400000),
            ])
            await db.flush()

        await db.commit()
        print("Seed completado: 30 países + Midnight Lace + subastador + 5 depósitos + 8 seguros.")


if __name__ == "__main__":
    asyncio.run(seed())
