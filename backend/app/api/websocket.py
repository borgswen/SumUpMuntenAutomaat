from __future__ import annotations
from typing import Any

from fastapi import WebSocket

from app.core.events import Event


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, event: Event) -> None:
        payload = event.to_dict()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except RuntimeError:
                self.active_connections.remove(connection)


class WebSocketMessageParser:
    @staticmethod
    def parse(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("WebSocket payload must be a JSON object")
        return raw
