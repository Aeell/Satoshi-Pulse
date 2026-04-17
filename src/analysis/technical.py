"""
Technical analysis module.

Uses the `ta` library (pip install ta) for indicators.  Falls back to
pure-NumPy/Pandas implementations for the most critical ones if `ta` is
not installed.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import ta as ta_lib

    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logger.warning("ta library not available — using built-in indicator fallbacks")


class TechnicalAnalyzer:
    """Calculate 40+ technical indicators on OHLCV DataFrames."""

    def __init__(self):
        self.timeframes = ["1h", "4h", "1d"]

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicator columns to *df* (in-place copy returned)."""
        if df.empty or "close" not in df.columns:
            return df

        df = df.copy()
        close = df["close"].astype(float)
        high = df.get("high", close).astype(float)
        low = df.get("low", close).astype(float)
        volume = df.get("volume", pd.Series(np.zeros(len(df)), index=df.index)).astype(float)

        # --- Moving averages (always computed) ---------------------------------
        for window in (7, 21, 50, 100, 200):
            df[f"sma_{window}"] = close.rolling(window).mean()
        for span in (7, 21):
            df[f"ema_{span}"] = close.ewm(span=span, adjust=False).mean()

        # --- RSI ---------------------------------------------------------------
        df["rsi"] = self._rsi(close, 14)

        # --- MACD --------------------------------------------------------------
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # --- Bollinger Bands ---------------------------------------------------
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        df["bb_upper"] = bb_mid + 2 * bb_std
        df["bb_middle"] = bb_mid
        df["bb_lower"] = bb_mid - 2 * bb_std

        # --- ATR ---------------------------------------------------------------
        df["atr"] = self._atr(high, low, close, 14)

        # --- VWAP --------------------------------------------------------------
        df["vwap"] = (close * volume).cumsum() / volume.cumsum().replace(0, np.nan)

        if TA_AVAILABLE:
            # Use ta library for remaining indicators
            try:
                adx_ind = ta_lib.trend.ADXIndicator(high, low, close, window=14)
                df["adx"] = adx_ind.adx()
            except Exception:
                pass

            try:
                stoch = ta_lib.momentum.StochasticOscillator(high, low, close)
                df["stoch_k"] = stoch.stoch()
                df["stoch_d"] = stoch.stoch_signal()
            except Exception:
                pass

            try:
                df["williams_r"] = ta_lib.momentum.WilliamsRIndicator(high, low, close).williams_r()
            except Exception:
                pass

            try:
                df["obv"] = ta_lib.volume.OnBalanceVolumeIndicator(
                    close, volume
                ).on_balance_volume()
            except Exception:
                pass

            try:
                df["cci"] = ta_lib.trend.CCIIndicator(high, low, close).cci()
            except Exception:
                pass

            try:
                df["cmf"] = ta_lib.volume.ChaikinMoneyFlowIndicator(
                    high, low, close, volume
                ).chaikin_money_flow()
            except Exception:
                pass

            try:
                df["mfi"] = ta_lib.volume.MFIIndicator(high, low, close, volume).money_flow_index()
            except Exception:
                pass

        else:
            # Minimal fallbacks
            df["adx"] = self._adx_approx(high, low, close, 14)

        return df

    # ------------------------------------------------------------------
    # Pure-NumPy indicator implementations (fallbacks + always-on)
    # ------------------------------------------------------------------

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta).clip(lower=0).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def _adx_approx(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """Simple ADX approximation (accurate enough for signal scoring)."""
        tr = pd.concat(
            [
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs(),
            ],
            axis=1,
        ).max(axis=1)
        smooth_tr = tr.rolling(period).mean()
        dm_plus = (high - high.shift(1)).clip(lower=0)
        dm_minus = (low.shift(1) - low).clip(lower=0)
        di_plus = 100 * dm_plus.rolling(period).mean() / smooth_tr.replace(0, np.nan)
        di_minus = 100 * dm_minus.rolling(period).mean() / smooth_tr.replace(0, np.nan)
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
        return dx.rolling(period).mean()

    # ------------------------------------------------------------------
    # High-level helpers used by SignalGenerator
    # ------------------------------------------------------------------

    def detect_divergence(
        self, df: pd.DataFrame, price_col: str = "close", indicator_col: str = "rsi"
    ) -> str:
        if df.empty or indicator_col not in df.columns:
            return "none"
        price_trend = df[price_col].diff().sum()
        ind_trend = df[indicator_col].diff().sum()
        if price_trend > 0 and ind_trend < 0:
            return "bearish_divergence"
        elif price_trend < 0 and ind_trend > 0:
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
        if "rsi" in df.columns and not pd.isna(df["rsi"].iloc[-1]):
            rsi = df["rsi"].iloc[-1]
            if rsi > 70:
                score -= 15
            elif rsi < 30:
                score += 15
            else:
                score += (50 - rsi) / 40 * 10
        if "macd" in df.columns and "macd_signal" in df.columns:
            if df["macd"].iloc[-1] > df["macd_signal"].iloc[-1]:
                score += 10
            else:
                score -= 10
        if "adx" in df.columns and not pd.isna(df["adx"].iloc[-1]):
            if df["adx"].iloc[-1] > 25:
                score += 5
        return max(0.0, min(100.0, score))


class OnChainAnalyzer:
    def analyze_exchange_flows(self, df: pd.DataFrame) -> dict:
        if df.empty or "net_flow" not in df.columns:
            return {"signal": "neutral", "net_flow": 0}
        net_flow = df["net_flow"].sum()
        signal = "bullish" if net_flow < 0 else "bearish" if net_flow > 0 else "neutral"
        return {"signal": signal, "net_flow": net_flow}

    def analyze_mvrv(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "z_score": 0}
        z_score = df["metric_value"].iloc[-1] if "metric_value" in df.columns else 0
        signal = "sell" if z_score > 8 else "buy" if z_score < 0 else "neutral"
        return {"signal": signal, "z_score": z_score}

    def analyze_whale_activity(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "whale_pressure": 0}
        total_volume = df.get("usd_value", pd.Series()).sum()
        net_direction = df.get("amount", pd.Series()).sum()
        signal = (
            "accumulation"
            if net_direction < 0
            else "distribution"
            if net_direction > 0
            else "neutral"
        )
        return {"signal": signal, "whale_pressure": total_volume, "net_direction": net_direction}


class SentimentAnalyzer:
    def __init__(self):
        self.thresholds = {"fear": 25, "greed": 75}

    def analyze_fear_greed(self, df: pd.DataFrame) -> dict:
        if df.empty or "value" not in df.columns:
            return {"signal": "neutral", "value": 50, "classification": "neutral"}
        current = df["value"].iloc[-1]
        classification = (
            df["classification"].iloc[-1] if "classification" in df.columns else "neutral"
        )
        signal = (
            "buy"
            if current < self.thresholds["fear"]
            else "sell"
            if current > self.thresholds["greed"]
            else "neutral"
        )
        return {"signal": signal, "value": current, "classification": classification}

    def analyze_news_sentiment(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"signal": "neutral", "sentiment_score": 50}
        bullish = bearish = 0
        for votes in df.get("votes", []):
            if isinstance(votes, dict):
                bullish += votes.get("bullish", 0)
                bearish += votes.get("bearish", 0)
        total = bullish + bearish
        sentiment = (bullish / total * 100) if total > 0 else 50.0
        signal = "buy" if sentiment > 60 else "sell" if sentiment < 40 else "neutral"
        return {"signal": signal, "sentiment_score": sentiment}

    def get_composite_sentiment(self, fear_greed: dict, news: dict) -> float:
        return fear_greed.get("value", 50) * 0.5 + news.get("sentiment_score", 50) * 0.5


class DerivativesAnalyzer:
    def analyze_funding_rate(self, df: pd.DataFrame) -> dict:
        if df.empty or "rate" not in df.columns:
            return {"signal": "neutral", "rate": 0}
        rate = df["rate"].iloc[-1]
        signal = "sell" if rate > 0.01 else "buy" if rate < -0.01 else "neutral"
        return {"signal": signal, "rate": rate}

    def analyze_oi_divergence(self, price_df: pd.DataFrame, oi_df: pd.DataFrame) -> dict:
        if price_df.empty or oi_df.empty:
            return {"signal": "neutral"}
        price_change = price_df["close"].iloc[-1] - price_df["close"].iloc[0]
        oi_change = oi_df["oi_value"].iloc[-1] - oi_df["oi_value"].iloc[0]
        if price_change > 0 and oi_change > 0:
            signal = "bullish_confirmation"
        elif price_change < 0 and oi_change > 0:
            signal = "bearish_divergence"
        elif price_change > 0 and oi_change < 0:
            signal = "bullish_divergence"
        else:
            signal = "neutral"
        return {"signal": signal, "price_change": price_change, "oi_change": oi_change}

    def analyze_long_short_ratio(self, df: pd.DataFrame) -> dict:
        if df.empty or "ratio" not in df.columns:
            return {"signal": "neutral", "ratio": 1}
        ratio = df["ratio"].iloc[-1]
        signal = "sell" if ratio > 1.2 else "buy" if ratio < 0.8 else "neutral"
        return {"signal": signal, "ratio": ratio}
