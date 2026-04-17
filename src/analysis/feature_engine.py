import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngine:
    def __init__(self):
        pass

    def calculate_composite_bull_score(
        self,
        technical_score: float,
        onchain_score: float,
        sentiment_score: float,
        derivatives_score: float,
    ) -> pd.Series:
        weights = {"technical": 0.40, "onchain": 0.30, "sentiment": 0.20, "derivatives": 0.10}
        return (
            technical_score * weights["technical"]
            + onchain_score * weights["onchain"]
            + sentiment_score * weights["sentiment"]
            + derivatives_score * weights["derivatives"]
        )

    def calculate_whale_pressure(
        self,
        whale_df: pd.DataFrame,
    ) -> float:
        if whale_df.empty:
            return 0.0

        amounts = whale_df["amount"].values if "amount" in whale_df.columns else []
        usd_values = whale_df["usd_value"].values if "usd_value" in whale_df.columns else []

        if len(usd_values) == 0:
            return 0.0

        total_volume = np.sum(usd_values)
        net_flow = np.sum(amounts)

        if net_flow < 0:
            return total_volume
        return -total_volume

    def calculate_smart_money_divergence(
        self,
        price_trend: float,
        onchain_health: float,
    ) -> float:
        if onchain_health > 0.6 and price_trend < 0:
            return 1.0
        elif onchain_health < 0.4 and price_trend > 0:
            return -1.0
        return price_trend - (onchain_health - 0.5) * 2

    def calculate_fear_greed_zscore(
        self,
        current_value: float,
        historical_mean: float,
        historical_std: float,
    ) -> float:
        if historical_std == 0:
            return 0.0
        return (current_value - historical_mean) / historical_std

    def calculate_oi_price_divergence(
        self,
        oi_trend: float,
        price_trend: float,
    ) -> float:
        if oi_trend > 0 and price_trend > 0:
            return 1.0
        elif oi_trend > 0 and price_trend < 0:
            return -1.0
        elif oi_trend < 0 and price_trend > 0:
            return -0.5
        return 0.0

    def calculate_funding_percentile(
        self,
        current_rate: float,
        historical_rates: list[float],
    ) -> float:
        if not historical_rates:
            return 0.5

        sorted_rates = sorted(historical_rates)
        position = sum(1 for r in sorted_rates if r < current_rate)
        return position / len(sorted_rates)

    def calculate_liquidity_health(
        self,
        dex_liquidity: float,
        exchange_depth: float,
    ) -> float:
        return (dex_liquidity + exchange_depth) / 2

    def calculate_macro_defi_score(
        self,
        tvl_trend: float,
        stablecoin_flow: float,
    ) -> float:
        return (tvl_trend + stablecoin_flow) / 2

    def calculate_target_variable(
        self,
        prices: pd.Series,
        forward_periods: int = 24,
    ) -> pd.Series:
        return prices.pct_change(forward_periods).shift(-forward_periods)

    def get_feature_importance(self, features: list[str]) -> dict[str, float]:
        importance = {
            "composite_bull_score": 0.25,
            "whale_pressure_score": 0.15,
            "smart_money_divergence": 0.15,
            "fear_greed_zscore": 0.10,
            "oi_price_divergence": 0.10,
            "funding_rate_percentile": 0.10,
            "liquidity_health": 0.10,
            "macro_defi_score": 0.05,
        }
        return {k: v for k, v in importance.items() if k in features}


class CorrelationAnalyzer:
    def __init__(self):
        pass

    def calculate_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
    ) -> float:
        return series1.corr(series2)

    def analyze_btc_correlations(
        self,
        btc_prices: pd.Series,
        other_prices: pd.DataFrame,
    ) -> dict[str, float]:
        correlations = {}
        for col in other_prices.columns:
            correlations[col] = self.calculate_correlation(btc_prices, other_prices[col])
        return correlations

    def analyze_onchain_price_lead(
        self,
        onchain_metrics: pd.DataFrame,
        prices: pd.Series,
    ) -> dict[str, float]:
        correlations = {}
        for col in onchain_metrics.columns:
            correlations[col] = self.calculate_correlation(onchain_metrics[col], prices)
        return correlations

    def analyze_sentiment_price_lead(
        self,
        sentiment: pd.DataFrame,
        prices: pd.Series,
    ) -> dict[str, float]:
        correlations = {}
        for col in sentiment.columns:
            correlations[col] = self.calculate_correlation(sentiment[col], prices)
        return correlations
