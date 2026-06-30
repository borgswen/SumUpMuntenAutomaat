from __future__ import annotations
from enum import Enum
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel, ValidationError

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


class CommandType(str, Enum):
    SELECT_AMOUNT = "SelectAmount"
    CONFIRM_SELECTION = "ConfirmSelection"
    START_PAYMENT = "StartPayment"
    CANCEL_PAYMENT = "CancelPayment"
    RESET_MACHINE = "ResetMachine"


class WebSocketMessage(BaseModel):
    type: str
    payload: dict[str, Any] | None = None


class WebSocketMessageParser:
    @staticmethod
    def parse(raw: Any) -> WebSocketMessage:
        if not isinstance(raw, dict):
            raise ValueError("WebSocket payload must be a JSON object")
        try:
            message = WebSocketMessage.parse_obj(raw)
        except ValidationError as exc:
            raise ValueError(f"Invalid WebSocket message: {exc}") from exc
        try:
            CommandType(message.type)
        except ValueError as exc:
            raise ValueError(f"Unknown command: {message.type}") from exc
        return message
