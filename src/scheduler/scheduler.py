import asyncio
import logging
from typing import Optional

import pandas as pd

from src.collectors.base import CollectorBase
from src.collectors.defi import DefiLlamaCollector, DexScreenerCollector
from src.collectors.derivatives import (
    CoinalyzeCollector,
    CryptoPanicCollector,
    FearGreedCollector,
    WhaleAlertCollector,
)
from src.collectors.market_data import CCXTCollector, CoinGeckoCollector, CoinMarketCapCollector
from src.collectors.on_chain import CoinMetricsCollector
from src.config.settings import get_settings
from src.storage.database import db
from src.storage.writer import persist_dataframe

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self.settings = get_settings()
        self._collectors: list[CollectorBase] = []
        self._running = False
        self._tasks: list[asyncio.Task] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_collector(self, collector: CollectorBase) -> None:
        self._collectors.append(collector)
        logger.info(f"Registered collector: {collector.name}")

    async def start(self) -> None:
        """Initialise DB, wire collectors, and run them concurrently."""
        # Ensure DB tables exist
        db.init()
        await db.create_tables()

        self._running = True
        self._collectors = self._build_collectors()

        logger.info(f"Scheduler starting with {len(self._collectors)} collectors")

        self._tasks = [
            asyncio.create_task(self._run_collector(collector)) for collector in self._collectors
        ]

        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        logger.info("Stopping scheduler …")
        self._running = False

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        for collector in self._collectors:
            await collector.close()

        await db.close()
        logger.info("Scheduler stopped")

    def get_status(self) -> pd.DataFrame:
        return pd.DataFrame([c.get_status() for c in self._collectors])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_collectors(self) -> list[CollectorBase]:
        """Instantiate all enabled collectors from settings."""
        collectors: list[CollectorBase] = []
        s = self.settings.collector

        if s.coingecko_enabled:
            collectors.append(CoinGeckoCollector(interval=s.coingecko_interval))

        if s.coinmarketcap_enabled:
            collectors.append(CoinMarketCapCollector(interval=s.coinmarketcap_interval))

        if s.ccxt_enabled:
            for exchange in s.ccxt_priority_exchanges or ["binance"]:
                collectors.append(CCXTCollector(exchange_id=exchange, interval=s.ccxt_interval))

        if s.defillama_enabled:
            collectors.append(DefiLlamaCollector(interval=s.defillama_interval))

        if s.dexscreener_enabled:
            collectors.append(DexScreenerCollector(interval=s.dexscreener_interval))

        if s.coinalyze_enabled:
            collectors.append(CoinalyzeCollector(interval=s.coinalyze_interval))

        if s.fear_greed_enabled:
            collectors.append(FearGreedCollector(interval=s.fear_greed_interval))

        if s.cryptopanic_enabled:
            collectors.append(CryptoPanicCollector(interval=s.cryptopanic_interval))

        if s.whale_alert_enabled:
            collectors.append(WhaleAlertCollector(interval=s.whale_alert_interval))

        if s.coinmetrics_enabled:
            collectors.append(CoinMetricsCollector(interval=s.coinmetrics_interval))

        return collectors

    async def _run_collector(self, collector: CollectorBase) -> None:
        """Loop: collect → persist → sleep → repeat."""
        while self._running:
            try:
                logger.info(f"Collecting: {collector.name}")
                df = await collector.collect()

                if not df.empty:
                    rows = await persist_dataframe(collector.name, df)
                    logger.info(f"{collector.name}: {len(df)} rows collected, {rows} written to DB")
                else:
                    logger.debug(f"{collector.name}: no data returned")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collector {collector.name} error: {e}", exc_info=True)

            if not self._running:
                break

            await asyncio.sleep(collector.interval)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scheduler = Scheduler()
    try:
        await scheduler.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
