from typing import Any, Optional

import pandas as pd

from src.collectors.base import CollectorBase


class CoinalyzeCollector(CollectorBase):
    def __init__(self, api_key: Optional[str] = None, interval: int = 900):
        super().__init__(
            name="coinalyze",
            base_url="https://api.coinalyze.net/v1",
            api_key=api_key,
            rate_limit=40,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        headers = {"Auth-Token": self.api_key} if self.api_key else {}
        async with self._session() as client:
            try:
                response = await client.get("/open-interest", headers=headers)
                data["open_interest"] = response.json()
            except Exception:
                data["open_interest"] = []

            try:
                response = await client.get("/funding-rate", headers=headers)
                data["funding_rate"] = response.json()
            except Exception:
                data["funding_rate"] = []

            try:
                response = await client.get("/long-short-ratio-history", headers=headers)
                data["ls_ratio"] = response.json()
            except Exception:
                data["ls_ratio"] = []

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        for item in data.get("open_interest", [])[:20]:
            records.append(
                {
                    "timestamp": timestamp,
                    "symbol": item.get("symbol", "BTC"),
                    "exchange": item.get("exchange", ""),
                    "oi_value": item.get("value"),
                    "oi_change": item.get("changePercent"),
                }
            )

        for item in data.get("funding_rate", [])[:20]:
            records.append(
                {
                    "timestamp": timestamp,
                    "symbol": item.get("symbol", "BTC"),
                    "exchange": item.get("exchange", ""),
                    "rate": item.get("rate"),
                    "predicted_rate": item.get("predictedRate"),
                }
            )

        for item in data.get("ls_ratio", [])[:20]:
            records.append(
                {
                    "timestamp": timestamp,
                    "symbol": item.get("symbol", "BTC"),
                    "exchange": item.get("exchange", ""),
                    "ratio": item.get("ratio", {}).get("longShortRatio"),
                    "long_pct": item.get("ratio", {}).get("long"),
                    "short_pct": item.get("ratio", {}).get("short"),
                }
            )

        return pd.DataFrame(records)


class FearGreedCollector(CollectorBase):
    def __init__(self, interval: int = 3600):
        super().__init__(
            name="fear_greed",
            base_url="https://api.alternative.me",
            rate_limit=10,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        async with self._get_client() as client:
            response = await client.get("/fng/?limit=1")
            return response.json()

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []

        if "data" in data:
            for item in data["data"]:
                records.append(
                    {
                        "timestamp": pd.Timestamp(int(item["timestamp"]), unit="s"),
                        "value": int(item["value"]),
                        "classification": item.get("value_classification", ""),
                    }
                )

        return pd.DataFrame(records)


class CryptoPanicCollector(CollectorBase):
    def __init__(self, api_key: Optional[str] = None, interval: int = 3600):
        super().__init__(
            name="cryptopanic",
            base_url="https://cryptopanic.com/api/v1",
            api_key=api_key,
            rate_limit=60,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        params = {"filter": "rising"}
        if self.api_key:
            params["auth_token"] = self.api_key

        async with self._get_client() as client:
            response = await client.get("/posts/", params=params)
            return response.json()

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "results" in data:
            for item in data["results"][:20]:
                records.append(
                    {
                        "timestamp": timestamp,
                        "source": item.get("source", {}).get("title", ""),
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "currencies": ",".join([c["code"] for c in item.get("currencies", [])]),
                        "votes": item.get("votes", {}),
                    }
                )

        return pd.DataFrame(records)


class WhaleAlertCollector(CollectorBase):
    def __init__(self, api_key: Optional[str] = None, interval: int = 900):
        super().__init__(
            name="whale_alert",
            base_url="https://api.whale-alert.io/v1",
            api_key=api_key,
            rate_limit=10,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with self._get_client() as client:
            response = await client.get(
                "/transactions", params={"min_value": 500000}, headers=headers
            )
            return response.json()

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        for tx in data.get("transactions", []):
            records.append(
                {
                    "timestamp": timestamp,
                    "symbol": tx.get("symbol", ""),
                    "from_addr": tx.get("from", {}).get("owner", ""),
                    "to_addr": tx.get("to", {}).get("owner", ""),
                    "amount": tx.get("amount"),
                    "usd_value": tx.get("usd_value"),
                    "from_owner": tx.get("from", {}).get("owner_type"),
                    "to_owner": tx.get("to", {}).get("owner_type"),
                }
            )

        return pd.DataFrame(records)


class MessariCollector(CollectorBase):
    def __init__(self, api_key: Optional[str] = None, interval: int = 86400):
        super().__init__(
            name="messari",
            base_url="https://api.messari.io",
            api_key=api_key,
            rate_limit=20,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with self._get_client() as client:
            try:
                symbols = ["BTC", "ETH", "SOL"]
                for symbol in symbols:
                    response = await client.get(
                        f"/api/v2/assets/{symbol}/metrics",
                        headers=headers,
                    )
                    data[symbol] = response.json()
            except Exception:
                pass

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        for symbol, item in data.items():
            if "data" in item:
                metrics = item["data"].get("market_data", {})
                records.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "price_usd": metrics.get("price_usd"),
                        "market_cap": metrics.get("market_cap_dominance"),
                        "volume": metrics.get("volume_usd_24h"),
                    }
                )

        return pd.DataFrame(records)
