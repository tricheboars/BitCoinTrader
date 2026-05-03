"""News wire — schedules random market-moving headlines."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from bitcointrader.market.model import NewsEvent

if TYPE_CHECKING:
    from bitcointrader.engine.tick import MarketEngine


class NewsScheduler:
    def __init__(self, events: list[NewsEvent], market: "MarketEngine"):
        self.events = events
        self.market = market

    def next_delay(self) -> float:
        return random.uniform(30.0, 90.0)

    def fire(self) -> dict:
        event = random.choice(self.events)
        if event.ticker_pool == "all":
            ticker = "ALL"
        elif event.ticker_pool == "random":
            ticker = random.choice(list(self.market.assets.keys()))
        else:
            pool = [t for t in event.ticker_pool if t in self.market.assets]
            if not pool:
                ticker = random.choice(list(self.market.assets.keys()))
            else:
                ticker = random.choice(pool)

        impact = random.uniform(event.impact_min, event.impact_max)
        headline = event.template.replace("$TICKER", ticker)

        if ticker == "ALL":
            for t in self.market.prices:
                self.market.prices[t] = max(self.market.prices[t] * impact, 0.0001)
        else:
            self.market.prices[ticker] = max(self.market.prices[ticker] * impact, 0.0001)

        return {"headline": headline, "ticker": ticker, "impact": impact}
