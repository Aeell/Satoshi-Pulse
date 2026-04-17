import logging
from typing import Any

import httpx

from src.analysis.signal_generator import Signal, SignalType

logger = logging.getLogger(__name__)


class SignalBridge:
    def __init__(
        self,
        rpc_url: str = "http://localhost:8080",
        api_key: str = "",
        mode: str = "webhook",
    ):
        self.rpc_url = rpc_url
        self.api_key = api_key
        self.mode = mode

    async def send_signal_via_webhook(self, signal: Signal) -> bool:
        if signal.signal_type == SignalType.BUY:
            action = "buy"
        elif signal.signal_type == SignalType.SELL:
            action = "sell"
        else:
            return False

        payload = {
            "action": action,
            "pair": f"{signal.symbol}/USDT",
            "stop_loss": signal.stop_loss,
            "take_profit": signal.price_target,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rpc_url}/api/v1/webhook",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send signal to Freqtrade: {e}")
            return False

    async def send_signal_via_api(self, signal: Signal) -> bool:
        if (
            signal.signal_type == SignalType.CLOSE_LONG
            or signal.signal_type == SignalType.CLOSE_SHORT
        ):
            action = "exit"
        elif signal.signal_type == SignalType.BUY:
            action = "enter"
        elif signal.signal_type == SignalType.SELL:
            action = "enter"
        else:
            return False

        payload = {
            "reqid": signal.timestamp.isoformat(),
            "action": action,
            "side": "long"
            if signal.signal_type in [SignalType.BUY, SignalType.CLOSE_SHORT]
            else "short",
            "pair": f"{signal.symbol}/USDT",
            "enter_side": "long",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rpc_url}/api/v1/freqai/{signal.strategy}",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send signal to Freqtrade: {e}")
            return False

    async def send_signal(self, signal: Signal) -> bool:
        if self.mode == "webhook":
            return await self.send_signal_via_webhook(signal)
        else:
            return await self.send_signal_via_api(signal)

    async def get_open_positions(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.rpc_url}/api/v1/status",
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
        return []

    async def get_balance(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.rpc_url}/api/v1/balance",
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
        return {"total": 0.0, "free": 0.0}

    async def start_strategy(self, strategy_name: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rpc_url}/api/v1/start",
                    json={"strategy": strategy_name},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to start strategy: {e}")
            return False

    async def stop_strategy(self, strategy_name: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rpc_url}/api/v1/stop",
                    json={"strategy": strategy_name},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to stop strategy: {e}")
            return False
