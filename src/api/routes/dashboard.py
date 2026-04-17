from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import get_db
from src.storage.models import (
    CollectorStatus,
    FearGreed,
    OHLCVCandle,
    OnChainMetric,
    TickerSnapshot,
    TradingSignal,
)

router = APIRouter()


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """High-level market snapshot."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)

    # Latest BTC ticker
    result = await db.execute(
        select(TickerSnapshot)
        .where(TickerSnapshot.symbol == "BTC")
        .order_by(desc(TickerSnapshot.timestamp))
        .limit(1)
    )
    ticker = result.scalar_one_or_none()

    # Latest fear & greed
    result = await db.execute(select(FearGreed).order_by(desc(FearGreed.timestamp)).limit(1))
    fg = result.scalar_one_or_none()

    # Signal count (last 24 h)
    result = await db.execute(
        select(func.count(TradingSignal.id)).where(
            TradingSignal.timestamp >= now - timedelta(hours=24)
        )
    )
    signal_count = result.scalar_one() or 0

    return {
        "btc_price": float(ticker.last) if ticker and ticker.last else None,
        "btc_change_24h": float(ticker.change_24h) if ticker and ticker.change_24h else None,
        "fear_greed_value": fg.value if fg else None,
        "fear_greed_classification": fg.classification if fg else None,
        "signals_last_24h": signal_count,
        "updated_at": now.isoformat(),
    }


@router.get("/market")
async def get_market_data(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Recent ticker snapshots."""
    result = await db.execute(
        select(TickerSnapshot).order_by(desc(TickerSnapshot.timestamp)).limit(limit)
    )
    rows = result.scalars().all()

    return {
        "tickers": [
            {
                "symbol": r.symbol,
                "exchange": r.exchange,
                "last": float(r.last) if r.last else None,
                "bid": float(r.bid) if r.bid else None,
                "ask": float(r.ask) if r.ask else None,
                "change_24h": float(r.change_24h) if r.change_24h else None,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = "BTC",
    timeframe: str = "1m",
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """OHLCV candles for a symbol."""
    result = await db.execute(
        select(OHLCVCandle)
        .where(OHLCVCandle.symbol == symbol.upper(), OHLCVCandle.timeframe == timeframe)
        .order_by(desc(OHLCVCandle.timestamp))
        .limit(limit)
    )
    rows = result.scalars().all()

    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "candles": [
            {
                "timestamp": r.timestamp.isoformat(),
                "open": float(r.open),
                "high": float(r.high),
                "low": float(r.low),
                "close": float(r.close),
                "volume": float(r.volume),
            }
            for r in reversed(rows)
        ],
    }


@router.get("/on-chain")
async def get_on_chain(
    symbol: str = "BTC",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Latest on-chain metrics."""
    result = await db.execute(
        select(OnChainMetric)
        .where(OnChainMetric.symbol == symbol.upper())
        .order_by(desc(OnChainMetric.timestamp))
        .limit(limit)
    )
    rows = result.scalars().all()

    return {
        "symbol": symbol.upper(),
        "metrics": [
            {
                "timestamp": r.timestamp.isoformat(),
                "metric_name": r.metric_name,
                "metric_value": float(r.metric_value),
            }
            for r in rows
        ],
    }


@router.get("/health")
async def get_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return collector health from DB."""
    result = await db.execute(select(CollectorStatus))
    rows = result.scalars().all()

    return {
        "collectors": [
            {
                "name": r.collector_name,
                "status": r.status,
                "last_run": r.last_run.isoformat() if r.last_run else None,
                "error_count": r.error_count,
            }
            for r in rows
        ],
        "updated_at": datetime.utcnow().isoformat(),
    }
