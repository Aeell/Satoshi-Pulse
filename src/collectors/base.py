import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


class CollectorBase(ABC):
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 60,
        interval: int = 300,
        enabled: bool = True,
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.interval = interval
        self.enabled = enabled
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._error_count: int = 0
        self._last_error: Optional[str] = None
        self._status: str = "idle"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def last_run(self) -> Optional[datetime]:
        return self._last_run

    @property
    def next_run(self) -> Optional[datetime]:
        return self._next_run

    @property
    def status(self) -> str:
        return self._status

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def get_rate_limit(self) -> int:
        return self.rate_limit

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["X-CG-API-Key"] = self.api_key

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Async context manager wrapper around _get_client for use in collectors."""
        client = await self._get_client()
        yield client

    async def _close_client(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        for attempt in range(3):
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RateLimitException:
                wait_time = self.rate_limit * (2**attempt)
                logger.warning(f"Rate limited, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = self.rate_limit * (2**attempt)
                    logger.warning(f"Rate limited (HTTP 429), waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt == 2:
                    raise
                wait_time = 2**attempt
                logger.warning(f"Error, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        raise RuntimeError("Max retries exceeded")

    async def _post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def _validate(self, data: dict[str, Any]) -> bool:
        return data is not None and len(data) > 0

    async def collect(self) -> pd.DataFrame:
        if not self.enabled:
            return pd.DataFrame()

        self._status = "running"
        start_time = datetime.now()

        try:
            data = await self._fetch()
            if self._validate(data):
                df = self._transform(data)
                self._status = "completed"
            else:
                df = pd.DataFrame()
                self._status = "completed_empty"

            self._error_count = 0
            self._last_error = None

        except Exception as e:
            self._status = "error"
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Collector {self.name} failed: {e}")
            raise

        finally:
            self._last_run = start_time
            self._next_run = datetime.now() + timedelta(seconds=self.interval)

        return df

    @abstractmethod
    async def _fetch(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def _transform(self, data: dict[str, Any]) -> pd.DataFrame:
        pass

    async def close(self) -> None:
        await self._close_client()

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "status": self._status,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "enabled": self.enabled,
        }
