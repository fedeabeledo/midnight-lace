import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ws_manager
from app.models import Empleado, Notificacion, Persona


async def crear_y_push(db: AsyncSession, user_id: int, tipo: str, datos: dict, commit: bool = True) -> Notificacion:
    notif = Notificacion(persona=user_id, tipo=tipo, detalle=json.dumps(datos))
    db.add(notif)
    if commit:
        await db.commit()
        await db.refresh(notif)
    await ws_manager.send_to_user(user_id, {"evento": tipo, "datos": datos})
    return notif


async def push_to_empleados(db: AsyncSession, tipo: str, datos: dict) -> None:
    result = await db.execute(
        select(Empleado.identificador)
        .join(Persona, Persona.identificador == Empleado.identificador)
        .where(Persona.estado == "activo")
    )
    empleados = result.scalars().all()
    for empleado_id in empleados:
        db.add(Notificacion(persona=empleado_id, tipo=tipo, detalle=json.dumps(datos)))
    await db.commit()

    for empleado_id in empleados:
        await ws_manager.send_to_user(empleado_id, {"evento": tipo, "datos": datos})
