"""
Persist collector DataFrames to the database.

Each collector produces a DataFrame with a known schema.  The writer
maps collector names to the appropriate table and upserts rows so
re-runs never create duplicates.
"""

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import db
from src.storage.models import (
    CoinMetric,
    CollectorStatus,
    DefiTVL,
    FearGreed,
    NewsArticle,
    OHLCVCandle,
    OnChainMetric,
    TickerSnapshot,
    WhaleTransaction,
)

logger = logging.getLogger(__name__)


async def persist_dataframe(collector_name: str, df: pd.DataFrame) -> int:
    """
    Persist a collector's output DataFrame to the correct table.
    Returns the number of rows written.
    """
    if df is None or df.empty:
        return 0

    try:
        async with db.session() as session:
            rows = await _route(collector_name, df, session)
            await _update_collector_status(session, collector_name, rows)
            return rows
    except Exception as e:
        logger.error(f"DB write error for {collector_name}: {e}")
        return 0


async def _route(collector_name: str, df: pd.DataFrame, session: AsyncSession) -> int:
    """Route a DataFrame to the correct writer based on collector name."""
    name = collector_name.lower()

    if name.startswith("ccxt_"):
        return await _write_ccxt(df, name.replace("ccxt_", ""), session)
    elif name == "coingecko":
        return await _write_coin_metrics(df, session)
    elif name == "coinmetrics":
        return await _write_on_chain(df, session)
    elif name == "defillama":
        return await _write_defi_tvl(df, session)
    elif name == "fear_greed":
        return await _write_fear_greed(df, session)
    elif name == "whale_alert":
        return await _write_whale(df, session)
    elif name == "cryptopanic":
        return await _write_news(df, session)
    else:
        # Fallback: log rows only
        logger.debug(f"No specific writer for {collector_name}, {len(df)} rows ignored")
        return 0


async def _write_ccxt(df: pd.DataFrame, exchange: str, session: AsyncSession) -> int:
    """Write CCXT ticker + OHLCV data."""
    written = 0

    # OHLCV rows have an 'open' column
    ohlcv = (
        df[df.get("open", pd.Series(dtype=float)).notna()]
        if "open" in df.columns
        else pd.DataFrame()
    )
    tickers = df[~df.index.isin(ohlcv.index)] if not ohlcv.empty else df

    for _, row in ohlcv.iterrows():
        try:
            candle = OHLCVCandle(
                timestamp=_ts(row.get("timestamp")),
                symbol=str(row.get("symbol", "BTC")),
                exchange=exchange,
                timeframe=str(row.get("timeframe", "1m")),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            session.add(candle)
            written += 1
        except Exception as e:
            logger.debug(f"OHLCV row skip: {e}")

    for _, row in tickers.iterrows():
        try:
            snap = TickerSnapshot(
                timestamp=_ts(row.get("timestamp")),
                symbol=str(row.get("symbol", "")),
                exchange=exchange,
                bid=_safe_float(row.get("bid")),
                ask=_safe_float(row.get("ask")),
                last=_safe_float(row.get("last")),
                volume_24h=_safe_float(row.get("volume")),
                change_24h=_safe_float(row.get("change_24h")),
            )
            session.add(snap)
            written += 1
        except Exception as e:
            logger.debug(f"Ticker row skip: {e}")

    return written


async def _write_coin_metrics(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            metric = CoinMetric(
                timestamp=_ts(row.get("timestamp")),
                symbol=str(row.get("symbol", "")),
                volume=_safe_float(row.get("volume_24h")),
            )
            session.add(metric)
            written += 1
        except Exception as e:
            logger.debug(f"CoinMetric row skip: {e}")
    return written


async def _write_on_chain(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            m = OnChainMetric(
                timestamp=_ts(row.get("timestamp")),
                symbol=str(row.get("symbol", "BTC")),
                metric_name=str(row.get("metric_name", "")),
                metric_value=float(row.get("metric_value", 0)),
            )
            session.add(m)
            written += 1
        except Exception as e:
            logger.debug(f"OnChain row skip: {e}")
    return written


async def _write_defi_tvl(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            tvl = DefiTVL(
                timestamp=_ts(row.get("timestamp")),
                protocol=str(row.get("protocol", "")),
                chain=str(row.get("chain", "")),
                tvl_usd=float(row.get("tvl_usd", 0)),
            )
            session.add(tvl)
            written += 1
        except Exception as e:
            logger.debug(f"DefiTVL row skip: {e}")
    return written


async def _write_fear_greed(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            fg = FearGreed(
                timestamp=_ts(row.get("timestamp")),
                value=int(row.get("value", 50)),
                classification=str(row.get("classification", "")),
            )
            session.add(fg)
            written += 1
        except Exception as e:
            logger.debug(f"FearGreed row skip: {e}")
    return written


async def _write_whale(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            tx = WhaleTransaction(
                timestamp=_ts(row.get("timestamp")),
                symbol=str(row.get("symbol", "")),
                from_addr=str(row.get("from_addr", "")),
                to_addr=str(row.get("to_addr", "")),
                amount=float(row.get("amount", 0)),
                usd_value=_safe_float(row.get("usd_value")),
                from_owner=str(row.get("from_owner", "")),
                to_owner=str(row.get("to_owner", "")),
            )
            session.add(tx)
            written += 1
        except Exception as e:
            logger.debug(f"Whale row skip: {e}")
    return written


async def _write_news(df: pd.DataFrame, session: AsyncSession) -> int:
    written = 0
    for _, row in df.iterrows():
        try:
            article = NewsArticle(
                timestamp=_ts(row.get("timestamp")),
                source=str(row.get("source", "")),
                title=str(row.get("title", "")),
                url=str(row.get("url", "")),
                currencies=str(row.get("currencies", "")),
                sentiment_votes=row.get("votes"),
            )
            session.add(article)
            written += 1
        except Exception as e:
            logger.debug(f"News row skip: {e}")
    return written


async def _update_collector_status(session: AsyncSession, name: str, rows_written: int) -> None:
    from sqlalchemy import select

    result = await session.execute(
        select(CollectorStatus).where(CollectorStatus.collector_name == name)
    )
    status_row = result.scalar_one_or_none()

    if status_row is None:
        status_row = CollectorStatus(
            collector_name=name,
            last_run=datetime.now(),
            status="ok",
            error_count=0,
        )
        session.add(status_row)
    else:
        status_row.last_run = datetime.now()
        status_row.status = "ok"
        status_row.error_count = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts(val) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    return datetime.now()


def _safe_float(val) -> float | None:
    try:
        return float(val) if val is not None and str(val) not in ("nan", "None") else None
    except (TypeError, ValueError):
        return None
