import uuid
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from main import app
from app.websocket.manager import ws_manager
from app.core.security import decode_token
import structlog

logger = structlog.get_logger()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    token = websocket.query_params.get("token")
    is_admin = False

    if token:
        payload = decode_token(token)
        if payload and payload.get("role") == "admin":
            is_admin = True

    await ws_manager.connect(websocket, client_id, is_admin=is_admin)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await ws_manager.send_personal(client_id, {"type": "pong"})

                elif msg_type == "subscribe_stats" and is_admin:
                    # Send initial stats immediately
                    await ws_manager.broadcast_stats()

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info("WebSocket disconnected", client_id=client_id)


async def broadcast_document_status(doc_id: str, status: str, progress: int = 0):
    await ws_manager.broadcast_admin({
        "type": "document_status",
        "doc_id": doc_id,
        "status": status,
        "progress": progress,
    })


async def broadcast_new_chat():
    await ws_manager.broadcast_admin({
        "type": "new_chat",
        "online_users": ws_manager.online_count,
    })
