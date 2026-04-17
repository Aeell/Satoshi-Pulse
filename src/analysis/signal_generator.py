import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class SignalSource(str, Enum):
    TECHNICAL = "technical"
    ON_CHAIN = "on_chain"
    SENTIMENT = "sentiment"
    DERIVATIVES = "derivatives"
    DEFI = "defi"
    COMPOSITE = "composite"


class Signal:
    def __init__(
        self,
        symbol: str,
        signal_type: SignalType,
        strength: int,
        strategy: str,
        source: SignalSource = SignalSource.COMPOSITE,
        price_target: Optional[float] = None,
        stop_loss: Optional[float] = None,
        confidence: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.timestamp = datetime.now()
        self.symbol = symbol
        self.signal_type = signal_type
        self.strength = strength
        self.strategy = strategy
        self.source = source
        self.price_target = price_target
        self.stop_loss = stop_loss
        self.confidence = confidence
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "strength": self.strength,
            "strategy": self.strategy,
            "source": self.source.value,
            "price_target": self.price_target,
            "stop_loss": self.stop_loss,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class SignalGenerator:
    SOURCE_WEIGHTS = {
        SignalSource.TECHNICAL: 0.40,
        SignalSource.ON_CHAIN: 0.30,
        SignalSource.SENTIMENT: 0.20,
        SignalSource.DERIVATIVES: 0.10,
    }

    def __init__(self):
        self.min_confidence = 0.5

    def generate_technical_signal(
        self,
        trend: str,
        momentum: float,
        divergence: str = "none",
    ) -> Optional[Signal]:
        if momentum > 65 and trend == "bullish":
            signal_type = SignalType.BUY
            strength = min(5, int((momentum - 50) / 15))
        elif momentum < 35 and trend == "bearish":
            signal_type = SignalType.SELL
            strength = min(5, int((50 - momentum) / 15))
        elif trend == "bullish":
            signal_type = SignalType.BUY
            strength = 2
        elif trend == "bearish":
            signal_type = SignalType.SELL
            strength = 2
        elif divergence == "bullish_divergence":
            signal_type = SignalType.BUY
            strength = 3
        elif divergence == "bearish_divergence":
            signal_type = SignalType.SELL
            strength = 3
        else:
            return None

        confidence = min(1.0, momentum / 100)

        return Signal(
            symbol="BTC",
            signal_type=signal_type,
            strength=strength,
            strategy="SatoshiCompositeStrategy",
            source=SignalSource.TECHNICAL,
            confidence=confidence,
            metadata={"trend": trend, "momentum": momentum, "divergence": divergence},
        )

    def generate_onchain_signal(
        self,
        exchange_flow: dict,
        mvrv: dict,
        whale: dict,
    ) -> Optional[Signal]:
        signals = []

        if exchange_flow["signal"] == "bullish":
            signals.append(("BUY", 3))
        elif exchange_flow["signal"] == "bearish":
            signals.append(("SELL", 3))

        if mvrv["signal"] == "buy":
            signals.append(("BUY", 2))
        elif mvrv["signal"] == "sell":
            signals.append(("SELL", 2))

        if whale["signal"] == "accumulation":
            signals.append(("BUY", 2))
        elif whale["signal"] == "distribution":
            signals.append(("SELL", 2))

        if not signals:
            return None

        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")

        if buy_score > sell_score:
            signal_type = SignalType.BUY
            strength = min(5, buy_score)
        elif sell_score > buy_score:
            signal_type = SignalType.SELL
            strength = min(5, sell_score)
        else:
            return None

        return Signal(
            symbol="BTC",
            signal_type=signal_type,
            strength=strength,
            strategy="OnChainWhaleStrategy",
            source=SignalSource.ON_CHAIN,
            confidence=0.7,
        )

    def generate_sentiment_signal(
        self,
        fear_greed: dict,
        news: dict,
    ) -> Optional[Signal]:
        fg_value = fear_greed.get("value", 50)
        news_sentiment = news.get("sentiment_score", 50)

        if fg_value < 15 and news_sentiment < 40:
            signal_type = SignalType.BUY
            strength = 5
        elif fg_value > 85 and news_sentiment > 60:
            signal_type = SignalType.SELL
            strength = 5
        elif fg_value < 25:
            signal_type = SignalType.BUY
            strength = 3
        elif fg_value > 75:
            signal_type = SignalType.SELL
            strength = 3
        else:
            return None

        confidence = abs(50 - fg_value) / 50

        return Signal(
            symbol="BTC",
            signal_type=signal_type,
            strength=strength,
            strategy="SentimentReversalStrategy",
            source=SignalSource.SENTIMENT,
            confidence=confidence,
        )

    def generate_derivatives_signal(
        self,
        funding: dict,
        oi_div: dict,
        ls_ratio: dict,
    ) -> Optional[Signal]:
        signals = []

        if funding["signal"] == "buy":
            signals.append(("BUY", 2))
        elif funding["signal"] == "sell":
            signals.append(("SELL", 2))

        if oi_div["signal"] in ["bullish_confirmation", "bullish_divergence"]:
            signals.append(("BUY", 2))
        elif oi_div["signal"] == "bearish_divergence":
            signals.append(("SELL", 3))

        if ls_ratio["signal"] == "buy":
            signals.append(("BUY", 2))
        elif ls_ratio["signal"] == "sell":
            signals.append(("SELL", 2))

        if not signals:
            return None

        buy_score = sum(s[1] for s in signals if s[0] == "BUY")
        sell_score = sum(s[1] for s in signals if s[0] == "SELL")

        if buy_score > sell_score:
            signal_type = SignalType.BUY
            strength = min(5, buy_score)
        elif sell_score > buy_score:
            signal_type = SignalType.SELL
            strength = min(5, sell_score)
        else:
            return None

        return Signal(
            symbol="BTC",
            signal_type=signal_type,
            strength=strength,
            strategy="DerivativesAlphaStrategy",
            source=SignalSource.DERIVATIVES,
            confidence=0.6,
        )

    def generate_composite_signal(
        self,
        technical: Optional[Signal] = None,
        onchain: Optional[Signal] = None,
        sentiment: Optional[Signal] = None,
        derivatives: Optional[Signal] = None,
    ) -> Optional[Signal]:
        source_signals = [
            (SignalSource.TECHNICAL, technical),
            (SignalSource.ON_CHAIN, onchain),
            (SignalSource.SENTIMENT, sentiment),
            (SignalSource.DERIVATIVES, derivatives),
        ]

        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0

        for source, signal in source_signals:
            if signal:
                weight = self.SOURCE_WEIGHTS.get(source, 0.25)
                total_weight += weight

                if signal.signal_type == SignalType.BUY:
                    buy_score += signal.strength * weight * signal.confidence
                elif signal.signal_type == SignalType.SELL:
                    sell_score += signal.strength * weight * signal.confidence

        if total_weight == 0:
            return None

        buy_score /= total_weight
        sell_score /= total_weight

        strength_buy = int(buy_score)
        strength_sell = int(sell_score)

        if strength_buy >= 3 and buy_score >= sell_score + 1:
            signal_type = SignalType.BUY
            strength = strength_buy
            confidence = buy_score / 5.0
        elif strength_sell >= 3 and sell_score >= buy_score + 1:
            signal_type = SignalType.SELL
            strength = strength_sell
            confidence = sell_score / 5.0
        else:
            return None

        return Signal(
            symbol="BTC",
            signal_type=signal_type,
            strength=strength,
            strategy="SatoshiCompositeStrategy",
            source=SignalSource.COMPOSITE,
            confidence=min(1.0, confidence),
            metadata={
                "technical": technical.to_dict() if technical else None,
                "onchain": onchain.to_dict() if onchain else None,
                "sentiment": sentiment.to_dict() if sentiment else None,
                "derivatives": derivatives.to_dict() if derivatives else None,
            },
        )

    def calculate_position_size(
        self,
        signal: Signal,
        portfolio_value: float,
        max_position: float = 0.02,
    ) -> float:
        base_size = portfolio_value * max_position
        adjusted_size = base_size * signal.confidence
        return round(adjusted_size, 8)
