from typing import Any

import pandas as pd

from src.collectors.base import CollectorBase


class DefiLlamaCollector(CollectorBase):
    def __init__(self, interval: int = 21600):
        super().__init__(
            name="defillama",
            base_url="https://api.llama.fi",
            rate_limit=30,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        async with self._session() as client:
            response = await client.get("/protocols")
            data["protocols"] = response.json()

            response = await client.get("/overview/dexs")
            data["dexs"] = response.json()

            response = await client.get("/stablecoins")
            data["stablecoins"] = response.json()

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "protocols" in data:
            for protocol in data["protocols"][:50]:
                records.append(
                    {
                        "timestamp": timestamp,
                        "protocol": protocol.get("slug", ""),
                        "chain": protocol.get("chain", ""),
                        "tvl_usd": protocol.get("tvl", 0),
                    }
                )

        return pd.DataFrame(records)


class DexScreenerCollector(CollectorBase):
    def __init__(self, interval: int = 300):
        super().__init__(
            name="dexscreener",
            base_url="https://api.dexscreener.com",
            rate_limit=60,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        async with self._session() as client:
            response = await client.get("/latest/dex/search")
            data["search"] = response.json()

            response = await client.get("/token-boosts/top/v1")
            data["boosts"] = response.json()

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "search" in data and "pairs" in data["search"]:
            for pair in data["search"]["pairs"][:20]:
                records.append(
                    {
                        "timestamp": timestamp,
                        "pair_address": pair.get("pairAddress", ""),
                        "base_token": pair.get("baseToken", {}).get("symbol", ""),
                        "quote_token": pair.get("quoteToken", {}).get("symbol", ""),
                        "price_usd": pair.get("priceUsd"),
                        "liquidity": pair.get("liquidity", {}).get("usd"),
                        "volume_24h": pair.get("volume", {}).get("h24"),
                    }
                )

        return pd.DataFrame(records)
