from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Shared config — all sub-models point at the same .env file
_ENV_FILE = ".env"
_ENV_ENC = "utf-8"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_ENC,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    name: str = "satoshi_pulse"
    user: str = "postgres"
    password: str = "postgres"
    use_sqlite: bool = True  # default ON — zero-config local dev
    sqlite_path: str = "./data/satoshi_pulse.db"

    @property
    def async_url(self) -> str:
        if self.use_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_ENC,
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    ws_enabled: bool = True


class CollectorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COLLECTOR_",
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_ENC,
        extra="ignore",
    )

    coingecko_enabled: bool = True
    coingecko_interval: int = 300

    coinmarketcap_enabled: bool = False  # needs API key
    coinmarketcap_interval: int = 3600

    ccxt_enabled: bool = True
    ccxt_interval: int = 60
    ccxt_priority_exchanges: list[str] = ["binance"]

    coinmetrics_enabled: bool = True
    coinmetrics_interval: int = 86400

    santiment_enabled: bool = False
    santiment_interval: int = 21600

    defillama_enabled: bool = True
    defillama_interval: int = 21600

    dexscreener_enabled: bool = True
    dexscreener_interval: int = 300

    coinalyze_enabled: bool = False  # needs API key
    coinalyze_interval: int = 900

    fear_greed_enabled: bool = True
    fear_greed_interval: int = 3600

    cryptopanic_enabled: bool = False  # needs API key
    cryptopanic_interval: int = 3600

    whale_alert_enabled: bool = False  # needs API key
    whale_alert_interval: int = 900

    messari_enabled: bool = False  # needs API key
    messari_interval: int = 86400


class FreqtradeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FREQTRADE_",
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_ENC,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 8080
    ws_port: int = 8081
    api_key: str = ""
    rpc_url: str = "http://localhost:8080"
    strategy_mode: str = "webhook"
    dry_run: bool = True

    max_position_size: float = 0.02
    max_total_exposure: float = 0.20
    max_daily_loss: float = 0.05
    max_consecutive_losses: int = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding=_ENV_ENC,
        extra="ignore",
    )

    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    collector: CollectorSettings = CollectorSettings()
    freqtrade: FreqtradeSettings = FreqtradeSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
