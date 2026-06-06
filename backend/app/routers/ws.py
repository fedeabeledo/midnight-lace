from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decode_token
from app.core.ws_manager import ws_manager
from app.models import (
    Asistente,
    Cliente,
    Multa,
    Persona,
    Subasta,
)

router = APIRouter(tags=["WebSocket"])


async def _authenticate_ws(websocket: WebSocket) -> dict | None:
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        await websocket.close(code=4001)
        return None

    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=4001)
        return None

    if payload.get("type") != "access":
        await websocket.close(code=4001)
        return None

    sub = payload.get("sub")
    if sub is None:
        await websocket.close(code=4001)
        return None

    user_id = int(sub)
    multa_impaga = payload.get("multaImpaga", False)

    async with async_session() as db:
        persona = await db.get(Persona, user_id)
        if persona is None or persona.estado != "activo":
            await websocket.close(code=4001)
            return None

        cliente = await db.scalar(
            select(Cliente).where(Cliente.identificador == user_id)
        )
        if cliente is None:
            await websocket.close(code=4001)
            return None

        if not multa_impaga:
            multa = await db.scalar(
                select(Multa).where(
                    Multa.cliente == user_id,
                    Multa.pagada == "no",
                )
            )
            if multa:
                await websocket.close(code=4003)
                return None

    return {
        "identificador": user_id,
        "multa_impaga": multa_impaga,
    }


@router.websocket("/v1/ws/subastas/{idSubasta}")
async def ws_subasta(websocket: WebSocket, idSubasta: int):
    await websocket.accept()

    user = await _authenticate_ws(websocket)
    if user is None:
        return

    user_id = user["identificador"]

    async with async_session() as db:
        subasta = await db.get(Subasta, idSubasta)
        if subasta is None:
            await websocket.close(code=4004)
            return

        if subasta.estado != "abierta":
            await websocket.close(code=4004)
            return

        asistente = await db.scalar(
            select(Asistente).where(
                Asistente.cliente == user_id,
                Asistente.subasta == idSubasta,
            )
        )

        if asistente is None:
            max_postor = await db.scalar(
                select(func.max(Asistente.numero_postor)).where(
                    Asistente.subasta == idSubasta
                )
            )
            numero_postor = (max_postor or 0) + 1

            asistente = Asistente(
                cliente=user_id,
                subasta=idSubasta,
                numero_postor=numero_postor,
            )
            db.add(asistente)
            await db.commit()
            await db.refresh(asistente)
        else:
            numero_postor = asistente.numero_postor

    await ws_manager.connect(
        websocket,
        idSubasta,
        user_id,
        asistente.identificador,
        numero_postor,
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
