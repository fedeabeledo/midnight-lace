import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session
from app.models import Cliente
from app.models.personas import Persona
from app.core.security import hash_password

async def main():
    usuarios = [
        {
            "username": "comprador1",
            "email": "comprador1@gmail.com",
            "nombre": "Pedro",
            "apellido": "Pujador",
            "documento": "33444555"
        },
        {
            "username": "comprador2",
            "email": "comprador2@gmail.com",
            "nombre": "Lucía",
            "apellido": "Ofertas",
            "documento": "55666777"
        }
    ]

    async with async_session() as db:
        for u in usuarios:
            # Check if user already exists
            res = await db.execute(
                select_persona_by_username_or_email(u["username"], u["email"])
            )
            existing = res.scalars().first()
            if existing:
                print(f"Usuario {u['username']} ya existe (ID: {existing.identificador}), actualizando clave a Password123")
                # Ensure it is a client and has category 'comun'
                cliente = await db.get(Cliente, existing.identificador)
                if not cliente:
                    cliente = Cliente(
                        identificador=existing.identificador,
                        numero_pais=1,
                        admitido="si",
                        categoria="comun",
                        verificador=1
                    )
                    db.add(cliente)
                else:
                    cliente.admitido = "si"
                    cliente.categoria = "comun"
                existing.estado = "activo"
                existing.hash_contrasenia = hash_password("Password123")
                continue

            persona = Persona(
                documento=u["documento"],
                nombre=u["nombre"],
                apellido=u["apellido"],
                email=u["email"],
                nombre_usuario=u["username"],
                hash_contrasenia=hash_password("Password123"),
                estado="activo",
                direccion="Calle Falsa 123",
                altura="123",
                codigo_postal="1425",
                localidad="CABA",
                ciudad="Buenos Aires",
                url_foto_doc_frente="uploads/placeholder.jpg",
                url_foto_doc_dorso="uploads/placeholder.jpg"
            )
            db.add(persona)
            await db.flush()

            cliente = Cliente(
                identificador=persona.identificador,
                numero_pais=1,
                admitido="si",
                categoria="comun",
                verificador=1
            )
            db.add(cliente)
            print(f"Creado usuario {u['username']} con ID: {persona.identificador}")
        
        await db.commit()

def select_persona_by_username_or_email(username: str, email: str):
    from sqlalchemy import select
    return select(Persona).where((Persona.nombre_usuario == username) | (Persona.email == email))

if __name__ == '__main__':
    asyncio.run(main())
