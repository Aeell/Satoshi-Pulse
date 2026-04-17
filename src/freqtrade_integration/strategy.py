from typing import Optional

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class SatoshiCompositeStrategy(IStrategy):
    timeframe = "1h"
    minimal_roi = {"0": 0.02}
    stoploss = -0.03

    params = {
        "buy_threshold": 60,
        "sell_threshold": 40,
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        from src.analysis.technical import TechnicalAnalyzer

        analyzer = TechnicalAnalyzer()
        dataframe = analyzer.calculate_indicators(dataframe)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.params.get("buy_threshold", 60)

        dataframe.loc[
            (dataframe["rsi"] < 35) & (dataframe["close"] > dataframe["sma_21"]),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.params.get("sell_threshold", 40)

        dataframe.loc[
            (dataframe["rsi"] > 65) | (dataframe["close"] < dataframe["sma_21"]),
            "exit_long",
        ] = 1

        return dataframe


class OnChainWhaleStrategy(IStrategy):
    timeframe = "4h"
    minimal_roi = {"0": 0.03}
    stoploss = -0.05

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["close"] > dataframe["close"].shift(1),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["close"] < dataframe["close"].shift(1),
            "exit_long",
        ] = 1

        return dataframe


class SentimentReversalStrategy(IStrategy):
    timeframe = "1h"
    minimal_roi = {"24": 0.01}
    stoploss = -0.02

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["close"] < dataframe["close"].rolling(20).mean() * 0.95,
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["close"] > dataframe["close"].rolling(20).mean() * 1.05,
            "exit_long",
        ] = 1

        return dataframe


class DerivativesAlphaStrategy(IStrategy):
    timeframe = "15m"
    minimal_roi = {"0": 0.015}
    stoploss = -0.025

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        from src.analysis.technical import TechnicalAnalyzer

        analyzer = TechnicalAnalyzer()
        dataframe = analyzer.calculate_indicators(dataframe)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["macd"] > dataframe["macd_signal"])
            & (dataframe["volume"] > dataframe["volume"].rolling(20).mean()),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["macd"] < dataframe["macd_signal"])
            & (dataframe["volume"] > dataframe["volume"].rolling(20).mean()),
            "exit_long",
        ] = 1

        return dataframe
