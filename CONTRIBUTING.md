# Contributing to Satoshi Pulse v2

Thanks for your interest in improving Satoshi Pulse. This guide explains how
the project is organised, how to set up a dev environment, and the conventions
you should follow when opening a pull request.

> If you are an AI coding agent, read **`AGENTS.md`** first — it contains the
> architectural rules and invariants that **must not** be violated.

---

## 1. Project structure

The repository is laid out like this (abbreviated — see `AGENTS.md` §3 for the
full tree):

```
Satoshi-Pulse/
├── src/
│   ├── __main__.py           # CLI: api | scheduler | full
│   ├── config/settings.py    # Pydantic settings read from .env
│   ├── collectors/           # One file per data-source family
│   ├── scheduler/            # Async collection loop
│   ├── storage/              # Async SQLAlchemy models + writer
│   ├── analysis/             # Indicators + signal generator
│   ├── api/                  # FastAPI app + routes + websocket
│   └── freqtrade_integration/# ISOLATED — do not import from core
├── dashboard/                # React + Vite + Tremor frontend
├── tests/                    # pytest (async) suite
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── README.md                 # User-facing docs
├── AGENTS.md                 # Architectural reference for devs/agents
└── CONTRIBUTING.md           # This file
```

---

## 2. Development setup

### Prerequisites

- Python **3.11** (3.12 works but `pandas-ta` may need a pre-release wheel)
- `pip` or `uv`
- Node 20+ and `npm` (only if you touch `dashboard/`)
- Docker (optional — required for the full TimescaleDB stack)

### Install

```bash
git clone https://github.com/Aeell/Satoshi-Pulse.git
cd Satoshi-Pulse
pip install -e ".[dev]"
cp .env.example .env
```

For a zero-key, zero-Docker local run:

```env
DB_USE_SQLITE=true
COLLECTOR_COINMARKETCAP_ENABLED=false
COLLECTOR_COINALYZE_ENABLED=false
COLLECTOR_WHALE_ALERT_ENABLED=false
COLLECTOR_CRYPTOPANIC_ENABLED=false
```

Then:

```bash
make run-full        # API + scheduler, SQLite
```

The API will be on `http://localhost:8000/docs`.

---

## 3. Running tests

```bash
make test                    # pytest tests/ -v
pytest tests/test_core.py -k fear_greed -v   # one test
```

The suite currently ships **13 tests** in `tests/test_core.py`, all passing
with **0 warnings** and **0 lint errors**. It uses `pytest-asyncio` in `auto`
mode (see `pyproject.toml`); when adding async tests, just write
`async def test_...()` — no decorator needed. Use `asyncio.run()` rather than
the deprecated `asyncio.get_event_loop()` when you need to drive an async
helper from a sync test.

**Regression-first policy:** when you fix a bug, add the failing test in
`tests/test_core.py` (or a new `tests/test_<area>.py`) **before** the fix, and
reference it in the `AGENTS.md` §9 bug list.

---

## 4. Code style

We use **ruff** for both linting and formatting. Configuration is in
`pyproject.toml`:

- `line-length = 100`
- `target-version = "py311"`
- Rule sets: `E`, `F`, `I`, `N`, `W`, `UP` (pycodestyle, pyflakes, import
  sort, naming, warnings, pyupgrade)
- Ignored: `E501` (line length — already enforced by formatter)

Commands:

```bash
make format     # ruff format src tests   (writes)
make lint       # ruff check  src tests   (read-only)
```

Type hints are expected on new public functions. Prefer the built-in generic
syntax (`list[str]`, `dict[str, Any]`) over `typing.List`/`Dict`.

Imports should be sorted by ruff's `I` rule — don't fight it.

---

## 5. Adding a new collector

A collector is a subclass of `src/collectors/base.py::CollectorBase`. Walk
through the checklist below; every step is **required** for the collector to
actually persist data.

### 5.1 Implement the collector

Create `src/collectors/my_source.py`:

```python
from typing import Any
import pandas as pd
from src.collectors.base import CollectorBase


class MySourceCollector(CollectorBase):
    def __init__(self, interval: int = 3600, api_key: str | None = None):
        super().__init__(
            name="my_source",                       # must be unique & snake_case
            base_url="https://api.example.com",
            api_key=api_key,
            rate_limit=60,
            interval=interval,
        )

    async def _fetch(self) -> dict[str, Any]:
        return await self._get("/v1/endpoint", params={"limit": 100})

    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        # Return a DataFrame with columns your writer understands.
        return pd.DataFrame(data.get("items", []))
```

Rules:

- **Do not** open your own `httpx.AsyncClient` — use `self._get()` /
  `self._post()` so you inherit the 3-retry + 429 back-off logic.
- If you genuinely need a raw client (e.g. non-GET flows, streaming), use
  `async with self._session() as client:`. **Never** do
  `async with self._get_client() as client:` — `_get_client()` returns a
  plain `httpx.AsyncClient` and is **not** an async context manager. This
  footgun has already caused four separate regressions (see `AGENTS.md` §9).
- Return an **empty DataFrame** (not `None`) when there is no data.
- The `name` attribute is how the writer routes rows — keep it stable.

### 5.2 Add settings

In `src/config/settings.py` → `CollectorSettings`, add:

```python
my_source_enabled: bool = True
my_source_interval: int = 3600
```

And in `.env.example`:

```env
COLLECTOR_MY_SOURCE_ENABLED=true
COLLECTOR_MY_SOURCE_INTERVAL=3600
MY_SOURCE_API_KEY=your_key_here
```

### 5.3 Wire it into the scheduler

In `src/scheduler/scheduler.py::_build_collectors()`:

```python
if s.my_source_enabled:
    collectors.append(MySourceCollector(interval=s.my_source_interval))
```

And import it at the top of the file.

### 5.4 Add a writer route

In `src/storage/writer.py::_route()`, add a branch **before** the `else`:

```python
elif name == "my_source":
    return await _write_my_source(df, session)
```

Implement `_write_my_source()` following the pattern of `_write_fear_greed()`:
iterate rows, build ORM objects from `src/storage/models.py`, `session.add()`
them. If you need a new table, add it to `models.py` with a
`UniqueConstraint` on `(timestamp, …)` so re-collection is idempotent, and
regenerate `create_all()` by just restarting the app (no Alembic yet).

### 5.5 Update docs

- `README.md` — add a row to the data-sources table.
- `AGENTS.md` §4 — add a row to the collector table.
- This file — no change needed unless the pattern itself evolved.

### 5.6 Add a transform test

In `tests/test_core.py` (or a new file), feed a recorded JSON sample into
`_transform()` and assert the returned DataFrame schema/rows. Do **not** hit
the live API in tests.

---

## 6. Database changes

Today we use `Base.metadata.create_all()` on startup — there are no Alembic
migrations yet. That means:

- Adding a **new** table → just define the model, restart, it appears.
- Changing an **existing** table → will **not** propagate to existing
  databases. Either drop the table manually in dev, or wait until Alembic is
  wired (tracked in `AGENTS.md` §11).

When Alembic is introduced, this section will be updated with the migration
workflow. Until then, flag schema changes clearly in your PR description.

---

## 7. Frontend (`dashboard/`)

### Dashboard development

The dashboard is a standalone npm workspace. It is **not** installed by
`pip install -e ".[dev]"` — you must run `npm install` inside `dashboard/`
at least once before `npm run dev`, otherwise you'll hit a blank page with
module-resolution errors in the browser console.

```bash
cd dashboard
npm install        # required on a fresh clone, and after any package.json change
npm run dev        # http://localhost:3000
npm run build
npm run lint
```

Vite is configured to proxy `/api/*` to the FastAPI backend on
`http://localhost:8000`, so start the API first (`make run-full` or
`make run-api`) in another terminal. You can override the target with
`DASHBOARD_API_URL`.

- Stack: React 18 + Vite + TypeScript + **`@tremor/react`** + TanStack Query
  + Zustand + React Router v6.
- All API calls go through the typed helpers in `dashboard/src/api.ts`; every
  page is a `useQuery` with an auto-refresh interval — don't `fetch()`
  directly from components.
- Layout is driven by `Layout.tsx` + `<Outlet />` (React Router v6 pattern),
  dark theme by default.
- Keep components typed; avoid `any` unless interoperating with untyped libs.

---

## 8. Pull request process

1. **Branch** off `main`: `git checkout -b feat/my-collector` (or
   `fix/…`, `docs/…`, `test/…`).
2. **Small, focused PRs.** One collector, one bug, one refactor — not all at
   once.
3. **Run locally before pushing:**
   ```bash
   make format
   make lint
   make test
   ```
4. **Commit style** — short imperative subject, optional body. Examples:
   - `feat(collectors): add Binance funding-rate collector`
   - `fix(writer): handle NaN usd_value in whale rows`
   - `docs: sync AGENTS.md with new collector`
5. **PR description** must cover:
   - What changed and **why**
   - Any new env vars (update `.env.example`)
   - Any schema changes (see §6)
   - Test evidence (`pytest` output, screenshots for dashboard changes)
6. **Do not commit secrets.** The `.env` file is git-ignored; keep it that
   way. API keys in `.env.example` must be placeholders.
7. **Keep the SQLite zero-config path green.** `make run-full` on a fresh
   clone with paid-key collectors disabled must still start cleanly.

---

## 9. Hard rules (see `AGENTS.md` §12)

These are non-negotiable. PRs violating them will be rejected.

- ❌ Do not re-introduce **Glassnode** or any paid-only data source.
- ❌ Do not import `src/freqtrade_integration/*` from core code.
- ❌ Do not break the `DB_USE_SQLITE=true` zero-config run.
- ✅ Collectors must be **idempotent** (respect unique constraints).
- ✅ Every bug fix ships with a regression test.
- ✅ `AGENTS.md`, `README.md`, and this file stay in sync.

---

## 10. Getting help

- Open a GitHub issue with logs and the output of `/api/status/collectors`.
- For architectural questions, reference the relevant section of `AGENTS.md`
  so reviewers have shared context.

Happy hacking.
