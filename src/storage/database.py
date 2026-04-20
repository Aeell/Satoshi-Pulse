import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.config.settings import get_settings
from src.storage.models import Base

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory = None
        self.is_sqlite = self.settings.database.use_sqlite

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine

    @property
    def session_factory(self):
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory

    def init(self) -> None:
        async_url = self.settings.database.async_url

        # aiosqlite manages its own thread; check_same_thread is a sync-sqlite arg only.
        connect_args: dict = {}
        poolclass = NullPool if self.is_sqlite else None

        self._engine = create_async_engine(
            async_url,
            echo=self.settings.debug,
            connect_args=connect_args,
            poolclass=poolclass,
        )

        self._session_factory = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(f"Database initialized: {'SQLite' if self.is_sqlite else 'PostgreSQL'}")

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._session_factory:
            self.init()

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        if not self._engine:
            self.init()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created")

    async def drop_tables(self) -> None:
        if not self._engine:
            self.init()

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Database tables dropped")

    async def create_hypertable(self, table_name: str, time_column: str = "timestamp") -> None:
        if self.is_sqlite:
            logger.warning("Hypertables not supported in SQLite mode")
            return

        from sqlalchemy import text

        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    f"SELECT create_hypertable('{table_name}', '{time_column}',"
                    " if_not_exists => TRUE);"
                )
            )
        logger.info(f"Hypertable created: {table_name}")

    async def setup_timescale(self) -> None:
        if self.is_sqlite:
            logger.warning("Timescale extensions not supported in SQLite mode")
            return

        from sqlalchemy import text

        async with self._engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        logger.info("TimescaleDB extension enabled")


db = Database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db.session() as session:
        yield session
