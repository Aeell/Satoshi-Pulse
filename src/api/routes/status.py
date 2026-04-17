import os
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import db, get_db
from src.storage.models import CollectorStatus

router = APIRouter()

_START_TIME = time.time()


@router.get("/collectors")
async def get_collector_status(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Latest per-collector status from DB."""
    result = await session.execute(select(CollectorStatus))
    rows = result.scalars().all()

    return {
        "collectors": [
            {
                "name": r.collector_name,
                "status": r.status,
                "last_run": r.last_run.isoformat() if r.last_run else None,
                "next_run": r.next_run.isoformat() if r.next_run else None,
                "error_count": r.error_count,
                "last_error": r.last_error,
            }
            for r in rows
        ]
    }


@router.get("/database")
async def get_database_status(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Check DB connectivity and approximate size."""
    try:
        await session.execute(text("SELECT 1"))
        connected = True
    except Exception:
        connected = False

    size_mb = None
    if db.is_sqlite:
        sqlite_path = db.settings.database.sqlite_path
        try:
            size_mb = round(os.path.getsize(sqlite_path) / 1_048_576, 2)
        except OSError:
            size_mb = 0.0

    return {
        "connected": connected,
        "backend": "sqlite" if db.is_sqlite else "postgresql",
        "size_mb": size_mb,
    }


@router.get("/system")
async def get_system_status() -> dict[str, Any]:
    """Basic process/uptime info."""
    uptime_seconds = int(time.time() - _START_TIME)

    return {
        "version": "2.0.0",
        "uptime_seconds": uptime_seconds,
        "uptime_human": _fmt_uptime(uptime_seconds),
        "utc_now": datetime.utcnow().isoformat(),
        "pid": os.getpid(),
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _fmt_uptime(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h {m:02d}m {s:02d}s"
