import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session
from app.models import Pujo, Asistente
from app.models.personas import Persona
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(Pujo))
        for p in res.scalars().all():
            asistente = await db.get(Asistente, p.asistente)
            nombre_usuario = None
            if asistente:
                persona = await db.get(Persona, asistente.cliente)
                if persona:
                    nombre_usuario = persona.nombre_usuario
            print(f"Puja ID: {p.identificador}, Importe: {p.importe}, Cliente ID: {asistente.cliente if asistente else None}, NombreUsuario: {nombre_usuario}")

if __name__ == '__main__':
    asyncio.run(main())
