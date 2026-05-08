import json
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.websocket.manager import ws_manager

logger = structlog.get_logger()

ws_router = APIRouter()


@ws_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str = Query(default=""),
):
    is_admin = False

    if token:
        payload = decode_token(token)
        if payload and payload.get("role") == "admin":
            is_admin = True

    await ws_manager.connect(websocket, client_id, is_admin=is_admin)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await ws_manager.send_personal(client_id, {"type": "pong"})

            elif msg_type == "subscribe_stats" and is_admin:
                await ws_manager.broadcast_stats()

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.debug("WebSocket disconnected", client_id=client_id)
