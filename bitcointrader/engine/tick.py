"""Market engine — ticks prices, fires news, broadcasts to subscribers."""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

from bitcointrader.engine.news import NewsScheduler
from bitcointrader.engine.walker import step
from bitcointrader.market.registry import load_assets, load_news

log = logging.getLogger(__name__)


class MarketEngine:
    def __init__(self, tick_ms: int = 5000, news_enabled: bool = True, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
        self.assets = load_assets()
        self.prices: dict[str, float] = {t: a.starting_price for t, a in self.assets.items()}
        self.tick_ms = tick_ms
        self.news_enabled = news_enabled
        self.news_scheduler = NewsScheduler(load_news(), self)
        self._subscribers: list[asyncio.Queue] = []
        self._tasks: list[asyncio.Task] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def broadcast(self, msg: dict) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    async def start(self) -> None:
        self._tasks.append(asyncio.create_task(self._tick_loop()))
        if self.news_enabled:
            self._tasks.append(asyncio.create_task(self._news_loop()))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()

    async def _tick_loop(self) -> None:
        while True:
            await asyncio.sleep(self.tick_ms / 1000)
            for ticker, asset in self.assets.items():
                self.prices[ticker] = step(self.prices[ticker], asset.drift, asset.volatility)
            await self.broadcast({
                "type": "tick",
                "prices": dict(self.prices),
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            })

    async def _news_loop(self) -> None:
        while True:
            await asyncio.sleep(self.news_scheduler.next_delay())
            try:
                event = self.news_scheduler.fire()
            except Exception as e:
                log.exception("news event failed: %s", e)
                continue
            await self.broadcast({"type": "news", **event})
