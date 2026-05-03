"""Domain models — assets and news events."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Asset:
    ticker: str
    name: str
    starting_price: float
    drift: float
    volatility: float
    flavor: str
    description: str


@dataclass
class NewsEvent:
    template: str
    ticker_pool: list[str] | str
    impact_min: float
    impact_max: float
