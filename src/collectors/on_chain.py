from typing import Any

import pandas as pd

from src.collectors.base import CollectorBase


class CoinMetricsCollector(CollectorBase):
    """
    CoinMetrics Community API — free, no API key required.
    https://community-api.coinmetrics.io/v4
    """

    def __init__(self, interval: int = 86400):
        super().__init__(
            name="coinmetrics",
            base_url="https://community-api.coinmetrics.io/v4",
            rate_limit=6,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        data = {}
        async with self._session() as client:
            try:
                response = await client.get(
                    "/timeseries/asset-metrics",
                    params={
                        "assets": "btc,eth",
                        "metrics": "ActiveAddresses,TxCount,HashRate,NVTAdj,FeeTotNtv",
                        "limit_per_asset": 10,
                    },
                )
                data["metrics"] = response.json()
            except Exception as e:
                data["metrics"] = {"error": str(e), "data": []}

        return data

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []
        timestamp = pd.Timestamp.now()

        if "metrics" in data:
            for asset_data in data["metrics"].get("data", []):
                asset = asset_data.get("asset", "").upper()
                for metric in ["ActiveAddresses", "TxCount", "HashRate", "NVTAdj", "FeeTotNtv"]:
                    val = asset_data.get(metric)
                    if val is not None:
                        records.append(
                            {
                                "timestamp": timestamp,
                                "symbol": asset,
                                "metric_name": metric,
                                "metric_value": val,
                            }
                        )

        return pd.DataFrame(records)


class SantimentCollector(CollectorBase):
    """
    Santiment GraphQL API — requires API key (free tier available).
    https://app.santiment.net
    """

    def __init__(self, api_key: str | None = None, interval: int = 21600):
        super().__init__(
            name="santiment",
            base_url="https://api.santiment.net/graphql",
            api_key=api_key,
            rate_limit=10,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        if not self.api_key:
            return {}

        query = """
        {
            getMetric(metric: "active_addresses_24h") {
                timeseriesData(
                    slug: "bitcoin"
                    from: "utc_now-7d"
                    to: "utc_now"
                    interval: "1d"
                ) {
                    datetime
                    value
                }
            }
        }
        """
        headers = {"Authorization": f"Apikey {self.api_key}"}
        async with self._session() as client:
            response = await client.post(
                "",
                json={"query": query},
                headers=headers,
            )
            return response.json()

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        records = []

        try:
            ts_data = data.get("data", {}).get("getMetric", {}).get("timeseriesData", [])
            for point in ts_data:
                records.append(
                    {
                        "timestamp": pd.Timestamp(point["datetime"]),
                        "symbol": "BTC",
                        "metric_name": "active_addresses_24h",
                        "metric_value": point.get("value"),
                    }
                )
        except Exception:
            pass

        return pd.DataFrame(records)
