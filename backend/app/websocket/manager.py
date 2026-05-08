import json
from typing import Dict, Set
from fastapi import WebSocket
import structlog

logger = structlog.get_logger()


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.admin_connections: Set[str] = set()

    async def startup(self):
        logger.info("WebSocket manager started")

    async def shutdown(self):
        for client_id, ws in list(self.active_connections.items()):
            try:
                await ws.close()
            except Exception:
                logger.debug("WebSocket already closed on shutdown", client_id=client_id)
        self.active_connections.clear()

    async def connect(self, websocket: WebSocket, client_id: str, is_admin: bool = False):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if is_admin:
            self.admin_connections.add(client_id)
        logger.info("WebSocket connected", client_id=client_id, total=len(self.active_connections))

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.admin_connections.discard(client_id)

    async def send_personal(self, client_id: str, data: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                logger.warning("WebSocket send failed, disconnecting", client_id=client_id)
                self.disconnect(client_id)

    async def broadcast_admin(self, data: dict):
        message = json.dumps(data)
        disconnected = []
        for cid in list(self.admin_connections):
            ws = self.active_connections.get(cid)
            if ws:
                try:
                    await ws.send_text(message)
                except Exception:
                    logger.warning("WebSocket broadcast failed", client_id=cid)
                    disconnected.append(cid)

        for cid in disconnected:
            self.disconnect(cid)

    async def broadcast_stats(self):
        await self.broadcast_admin({
            "type": "stats",
            "online_users": len(self.active_connections),
            "admin_count": len(self.admin_connections),
        })

    async def broadcast_document_status(self, doc_id: str, status: str, progress: int = 0):
        await self.broadcast_admin({
            "type": "document_status",
            "doc_id": doc_id,
            "status": status,
            "progress": progress,
        })

    async def broadcast_new_chat(self):
        await self.broadcast_admin({
            "type": "new_chat",
            "online_users": self.online_count,
        })

    @property
    def online_count(self) -> int:
        return len(self.active_connections)


ws_manager = WebSocketManager()
