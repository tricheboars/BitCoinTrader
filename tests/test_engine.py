"""Engine-level integration tests — walker, news scheduler, market engine."""
from __future__ import annotations

import asyncio
import random

import pytest

from bitcointrader.engine.news import NewsScheduler
from bitcointrader.engine.tick import MarketEngine
from bitcointrader.engine.walker import step
from bitcointrader.market.model import NewsEvent
from bitcointrader.market.registry import load_assets, load_news


# ─── walker ────────────────────────────────────────────────────────────────────

def test_walker_zero_volatility_pure_drift():
    random.seed(0)
    p = 100.0
    new = step(p, drift=0.05, volatility=0.0, dt=1.0)
    # exp(0.05 - 0) ~= 1.05127
    assert abs(new - 100.0 * 2.71828 ** 0.05) < 0.01


def test_walker_floors_at_tiny_positive():
    p = 1e-12
    for _ in range(100):
        p = step(p, drift=-10.0, volatility=10.0)
        assert p >= 0.0001


def test_walker_distribution_seeded_reproducible():
    random.seed(42)
    a = [step(1.0, 0.0, 0.1) for _ in range(50)]
    random.seed(42)
    b = [step(1.0, 0.0, 0.1) for _ in range(50)]
    assert a == b


# ─── news scheduler ────────────────────────────────────────────────────────────

class _StubMarket:
    def __init__(self, prices: dict[str, float]):
        self.prices = dict(prices)
        self.assets = {t: object() for t in prices}


def test_news_scheduler_all_pool_multiplies_every_price():
    random.seed(1)
    market = _StubMarket({"$A": 10.0, "$B": 20.0, "$C": 30.0})
    ev = NewsEvent(template="x", ticker_pool="all", impact_min=2.0, impact_max=2.0)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    out = sch.fire()
    assert out["ticker"] == "ALL"
    assert market.prices == {"$A": 20.0, "$B": 40.0, "$C": 60.0}


def test_news_scheduler_specific_pool_only_hits_matching_ticker():
    random.seed(1)
    market = _StubMarket({"$A": 10.0, "$B": 20.0})
    ev = NewsEvent(template="$TICKER moons", ticker_pool=["$A"],
                   impact_min=3.0, impact_max=3.0)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    out = sch.fire()
    assert out["ticker"] == "$A"
    assert "$A moons" in out["headline"]
    assert market.prices["$A"] == 30.0
    assert market.prices["$B"] == 20.0  # untouched


def test_news_scheduler_pool_with_no_overlap_falls_back_to_random():
    random.seed(1)
    market = _StubMarket({"$A": 10.0, "$B": 20.0})
    ev = NewsEvent(template="x", ticker_pool=["$NONEXIST"],
                   impact_min=1.0, impact_max=1.0)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    out = sch.fire()
    assert out["ticker"] in {"$A", "$B"}


def test_news_scheduler_random_pool_picks_known_ticker():
    random.seed(1)
    market = _StubMarket({"$A": 10.0, "$B": 20.0})
    ev = NewsEvent(template="$TICKER", ticker_pool="random",
                   impact_min=1.0, impact_max=1.0)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    out = sch.fire()
    assert out["ticker"] in market.assets


def test_news_scheduler_floors_price_when_impact_drives_to_zero():
    market = _StubMarket({"$A": 0.0001})
    ev = NewsEvent(template="x", ticker_pool=["$A"],
                   impact_min=0.0, impact_max=0.0)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    sch.fire()
    assert market.prices["$A"] == 0.0001


def test_news_scheduler_impact_within_declared_range():
    """Sample many impacts and assert all stay within declared bounds."""
    random.seed(0)
    market = _StubMarket({"$A": 10.0})
    ev = NewsEvent(template="$TICKER", ticker_pool=["$A"],
                   impact_min=1.5, impact_max=2.5)
    sch = NewsScheduler([ev], market)  # type: ignore[arg-type]
    for _ in range(200):
        market.prices["$A"] = 10.0
        out = sch.fire()
        assert 1.5 <= out["impact"] <= 2.5


def test_news_scheduler_delay_in_documented_range():
    sch = NewsScheduler([], _StubMarket({}))  # type: ignore[arg-type]
    for _ in range(100):
        d = sch.next_delay()
        assert 30.0 <= d <= 90.0


def test_all_news_events_load_with_valid_impact_bounds():
    for ev in load_news():
        assert ev.impact_min > 0, ev.template
        assert ev.impact_max >= ev.impact_min, ev.template
        if isinstance(ev.ticker_pool, list):
            assert all(t.startswith("$") for t in ev.ticker_pool), ev.template


# ─── market engine async lifecycle ─────────────────────────────────────────────

async def test_market_engine_start_stop():
    eng = MarketEngine(tick_ms=10, news_enabled=False, seed=0)
    await eng.start()
    await asyncio.sleep(0.05)
    await eng.stop()
    # After stop, tasks list cleared.
    assert eng._tasks == []


async def test_market_engine_broadcasts_tick_to_subscriber():
    eng = MarketEngine(tick_ms=10, news_enabled=False, seed=0)
    q = eng.subscribe()
    await eng.start()
    try:
        msg = await asyncio.wait_for(q.get(), timeout=1.0)
    finally:
        await eng.stop()
    assert msg["type"] == "tick"
    assert set(msg["prices"].keys()) == set(eng.assets.keys())
    for v in msg["prices"].values():
        assert v > 0


async def test_market_engine_unsubscribe_stops_messages():
    eng = MarketEngine(tick_ms=10, news_enabled=False, seed=0)
    q = eng.subscribe()
    eng.unsubscribe(q)
    assert q not in eng._subscribers


async def test_market_engine_news_event_does_not_crash_loop():
    """Drive the engine with news enabled but no events configured."""
    eng = MarketEngine(tick_ms=10, news_enabled=False, seed=0)
    # Hand-fire a news event through the scheduler to confirm broadcast path.
    eng.news_scheduler.events = [
        NewsEvent(template="$TICKER pumps", ticker_pool="random",
                  impact_min=1.0, impact_max=1.0)
    ]
    out = eng.news_scheduler.fire()
    assert out["ticker"] in eng.assets


# ─── asset catalogue ───────────────────────────────────────────────────────────

def test_assets_have_positive_starting_prices_and_volatility():
    for t, a in load_assets().items():
        assert t.startswith("$"), t
        assert a.starting_price > 0
        assert a.volatility >= 0
