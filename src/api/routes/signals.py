from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.signal_generator import Signal, SignalGenerator, SignalType
from src.storage.database import get_db
from src.storage.models import TradingSignal

router = APIRouter()


@router.get("/active")
async def get_active_signals(
    hours: int = Query(24, le=168),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return signals generated in the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(TradingSignal)
        .where(TradingSignal.timestamp >= since)
        .order_by(desc(TradingSignal.timestamp))
    )
    rows = result.scalars().all()

    return {
        "signals": [_signal_to_dict(r) for r in rows],
        "total": len(rows),
        "since": since.isoformat(),
    }


@router.get("/history")
async def get_signal_history(
    limit: int = Query(100, le=1000),
    since: Optional[str] = None,
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Paginated signal history with optional filters."""
    stmt = select(TradingSignal).order_by(desc(TradingSignal.timestamp))

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            stmt = stmt.where(TradingSignal.timestamp >= since_dt)
        except ValueError:
            pass

    if symbol:
        stmt = stmt.where(TradingSignal.symbol == symbol.upper())

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {"signals": [_signal_to_dict(r) for r in rows]}


@router.get("/performance")
async def get_performance(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Aggregate signal performance stats."""
    result = await db.execute(select(func.count(TradingSignal.id)))
    total = result.scalar_one() or 0

    result = await db.execute(
        select(func.count(TradingSignal.id)).where(TradingSignal.executed == True)  # noqa: E712
    )
    executed = result.scalar_one() or 0

    return {
        "total_signals": total,
        "executed_signals": executed,
        "pending_signals": total - executed,
    }


@router.post("/")
async def create_signal(
    symbol: str,
    signal_type: str,
    strength: int,
    strategy: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually inject a signal (useful for testing)."""
    try:
        st = SignalType(signal_type.upper())
    except ValueError:
        st = SignalType.HOLD

    row = TradingSignal(
        timestamp=datetime.utcnow(),
        symbol=symbol.upper(),
        strategy=strategy,
        signal_type=st.value,
        strength=max(1, min(100, strength)),
        executed=False,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return {"status": "created", "id": row.id}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _signal_to_dict(row: TradingSignal) -> dict[str, Any]:
    return {
        "id": row.id,
        "timestamp": row.timestamp.isoformat(),
        "symbol": row.symbol,
        "strategy": row.strategy,
        "signal_type": row.signal_type,
        "strength": row.strength,
        "price_target": float(row.price_target) if row.price_target else None,
        "stop_loss": float(row.stop_loss) if row.stop_loss else None,
        "executed": row.executed,
        "metadata": row.metadata_json,
    }
