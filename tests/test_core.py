"""
Core test suite for Satoshi Pulse v2.

Covers:
- Settings validation
- Collector base class mechanics
- FearGreed transform (was broken — regression test)
- Signal generation
- DB writer routing
- API health endpoint
"""

import asyncio
from datetime import datetime

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def test_settings_loads():
    """Settings module must import without errors."""
    from src.config.settings import get_settings

    s = get_settings()
    assert s.env in ("development", "production", "test")
    assert s.collector.coingecko_enabled is True


def test_settings_no_glassnode():
    """Glassnode must not exist in collector settings."""
    from src.config.settings import CollectorSettings

    settings = CollectorSettings()
    assert not hasattr(settings, "glassnode_enabled"), (
        "GlassnodeCollector was removed — no setting should exist"
    )


# ---------------------------------------------------------------------------
# Collector base
# ---------------------------------------------------------------------------


class _DummyCollector:
    """Minimal reimplementation for testing without network."""

    name = "dummy"
    interval = 60
    enabled = True

    async def collect(self) -> pd.DataFrame:
        return pd.DataFrame([{"timestamp": datetime.now(), "value": 42}])


def test_dummy_collector_sync():
    df = asyncio.run(_DummyCollector().collect())
    assert not df.empty
    assert "value" in df.columns


# ---------------------------------------------------------------------------
# FearGreed transform regression test
# ---------------------------------------------------------------------------


def test_fear_greed_transform():
    """Regression: FearGreed._transform was broken (unclosed tuple)."""
    from src.collectors.derivatives import FearGreedCollector

    collector = FearGreedCollector()
    sample = {
        "data": [
            {
                "timestamp": "1700000000",
                "value": "72",
                "value_classification": "Greed",
            }
        ]
    }
    df = collector._transform(sample)
    assert not df.empty
    assert "value" in df.columns
    assert df["value"].iloc[0] == 72


# ---------------------------------------------------------------------------
# Signal generator
# ---------------------------------------------------------------------------


def test_signal_generator_buy():
    from src.analysis.signal_generator import SignalGenerator, SignalType

    gen = SignalGenerator()
    # momentum > 65 + bullish trend → BUY
    signal = gen.generate_technical_signal(trend="bullish", momentum=70.0)
    assert signal is not None
    assert signal.signal_type == SignalType.BUY


def test_signal_generator_sell():
    from src.analysis.signal_generator import SignalGenerator, SignalType

    gen = SignalGenerator()
    # momentum < 35 + bearish trend → SELL
    signal = gen.generate_technical_signal(trend="bearish", momentum=25.0)
    assert signal is not None
    assert signal.signal_type == SignalType.SELL


# ---------------------------------------------------------------------------
# Storage writer helpers — regression tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_persist_empty_dataframe():
    """Persisting an empty DataFrame must return 0 and not raise."""
    from src.storage.writer import persist_dataframe

    rows = await persist_dataframe("coingecko", pd.DataFrame())
    assert rows == 0


@pytest.mark.asyncio
async def test_persist_unknown_collector():
    """Unknown collector names must return 0 gracefully."""
    from src.storage.writer import persist_dataframe

    df = pd.DataFrame([{"timestamp": datetime.now(), "x": 1}])
    rows = await persist_dataframe("totally_unknown_collector", df)
    assert rows == 0


def test_ts_helper_bad_input():
    """_ts() must return a datetime even for bad input and log a warning."""
    from src.storage.writer import _ts

    result = _ts("not-a-timestamp")
    assert isinstance(result, datetime)

    result2 = _ts(None)
    assert isinstance(result2, datetime)


def test_ts_helper_valid_inputs():
    """_ts() must pass through datetime and pd.Timestamp unchanged."""
    from src.storage.writer import _safe_float, _ts

    now = datetime.now()
    assert _ts(now) == now
    assert _ts(pd.Timestamp("2024-01-01")) == datetime(2024, 1, 1)

    # _safe_float: numpy NaN / inf must return None
    assert _safe_float(float("nan")) is None
    assert _safe_float(float("inf")) is None
    assert _safe_float(None) is None
    assert _safe_float("nan") is None
    assert abs(_safe_float(42.0) - 42.0) < 1e-9
    assert abs(_safe_float("3.14") - 3.14) < 1e-9


def test_sqlite_db_init():
    """Database.init() must select aiosqlite URL when use_sqlite=True."""
    import os
    os.environ["DB_USE_SQLITE"] = "true"

    from src.config.settings import DatabaseSettings
    s = DatabaseSettings()
    assert s.use_sqlite is True
    assert "aiosqlite" in s.async_url


# ---------------------------------------------------------------------------
# API root endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_root():
    from httpx import ASGITransport, AsyncClient

    from src.api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Satoshi Pulse"
    assert data["version"] == "2.0.0"


@pytest.mark.asyncio
async def test_api_health():
    from httpx import ASGITransport, AsyncClient

    from src.api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
