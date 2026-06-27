import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ws_manager
from app.models import Notificacion


async def crear_y_push(db: AsyncSession, user_id: int, tipo: str, datos: dict, commit: bool = True) -> Notificacion:
    notif = Notificacion(persona=user_id, tipo=tipo, detalle=json.dumps(datos))
    db.add(notif)
    if commit:
        await db.commit()
        await db.refresh(notif)
    await ws_manager.send_to_user(user_id, {"evento": tipo, "datos": datos})
    return notif
