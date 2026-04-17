import json
from typing import Any


class FreqtradeConfig:
    def __init__(self):
        self.config = {
            "max_open_trades": 3,
            "stake_currency": "USDT",
            "stake_amount": "unlimited",
            "dry_run": True,
            "cancel_trade_on_exit_timeout": {"minutes": 10},
            "unfilledtimeout": {"entry": 10, "exit": 10},
            "entry_pricing": {"price_side": "same", "use_order_book": True, "order_book_top_n": 3},
            "exit_pricing": {"price_side": "same", "use_order_book": True, "order_book_top_n": 3},
            "exchange": {
                "name": "binance",
                "key": "",
                "secret": "",
                "ccxt_config": {},
                "ccxt_config_is_null": True,
            },
            "pair_whitelist": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            "pair_blacklist": [],
            "edge": {"enabled": False},
            "api_server": {
                "enabled": True,
                "listen_address": "0.0.0.0",
                "verbosity": "error",
            },
            "bot_name": "SatoshiPulse",
            "initial_state": "running",
        }

    def set_exchange(
        self,
        name: str = "binance",
        api_key: str = "",
        api_secret: str = "",
        sandbox: bool = False,
    ) -> None:
        self.config["exchange"]["name"] = name
        self.config["exchange"]["key"] = api_key
        self.config["exchange"]["secret"] = api_secret
        self.config["exchange"]["ccxt_config"] = {"testnet": sandbox}

    def set_pairs(
        self,
        whitelist: list[str] = None,
        blacklist: list[str] = None,
    ) -> None:
        if whitelist:
            self.config["pair_whitelist"] = whitelist
        if blacklist:
            self.config["pair_blacklist"] = blacklist

    def set_risk_management(
        self,
        max_open_trades: int = 3,
        max_daily_loss: float = 0.05,
        stake_amount: str = "unlimited",
    ) -> None:
        self.config["max_open_trades"] = max_open_trades
        self.config["stake_amount"] = stake_amount
        max_daily_loss_pct = int(max_daily_loss * 100)
        self.config["max_daily_s"] = f"-{max_daily_loss_pct}"

    def set_api_server(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        api_key: str = "",
    ) -> None:
        self.config["api_server"] = {
            "enabled": True,
            "listen_address": host,
            "port": port,
            "verbosity": "error",
            "enable_openapi": False,
            "jwt_secret_key": api_key or "changeme",
            "ws_token": api_key or "changeme",
        }

    def set_dry_run(self, dry_run: bool = True) -> None:
        self.config["dry_run"] = dry_run

    def to_json(self, filepath: str = None) -> str:
        if filepath:
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)
            return filepath
        return json.dumps(self.config, indent=2)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "FreqtradeConfig":
        instance = cls()
        instance.config.update(config)
        return instance
