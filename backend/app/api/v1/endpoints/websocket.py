"""
CivilInc WebSocket Hub
Real-time events: complaint created/updated, project updated,
forum activity, officer assignment, broadcast notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import asyncio
import logging

logger = logging.getLogger("civilinc.ws")
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections with room-based broadcasting."""

    def __init__(self):
        # user_id → WebSocket
        self._connections: dict[str, WebSocket] = {}
        # room → set of user_ids (e.g. "department:ROADS", "ward:Ward-42")
        self._rooms: dict[str, set[str]] = {}

    async def connect(self, ws: WebSocket, user_id: str, rooms: list[str] = None):
        await ws.accept()
        self._connections[user_id] = ws
        for room in (rooms or []):
            self._rooms.setdefault(room, set()).add(user_id)
        logger.info(f"WS connected: {user_id}")

    def disconnect(self, user_id: str):
        self._connections.pop(user_id, None)
        for room_members in self._rooms.values():
            room_members.discard(user_id)
        logger.info(f"WS disconnected: {user_id}")

    async def send_to_user(self, user_id: str, event: dict):
        ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_json(event)
            except Exception:
                self.disconnect(user_id)

    async def broadcast_to_room(self, room: str, event: dict, exclude: str = None):
        members = self._rooms.get(room, set()).copy()
        tasks = [
            self.send_to_user(uid, event)
            for uid in members if uid != exclude
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_all(self, event: dict, exclude: str = None):
        tasks = [
            ws.send_json(event)
            for uid, ws in self._connections.items()
            if uid != exclude
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @property
    def connected_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    rooms: Optional[str] = Query(None),  # comma-separated room names
):
    """
    WebSocket connection endpoint.
    Client connects with: ws://host/api/v1/ws?token=<jwt>&user_id=<uuid>&rooms=department:ROADS,ward:Ward-42
    """
    if not user_id:
        await ws.close(code=4001)
        return

    # Validate JWT in production — simplified here
    room_list = rooms.split(",") if rooms else []
    room_list.append(f"user:{user_id}")  # personal room

    await manager.connect(ws, user_id, room_list)
    try:
        # Send connection ack
        await ws.send_json({
            "type": "connected",
            "payload": {"user_id": user_id, "rooms": room_list, "connected": manager.connected_count}
        })

        # Keep alive loop
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_json(), timeout=30.0)
                # Handle ping
                if data.get("type") == "ping":
                    await ws.send_json({"type": "pong", "ts": data.get("ts")})
                # Handle client-sent events (future: chat, typing indicators)
            except asyncio.TimeoutError:
                # Send server-side heartbeat
                await ws.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WS error for {user_id}: {e}")
        manager.disconnect(user_id)


async def emit_event(event_type: str, payload: dict, room: str = None, user_id: str = None):
    """
    Utility called by service layer to push real-time events.
    Usage:
        await emit_event("complaint_created", {...}, room="department:ROADS")
        await emit_event("assignment", {...}, user_id="officer-uuid")
    """
    event = {"type": event_type, "payload": payload}
    if user_id:
        await manager.send_to_user(user_id, event)
    elif room:
        await manager.broadcast_to_room(room, event)
    else:
        await manager.broadcast_all(event)
