import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def send(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict[str, Any], channel: str | None = None) -> None:
        if channel and channel in self.subscriptions:
            recipients = self.subscriptions[channel]
        else:
            recipients = self.active_connections

        for websocket in recipients:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

    def subscribe(self, websocket: WebSocket, channel: str) -> None:
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(websocket)

    def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                channel = message.get("channel")
                if channel:
                    manager.subscribe(websocket, channel)

            elif message.get("type") == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(websocket, channel)

            elif message.get("type") == "ping":
                await manager.send({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_price_update(prices: dict[str, float]) -> None:
    await manager.broadcast(
        {
            "type": "price_update",
            "data": prices,
        }
    )


async def broadcast_new_signal(signal: dict[str, Any]) -> None:
    await manager.broadcast(
        {
            "type": "new_signal",
            "data": signal,
        }
    )


async def broadcast_whale_alert(transaction: dict[str, Any]) -> None:
    await manager.broadcast(
        {
            "type": "whale_alert",
            "data": transaction,
        }
    )


async def broadcast_collector_status(status: dict[str, Any]) -> None:
    await manager.broadcast(
        {
            "type": "collector_status",
            "data": status,
        }
    )
