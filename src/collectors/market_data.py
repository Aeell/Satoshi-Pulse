import logging
from typing import Any

import pandas as pd

from src.collectors.base import CollectorBase

logger = logging.getLogger(__name__)


class CoinGeckoCollector(CollectorBase):
    def __init__(self, api_key: str | None = None, interval: int = 300):
        super().__init__(
            name="coingecko",
            base_url="https://api.coingecko.com/api/v3",
            api_key=api_key,
            rate_limit=10,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        data["simple"] = await self._get(
            "/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana,dogecoin,ripple,cardano",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
        )
        data["global"] = await self._get("/global")
        data["trending"] = await self._get("/search/trending")
        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "simple" in data and data["simple"]:
            for coin_id, price_data in data["simple"].items():
                records.append(
                    {
                        "timestamp": timestamp,
                        "symbol": coin_id.upper(),
                        "price_usd": price_data.get("usd"),
                        "change_24h": price_data.get("usd_24h_change"),
                    }
                )

        return pd.DataFrame(records)


class CoinMarketCapCollector(CollectorBase):
    def __init__(self, api_key: str | None = None, interval: int = 3600):
        super().__init__(
            name="coinmarketcap",
            base_url="https://pro-api.coinmarketcap.com",
            api_key=api_key,
            rate_limit=60,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        headers = {"X-CMC_PRO_API_KEY": self.api_key}
        data = {}
        async with self._session() as client:
            response = await client.get(
                "/v1/cryptocurrency/listings/latest",
                headers=headers,
                params={"limit": 50},
            )
            data["listings"] = response.json()

            response = await client.get(
                "/v1/global-metrics/quotes/latest",
                headers=headers,
            )
            data["global"] = response.json()

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "listings" in data:
            for item in data["listings"].get("data", []):
                records.append(
                    {
                        "timestamp": timestamp,
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "price_usd": item.get("quote", {}).get("USD", {}).get("price"),
                        "market_cap": item.get("quote", {}).get("USD", {}).get("market_cap"),
                        "volume_24h": item.get("quote", {}).get("USD", {}).get("volume_24h"),
                        "rank": item.get("cmc_rank"),
                    }
                )

        return pd.DataFrame(records)


class CCXTCollector(CollectorBase):
    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: str | None = None,
        api_secret: str | None = None,
        interval: int = 60,
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self._exchange = None
        super().__init__(
            name=f"ccxt_{exchange_id}",
            base_url="",
            rate_limit=1200,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        try:
            import ccxt.async_support as ccxt_async
        except ImportError:
            logger.warning("CCXT not installed, skipping exchange data")
            return {}

        exchange_class = getattr(ccxt_async, self.exchange_id, None)
        if not exchange_class:
            logger.warning(f"Exchange {self.exchange_id} not supported")
            return {}

        exchange = exchange_class(
            {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
            }
        )
        try:
            await exchange.load_markets()
            ticker_data = await exchange.fetch_tickers(["BTC/USDT", "ETH/USDT", "SOL/USDT"])
            ohlcv_data = await exchange.fetch_ohlcv("BTC/USDT", "1m", limit=100)

            return {
                "tickers": ticker_data,
                "ohlcv": ohlcv_data,
            }

        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} fetch error: {e}")
            return {}
        finally:
            await exchange.close()

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "tickers" in data and data["tickers"]:
            for symbol, ticker in data["tickers"].items():
                if "/USDT" not in symbol:
                    continue
                records.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol.replace("/USDT", ""),
                        "exchange": self.exchange_id,
                        "last": ticker.get("last"),
                        "bid": ticker.get("bid"),
                        "ask": ticker.get("ask"),
                        "volume": ticker.get("quoteVolume"),
                        "change_24h": ticker.get("percentage"),
                    }
                )

        if "ohlcv" in data and data["ohlcv"]:
            for candle in data["ohlcv"]:
                records.append(
                    {
                        "timestamp": pd.Timestamp(candle[0], unit="ms"),
                        "symbol": "BTC",
                        "exchange": self.exchange_id,
                        "timeframe": "1m",
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                    }
                )

        return pd.DataFrame(records)

    async def _get_client(self) -> None:  # type: ignore[override]
        return None
