import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import pandas_ta as ta

    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas-ta not available, using basic indicators")


class TechnicalAnalyzer:
    def __init__(self):
        self.timeframes = ["1h", "4h", "1d"]

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "close" not in df.columns:
            return df

        if PANDAS_TA_AVAILABLE:
            Close = df["close"]
            High = df.get("high", Close)
            Low = df.get("low", Close)
            Volume = df.get("volume", pd.Series([0] * len(df)))

            df["sma_7"] = Close.rolling(7).mean()
            df["sma_21"] = Close.rolling(21).mean()
            df["sma_50"] = Close.rolling(50).mean()
            df["sma_100"] = Close.rolling(100).mean()
            df["sma_200"] = Close.rolling(200).mean()

            df["ema_7"] = Close.ewm(span=7, adjust=False).mean()
            df["ema_21"] = Close.ewm(span=21, adjust=False).mean()

            delta = Close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            ema12 = Close.ewm(span=12, adjust=False).mean()
            ema26 = Close.ewm(span=26, adjust=False).mean()
            df["macd"] = ema12 - ema26
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]

            df["bb_upper"], df["bb_middle"], df["bb_lower"] = ta.bbands(Close, length=20, std=2)

            df["atr"] = ta.atr(High, Low, Close, length=14)

            df["adx"] = ta.adx(High, Low, Close, length=14)["ADX_14"]

            df["stoch_k"], df["stoch_d"] = ta.stoch(High, Low, Close)

            df["williams_r"] = ta.williams_r(High, Low, Close, length=14)

            df["obv"] = ta.obv(Close, Volume)

            df["vwap"] = (Close * Volume).cumsum() / Volume.cumsum()

            cci = ta.cci(High, Low, Close, length=20)
            df["cci"] = cci

        else:
            Close = df["close"]
            df["sma_7"] = Close.rolling(7).mean()
            df["sma_21"] = Close.rolling(21).mean()
            df["sma_50"] = Close.rolling(50).mean()

            delta = Close.diff()
            gain = delta.clip(lower=0)
            loss = (-delta).clip(lower=0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            df["rsi"] = 100 - (100 / (1 + rs))

            df["macd"] = Close.ewm(span=12).mean() - Close.ewm(span=26).mean()
            df["macd_signal"] = df["macd"].ewm(span=9).mean()

            df["atr"] = (Close.max() - Close.min()) * np.sqrt(len(Close))

        return df

    def detect_divergence(
        self, df: pd.DataFrame, price_col: str = "close", indicator_col: str = "rsi"
    ) -> str:
        if df.empty or indicator_col not in df.columns:
            return "none"

        price_trend = df[price_col].diff().sum()
        indicator_trend = df[indicator_col].diff().sum()

        if price_trend > 0 and indicator_trend < 0:
            return "bearish_divergence"
        elif price_trend < 0 and indicator_trend > 0:
            return "bullish_divergence"
        return "none"

    def get_trend_direction(self, df: pd.DataFrame) -> str:
        if df.empty or "close" not in df.columns:
            return "neutral"

        short_ma = df.get("sma_21", df["close"])
        long_ma = df.get("sma_50", df["close"])

        if short_ma.iloc[-1] > long_ma.iloc[-1]:
            return "bullish"
        elif short_ma.iloc[-1] < long_ma.iloc[-1]:
            return "bearish"
        return "neutral"

    def get_momentum_score(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 50.0

        score = 50.0

        if "rsi" in df.columns:
            rsi = df["rsi"].iloc[-1]
            if rsi > 70:
                score -= 15
            elif rsi < 30:
                score += 15
            else:
                score += (50 - rsi) / 40 * 10

        if "macd" in df.columns:
            macd = df["macd"].iloc[-1]
            macd_signal = df["macd_signal"].iloc[-1]
            if macd > macd_signal:
                score += 10
            else:
                score -= 10

        if "adx" in df.columns:
            adx = df["adx"].iloc[-1]
            if adx > 25:
                score += 5

        return max(0, min(100, score))


class OnChainAnalyzer:
    def __init__(self):
        pass

    def analyze_exchange_flows(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "net_flow": 0}

        net_flow = df["net_flow"].sum()
        signal = "neutral"

        if net_flow < 0:
            signal = "bullish"
        elif net_flow > 0:
            signal = "bearish"

        return {"signal": signal, "net_flow": net_flow}

    def analyze_mvrv(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "z_score": 0}

        z_score = df["metric_value"].iloc[-1] if "metric_value" in df.columns else 0
        signal = "neutral"

        if z_score > 8:
            signal = "sell"
        elif z_score < 0:
            signal = "buy"

        return {"signal": signal, "z_score": z_score}

    def analyze_whale_activity(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "whale_pressure": 0}

        total_volume = df["usd_value"].sum()
        net_direction = df["amount"].sum()

        signal = "neutral"
        if net_direction < 0:
            signal = "accumulation"
        elif net_direction > 0:
            signal = "distribution"

        return {"signal": signal, "whale_pressure": total_volume, "net_direction": net_direction}


class SentimentAnalyzer:
    def __init__(self):
        self.thresholds = {"fear": 25, "greed": 75}

    def analyze_fear_greed(self, df: pd.DataFrame) -> dict:
        if df.empty or "value" not in df.columns:
            return {"signal": "neutral", "value": 50, "classification": "neutral"}

        current = df["value"].iloc[-1]
        classification = df.get("classification", pd.Series(["neutral"])).iloc[-1]

        signal = "neutral"
        if current < self.thresholds["fear"]:
            signal = "buy"
        elif current > self.thresholds["greed"]:
            signal = "sell"

        return {"signal": signal, "value": current, "classification": classification}

    def analyze_news_sentiment(self, df: pd.DataFrame) -> dict:
        if df.empty or "votes" not in df.columns:
            return {"signal": "neutral", "sentiment_score": 50}

        bullish = 0
        bearish = 0

        for votes in df["votes"]:
            if isinstance(votes, dict):
                bullish += votes.get("bullish", 0)
                bearish += votes.get("bearish", 0)

        total = bullish + bearish
        if total == 0:
            sentiment = 50
        else:
            sentiment = (bullish / total) * 100

        signal = "neutral"
        if sentiment > 60:
            signal = "buy"
        elif sentiment < 40:
            signal = "sell"

        return {"signal": signal, "sentiment_score": sentiment}

    def get_composite_sentiment(self, fear_greed: dict, news: dict) -> float:
        return fear_greed.get("value", 50) * 0.5 + news.get("sentiment_score", 50) * 0.5


class DerivativesAnalyzer:
    def analyze_funding_rate(self, df: pd.DataFrame) -> dict:
        if df.empty or "rate" not in df.columns:
            return {"signal": "neutral", "rate": 0}

        current_rate = df["rate"].iloc[-1]
        signal = "neutral"

        if current_rate > 0.01:
            signal = "sell"
        elif current_rate < -0.01:
            signal = "buy"

        return {"signal": signal, "rate": current_rate}

    def analyze_oi_divergence(self, price_df: pd.DataFrame, oi_df: pd.DataFrame) -> dict:
        if price_df.empty or oi_df.empty:
            return {"signal": "neutral"}

        price_change = price_df["close"].iloc[-1] - price_df["close"].iloc[0]
        oi_change = oi_df["oi_value"].iloc[-1] - oi_df["oi_value"].iloc[0]

        signal = "neutral"
        if price_change > 0 and oi_change > 0:
            signal = "bullish_confirmation"
        elif price_change < 0 and oi_change > 0:
            signal = "bearish_divergence"
        elif price_change > 0 and oi_change < 0:
            signal = "bullish_divergence"

        return {"signal": signal, "price_change": price_change, "oi_change": oi_change}

    def analyze_long_short_ratio(self, df: pd.DataFrame) -> dict:
        if df.empty or "ratio" not in df.columns:
            return {"signal": "neutral", "ratio": 1}

        ratio = df["ratio"].iloc[-1]
        signal = "neutral"

        if ratio > 1.2:
            signal = "sell"
        elif ratio < 0.8:
            signal = "buy"

        return {"signal": signal, "ratio": ratio}
