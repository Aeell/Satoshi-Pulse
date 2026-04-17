# Satoshi Pulse v2 — Developer / Agent Guide

This file is the **primary reference for AI coding agents and human developers**
working inside this repository. It documents the v2 architecture, every module,
known fixed bugs, and outstanding work.

> If you are new to the project, read this file first, then `README.md` for a
> user-facing overview, and `CONTRIBUTING.md` for the contribution workflow.

---

## 1. What this project is

Satoshi Pulse v2 is a full-stack crypto analysis platform that:

1. **Collects** market, on-chain, DeFi, derivatives, sentiment and news data
   from **free public APIs** (no paid Glassnode subscription).
2. **Stores** it in SQLite (dev) or PostgreSQL + TimescaleDB (prod) through
   SQLAlchemy 2.0 **async** ORM.
3. **Analyses** it with a technical-indicator layer (pandas-ta, 40+ indicators)
   and generates composite **trading signals**.
4. **Serves** everything via a **FastAPI** backend and a **React + Vite +
   TypeScript + Tremor** dashboard.
5. Optionally exposes signals to **Freqtrade** (integration is **isolated and
   NOT wired** by default — see §7).

---

## 2. Entry points

| Command | What it does |
|---------|--------------|
| `python -m src api` | FastAPI server only (port 8000) |
| `python -m src scheduler` | Async scheduler → runs every enabled collector in a loop |
| `python -m src full` | API + scheduler concurrently (single process) |
| `make run-api` / `make run-scheduler` / `make run-full` | Same, with `DB_USE_SQLITE=true` pre-set |
| `make test` | Run `pytest tests/ -v` |
| `make lint` / `make format` | Ruff check / format |
| `make docker-up` / `make docker-down` | Full TimescaleDB stack via docker-compose |

Module entry: `src/__main__.py`.

---

## 3. Repository layout

```
Satoshi-Pulse/
├── src/
│   ├── __main__.py              # CLI dispatcher (api | scheduler | full)
│   ├── config/
│   │   └── settings.py          # Pydantic BaseSettings — reads .env
│   ├── collectors/
│   │   ├── base.py              # CollectorBase: httpx client, retry, rate limit, status
│   │   ├── market_data.py       # CoinGecko, CoinMarketCap, CCXT (Binance/Gate)
│   │   ├── on_chain.py          # CoinMetrics Community, Santiment (disabled by default)
│   │   ├── defi.py              # DefiLlama, DexScreener
│   │   └── derivatives.py       # Coinalyze, FearGreed, CryptoPanic, WhaleAlert
│   ├── scheduler/
│   │   └── scheduler.py         # Async loop: collect → persist → sleep(interval)
│   ├── storage/
│   │   ├── database.py          # Async engine + session factory (SQLite / Postgres)
│   │   ├── models.py            # SQLAlchemy 2.0 ORM models (see §5)
│   │   ├── writer.py            # persist_dataframe() — routes DFs to tables
│   │   └── processing.py        # Data validation / cleaning helpers
│   ├── analysis/
│   │   ├── technical.py         # 40+ indicators via pandas-ta
│   │   ├── signal_generator.py  # Composite signals from indicator outputs
│   │   └── feature_engine.py    # Feature engineering for ML / signals
│   ├── api/
│   │   ├── main.py              # FastAPI app + lifespan + CORS + routers
│   │   ├── websocket.py         # WS manager (real-time push)
│   │   └── routes/
│   │       ├── dashboard.py     # /api/dashboard/*
│   │       ├── signals.py       # /api/signals/*
│   │       └── status.py        # /api/status/*
│   └── freqtrade_integration/   # ISOLATED — see §7
│       ├── signal_bridge.py
│       ├── strategy.py
│       └── config.py
├── dashboard/                   # React + Vite + TypeScript + Tremor frontend
├── tests/test_core.py           # Core regression suite
├── freqtrade/                   # External Freqtrade install target (empty by default)
├── docker-compose.yml           # timescaledb + api + scheduler + dashboard
├── Dockerfile
├── Makefile
├── pyproject.toml               # deps + ruff + pytest config
├── .env.example                 # All configurable env vars
├── README.md                    # User-facing docs
├── AGENTS.md                    # This file
└── CONTRIBUTING.md              # Contributor workflow
```

---

## 4. Collector architecture

All collectors inherit from **`src/collectors/base.py::CollectorBase`** and
must implement two methods:

```python
async def _fetch(self) -> dict[str, Any]: ...
def _transform(self, data: dict[str, Any]) -> pd.DataFrame: ...
```

`CollectorBase.collect()` handles:

- Enable flag short-circuit
- `_fetch()` with HTTPx, **3-retry with exponential back-off**
- HTTP 429 rate-limit handling
- `_validate()` → `_transform()` into a pandas DataFrame
- `status`, `error_count`, `last_error`, `last_run`, `next_run` tracking
- `get_status()` dict for `/api/status/collectors`

### Registered collectors

| Class | Source | API key required | Default interval (s) |
|-------|--------|------------------|----------------------|
| `CoinGeckoCollector` | api.coingecko.com | demo key in .env | 300 |
| `CoinMarketCapCollector` | pro-api.coinmarketcap.com | **yes** | 3600 |
| `CCXTCollector` | Binance / Gate public endpoints | no (public) | 60 |
| `CoinMetricsCollector` | community-api.coinmetrics.io | no | 86400 |
| `DefiLlamaCollector` | api.llama.fi | no | 21600 |
| `DexScreenerCollector` | api.dexscreener.com | no | 300 |
| `CoinalyzeCollector` | api.coinalyze.net | **yes** | 900 |
| `FearGreedCollector` | api.alternative.me/fng | no | 3600 |
| `CryptoPanicCollector` | cryptopanic.com/api | **yes** | 3600 |
| `WhaleAlertCollector` | api.whale-alert.io | **yes** | 900 |
| `MessariCollector` | api.messari.io | optional | 86400 |

> **Glassnode is intentionally NOT included** — it would require a ~$1 000/mo
> subscription. `tests/test_core.py::test_settings_no_glassnode` enforces this.

All collectors are toggled via `COLLECTOR_*_ENABLED` env variables and
instantiated in `src/scheduler/scheduler.py::Scheduler._build_collectors()`.

---

## 5. Storage (`src/storage/`)

### Database

- Async SQLAlchemy 2.0 engine (`database.py`).
- `DB_USE_SQLITE=true` → `sqlite+aiosqlite:///./data/satoshi_pulse.db`
- Otherwise → `postgresql+asyncpg://…` (TimescaleDB in Docker).
- `db.init()` + `db.create_tables()` are called on startup by both the API
  lifespan and the scheduler.

### ORM models (`models.py`)

`OHLCVCandle`, `TickerSnapshot`, `CoinMetric`, `OnChainMetric`, `ExchangeFlow`,
`DefiTVL`, `DexVolume`, `YieldData`, `OpenInterest`, `FundingRate`,
`Liquidation`, `LongShortRatio`, `FearGreed`, `SocialMetric`, `NewsArticle`,
`TrendingWord`, `WhaleTransaction`, `TradingSignal`, `SignalPerformance`,
`CollectorStatus`.

Most tables have `UniqueConstraint` on `(timestamp, symbol, …)` to make
re-collection idempotent.

### Writer (`writer.py`)

`persist_dataframe(collector_name, df) -> int` dispatches through `_route()`
by collector name prefix:

- `ccxt_*`       → `OHLCVCandle` + `TickerSnapshot`
- `coingecko`    → `CoinMetric`
- `coinmetrics`  → `OnChainMetric`
- `defillama`    → `DefiTVL`
- `fear_greed`   → `FearGreed`
- `whale_alert`  → `WhaleTransaction`
- `cryptopanic`  → `NewsArticle`

Also updates the `CollectorStatus` row on every successful write.

---

## 6. API (`src/api/`)

FastAPI app with lifespan-managed DB, CORS, and three routers:

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `dashboard.py` | `/api/dashboard` | `overview`, `market`, `ohlcv`, `on-chain`, `health` |
| `signals.py`   | `/api/signals`   | `active`, `history`, `performance`, `POST /` |
| `status.py`    | `/api/status`    | `collectors`, `database`, `system` |

Plus `/`, `/health`, `/docs` (Swagger UI).

WebSocket manager lives in `api/websocket.py` (not heavily used yet).

---

## 7. Freqtrade integration — **ISOLATED**

`src/freqtrade_integration/` contains:

- `signal_bridge.py` — polls `/api/signals/active` and pushes to Freqtrade RPC
- `strategy.py` — Freqtrade strategy skeleton
- `config.py` — settings loader

It is **NOT imported anywhere** in `src/__main__.py`, `scheduler`, or `api`.
Wiring it up is an explicit opt-in step:

1. Install Freqtrade in its own virtualenv (it has conflicting deps).
2. Fill `FREQTRADE_*` in `.env`.
3. Uncomment the `freqtrade` service in `docker-compose.yml`.
4. Run `python -m src.freqtrade_integration.signal_bridge` separately.

Do **not** import anything from `freqtrade_integration` into the core app
without also adding Freqtrade to `pyproject.toml` dependencies (it is not
there on purpose).

---

## 8. Configuration

All configuration flows through `src/config/settings.py` via Pydantic
`BaseSettings`, split into nested groups: `DatabaseSettings`, `APISettings`,
`CollectorSettings`, `FreqtradeSettings`. Every field has an env-var prefix
(`DB_`, `API_`, `COLLECTOR_`, `FREQTRADE_`). See `.env.example` for the full
list.

Key local-dev toggle: **`DB_USE_SQLITE=true`** avoids needing PostgreSQL.

---

## 9. Known fixed bugs (regression tests live in `tests/test_core.py`)

- **FearGreed transform** — previously returned an empty DataFrame for the
  singleton response shape from `api.alternative.me/fng`. Fixed; covered by
  `test_fear_greed_transform`.
- **Glassnode references** removed from settings and writer to prevent
  accidental paid-API usage. Enforced by `test_settings_no_glassnode`.
- **Async DB session leak** in scheduler on collector exceptions — `writer.py`
  now opens a fresh session per dataframe and never leaks on error.
- **Rate-limit 429 handling** was previously crashing the whole scheduler —
  `CollectorBase._get()` now does exponential back-off up to 3 attempts.
- **SQLite vs Postgres URL selection** is driven purely by `DB_USE_SQLITE`;
  previously it tried to connect to Postgres even when SQLite was requested.

---

## 10. What is done ✅

- Async collector framework with retry + rate limiting
- 11 collectors, all free-tier
- SQLAlchemy 2.0 async models with uniqueness constraints
- Writer routing for all currently-used collectors
- Scheduler wiring all enabled collectors
- FastAPI with dashboard / signals / status routers + Swagger
- React + Vite + Tremor dashboard
- SQLite zero-config local mode (`make run-full`)
- Docker Compose stack with TimescaleDB
- Ruff + pytest + Makefile + `.env.example`
- Core regression test suite

## 11. What still needs work ⚠️

- **Freqtrade wiring** — module exists but is isolated; needs a separate
  process/service, env validation, and an e2e test.
- **More test coverage** — only `tests/test_core.py` exists. Need per-collector
  transform tests with recorded fixtures, writer round-trip tests, and API
  contract tests for every route.
- **Writer routing gaps** — `dexscreener`, `coinalyze`, `messari`, `santiment`
  currently fall through the `else` branch in `writer._route()` and are logged
  but not persisted. Add dedicated writers.
- **WebSocket push** — `api/websocket.py` exists but is not broadcasting
  collector events. Hook it into the scheduler loop.
- **Alembic migrations** — `alembic` is a dependency but no migration tree is
  initialised; currently we rely on `create_all()`.
- **Signal generator** — `signal_generator.py` generates composite signals but
  nothing yet writes them to `TradingSignal` automatically; the API currently
  reads whatever is inserted manually (or via `POST /api/signals/`).
- **Dashboard auth** — no authentication layer; OK for local dev, not for prod.
- **Rate-limit header awareness** — retry is blind exponential; ideally we
  parse `Retry-After`.
- **Docs** — per-module docstrings are sparse in `analysis/` and
  `freqtrade_integration/`.

---

## 12. Working conventions for agents

- **Never remove** the Glassnode guard test or re-introduce Glassnode.
- **Never import** `src/freqtrade_integration/*` from core code.
- **Never break** the `DB_USE_SQLITE=true` zero-config path — `make run-full`
  must keep working on a fresh clone with no API keys (disable paid-key
  collectors in `.env`).
- **Collectors must be idempotent** — respect the unique constraints in
  `models.py`.
- **Use `ruff`** for formatting and linting (`make format`, `make lint`).
- **Keep `AGENTS.md`, `README.md`, `CONTRIBUTING.md` in sync** — if you add a
  collector, update §4 here, the README table, and the "adding a collector"
  section of `CONTRIBUTING.md`.
- **Tests first for bug fixes** — add a regression test in `tests/test_core.py`
  before the fix when reproducing a reported bug.

---

## 13. Quick troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: src` | Run from repo root, or `pip install -e .` |
| `sqlalchemy.exc.OperationalError` on first run | Set `DB_USE_SQLITE=true` or start the Docker stack |
| `HTTP 401` from CoinMarketCap / Coinalyze / WhaleAlert | Add the API key or set `COLLECTOR_<NAME>_ENABLED=false` |
| Scheduler silent / no rows | Check `/api/status/collectors` — look at `last_error` |
| Dashboard cannot reach API | Set `DASHBOARD_API_URL=http://localhost:8000` |
| pandas-ta install fails on Python 3.12 | Use Python 3.11 or install the pre-release wheel |

---

## 14. Legacy note

An older single-file tool (`bitcoin_exchange_analyzer.py`) and a large whale
archive (`whale-alerts-archive.json.gzip`) may be present in the repo root.
They are **not** part of the v2 runtime and are kept only for historical
reference. Do not import from them.
