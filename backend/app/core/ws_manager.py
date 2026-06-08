import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = defaultdict(list)
        self.conn_info: dict[int, dict] = {}
        self.item_timers: dict[int, asyncio.Task] = {}

    async def connect(
        self,
        websocket: WebSocket,
        subasta_id: int,
        user_id: int,
        asistente_id: int,
        numero_postor: int,
    ):
        self.active[subasta_id].append(websocket)
        self.conn_info[id(websocket)] = {
            "subasta_id": subasta_id,
            "user_id": user_id,
            "asistente_id": asistente_id,
            "numero_postor": numero_postor,
        }
        await self.send_personal(websocket, {
            "evento": "asistenciaConfirmada",
            "datos": {
                "numeroPostor": numero_postor,
                "idSubasta": subasta_id,
            },
        })

    def disconnect(self, websocket: WebSocket):
        info = self.conn_info.pop(id(websocket), None)
        if info:
            subasta_id = info["subasta_id"]
            if websocket in self.active[subasta_id]:
                self.active[subasta_id].remove(websocket)
            if not self.active[subasta_id]:
                del self.active[subasta_id]

    async def broadcast(self, subasta_id: int, message: dict):
        dead = []
        for ws in self.active.get(subasta_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

    def start_item_timer(self, subasta_id: int, task: asyncio.Task):
        self.cancel_item_timer(subasta_id)
        self.item_timers[subasta_id] = task

    def cancel_item_timer(self, subasta_id: int):
        existing = self.item_timers.pop(subasta_id, None)
        if existing and not existing.done():
            existing.cancel()

    def has_connections(self, subasta_id: int) -> bool:
        return bool(self.active.get(subasta_id))


ws_manager = ConnectionManager()
