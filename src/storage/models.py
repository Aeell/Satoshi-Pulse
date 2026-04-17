from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OHLCVCandle(Base):
    __tablename__ = "ohlcv_candles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)

    __table_args__ = (
        UniqueConstraint("timestamp", "symbol", "exchange", "timeframe", name="uq_ohlcv"),
        Index("ix_ohlcv_symbol_time", "symbol", "timeframe", "timestamp"),
    )


class TickerSnapshot(Base):
    __tablename__ = "ticker_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    bid: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    ask: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    last: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    volume_24h: Mapped[Optional[float]] = mapped_column(Numeric(30, 8))
    change_24h: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "exchange", name="uq_ticker"),)


class CoinMetric(Base):
    __tablename__ = "coin_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market_cap: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))
    fdv: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))
    circulating_supply: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))
    volume: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))
    rank: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("timestamp", "symbol", name="uq_coin_metric"),)


class OnChainMetric(Base):
    __tablename__ = "on_chain_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)

    __table_args__ = (
        UniqueConstraint("timestamp", "symbol", "metric_name", name="uq_onchain"),
        Index("ix_onchain_name", "symbol", "metric_name"),
    )


class ExchangeFlow(Base):
    __tablename__ = "exchange_flows"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    net_flow: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)
    inflow: Mapped[float] = mapped_column(Numeric(30, 8))
    outflow: Mapped[float] = mapped_column(Numeric(30, 8))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "exchange", name="uq_exflow"),)


class DefiTVL(Base):
    __tablename__ = "defi_tvl"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    protocol: Mapped[str] = mapped_column(String(100), nullable=False)
    chain: Mapped[str] = mapped_column(String(50))
    tvl_usd: Mapped[float] = mapped_column(Numeric(30, 2), nullable=False)

    __table_args__ = (UniqueConstraint("timestamp", "protocol", "chain", name="uq_tvl"),)


class DexVolume(Base):
    __tablename__ = "dex_volumes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    protocol: Mapped[str] = mapped_column(String(100), nullable=False)
    chain: Mapped[str] = mapped_column(String(50))
    volume_24h: Mapped[float] = mapped_column(Numeric(30, 2))

    __table_args__ = (UniqueConstraint("timestamp", "protocol", "chain", name="uq_dexvol"),)


class YieldData(Base):
    __tablename__ = "yield_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    protocol: Mapped[str] = mapped_column(String(100), nullable=False)
    chain: Mapped[str] = mapped_column(String(50))
    pool: Mapped[str] = mapped_column(String(100))
    apy: Mapped[float] = mapped_column(Numeric(10, 4))
    tvl: Mapped[float] = mapped_column(Numeric(30, 2))

    __table_args__ = (UniqueConstraint("timestamp", "protocol", "pool", name="uq_yield"),)


class OpenInterest(Base):
    __tablename__ = "open_interest"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    oi_value: Mapped[float] = mapped_column(Numeric(30, 2), nullable=False)
    oi_change: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "exchange", name="uq_oi"),)


class FundingRate(Base):
    __tablename__ = "funding_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    predicted_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 8))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "exchange", name="uq_fund"),)


class Liquidation(Base):
    __tablename__ = "liquidations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10))
    amount_usd: Mapped[float] = mapped_column(Numeric(30, 2))
    price: Mapped[float] = mapped_column(Numeric(20, 8))


class LongShortRatio(Base):
    __tablename__ = "long_short_ratio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50))
    ratio: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    long_pct: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    short_pct: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "exchange", name="uq_ls"),)


class FearGreed(Base):
    __tablename__ = "fear_greed"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    classification: Mapped[str] = mapped_column(String(20))


class SocialMetric(Base):
    __tablename__ = "social_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    platform: Mapped[str] = mapped_column(String(50))
    mentions: Mapped[Optional[int]] = mapped_column(Integer)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    volume: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))

    __table_args__ = (UniqueConstraint("timestamp", "symbol", "platform", name="uq_social"),)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text)
    currencies: Mapped[Optional[str]] = mapped_column(String(200))
    sentiment_votes: Mapped[Optional[str]] = mapped_column(JSON)


class TrendingWord(Base):
    __tablename__ = "trending_words"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Numeric(10, 4))


class WhaleTransaction(Base):
    __tablename__ = "whale_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    from_addr: Mapped[str] = mapped_column(String(100))
    to_addr: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(30, 8), nullable=False)
    usd_value: Mapped[Optional[float]] = mapped_column(Numeric(30, 2))
    from_owner: Mapped[Optional[str]] = mapped_column(String(100))
    to_owner: Mapped[Optional[str]] = mapped_column(String(100))


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    strength: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    price_target: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    stop_loss: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    metadata_json: Mapped[Optional[str]] = mapped_column(JSON)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)


class SignalPerformance(Base):
    __tablename__ = "signal_performance"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    signal_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("trading_signals.id"))
    entry_price: Mapped[float] = mapped_column(Numeric(20, 8))
    exit_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    pnl_pct: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    status: Mapped[str] = mapped_column(String(20))


class CollectorStatus(Base):
    __tablename__ = "collector_status"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    collector_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
