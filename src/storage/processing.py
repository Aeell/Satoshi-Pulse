import logging
from datetime import datetime
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    @staticmethod
    def validate_timestamp(ts: Any) -> Optional[datetime]:
        if ts is None:
            return None
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts)
        try:
            return pd.to_datetime(ts)
        except Exception:
            logger.warning(f"Invalid timestamp: {ts}")
            return None

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        if not symbol:
            return "UNKNOWN"
        return symbol.upper().strip()

    @staticmethod
    def validate_price(price: Any) -> Optional[float]:
        if price is None:
            return None
        try:
            return float(price)
        except (ValueError, TypeError):
            logger.warning(f"Invalid price value: {price}")
            return None

    @staticmethod
    def validate_positive(value: float, name: str = "value") -> bool:
        if value is None or value < 0:
            logger.warning(f"Invalid {name}: must be positive, got {value}")
            return False
        return True

    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, name: str = "value") -> bool:
        if value is None:
            return False
        if not (min_val <= value <= max_val):
            logger.warning(f"Invalid {name}: {value} not in range [{min_val}, {max_val}]")
            return False
        return True


class DataProcessor:
    @staticmethod
    def deduplicate(
        df: pd.DataFrame,
        keys: list[str],
        keep: str = "first",
    ) -> pd.DataFrame:
        if df.empty:
            return df
        return df.drop_duplicates(subset=keys, keep=keep)

    @staticmethod
    def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower().str.replace(" ", "_")
        return df

    @staticmethod
    def add_source_column(df: pd.DataFrame, source: str) -> pd.DataFrame:
        df["source"] = source
        return df

    @staticmethod
    def fill_missing_timestamps(
        df: pd.DataFrame,
        timestamp_col: str,
        freq: str = "1min",
    ) -> pd.DataFrame:
        if df.empty or timestamp_col not in df.columns:
            return df
        idx = pd.date_range(df[timestamp_col].min(), df[timestamp_col].max(), freq=freq)
        return (
            df.set_index(timestamp_col)
            .reindex(idx, method="ffill")
            .reset_index()
            .rename(columns={"index": timestamp_col})
        )

    @staticmethod
    def calculate_pct_change(series: pd.Series) -> pd.Series:
        return series.pct_change() * 100

    @staticmethod
    def calculate_rolling_mean(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window).mean()

    @staticmethod
    def calculate_rolling_std(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window).std()


class DataQuality:
    @staticmethod
    def calculate_completeness(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        total_cells = df.size
        if total_cells == 0:
            return 0.0
        non_null_cells = df.count().sum()
        return non_null_cells / total_cells

    @staticmethod
    def get_null_counts(df: pd.DataFrame) -> dict[str, int]:
        return df.isnull().sum().to_dict()

    @staticmethod
    def get_outliers(series: pd.Series, n_std: float = 3.0) -> pd.Series:
        mean = series.mean()
        std = series.std()
        return series[(series < mean - n_std * std) | (series > mean + n_std * std)]
