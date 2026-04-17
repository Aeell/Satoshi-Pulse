import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.storage.database import db

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Satoshi Pulse API")
    db.init()
    await db.create_tables()
    yield
    await db.close()
    logger.info("Shutting down Satoshi Pulse API")


app = FastAPI(
    title="Satoshi Pulse API",
    description="Crypto analysis platform API with signals for Freqtrade",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"name": "Satoshi Pulse", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


from src.api.routes import dashboard, signals, status

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
