"""FastAPI app — serves the static frontend and brokers WS sessions."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bitcointrader.engine.tick import MarketEngine
from bitcointrader.server import config
from bitcointrader.server.session import TraderSession

WEBSITE_DIR = Path(__file__).resolve().parent.parent.parent / "website"


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = MarketEngine(
        tick_ms=config.TICK_MS,
        news_enabled=config.NEWS_ENABLED,
        seed=config.SEED,
    )
    await engine.start()
    app.state.market = engine
    try:
        yield
    finally:
        await engine.stop()


app = FastAPI(title="BitCoinTrader", lifespan=lifespan)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEBSITE_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = TraderSession(app.state.market, ws)
    await session.run()


app.mount("/static", StaticFiles(directory=WEBSITE_DIR), name="static")
