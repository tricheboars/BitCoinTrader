"""Smoke tests — make sure the engine boots and trades work."""
from bitcointrader.engine.walker import step
from bitcointrader.market.registry import load_assets, load_news
from bitcointrader.trader.portfolio import Portfolio


def test_assets_load():
    assets = load_assets()
    assert len(assets) == 10
    assert "$BTCN" in assets
    assert assets["$BTCN"].starting_price == 1.00


def test_news_load():
    events = load_news()
    assert len(events) > 0
    for e in events:
        assert e.template
        assert e.impact_min > 0
        assert e.impact_max >= e.impact_min


def test_walker_stays_positive():
    p = 1.0
    for _ in range(1000):
        p = step(p, drift=-0.1, volatility=0.5)
        assert p > 0


def test_portfolio_buy_sell():
    pf = Portfolio(cash=10000.0)
    msg = pf.buy("$BTCN", 5000.0, 1.0)
    assert "BUY" in msg
    assert pf.cash == 5000.0
    assert "$BTCN" in pf.positions
    assert pf.positions["$BTCN"].shares == 5000.0

    msg = pf.sell("$BTCN", 2500.0, 2.0)
    assert "SELL" in msg
    assert pf.cash == 10000.0
    assert pf.positions["$BTCN"].shares == 2500.0


def test_portfolio_insufficient_funds():
    pf = Portfolio(cash=100.0)
    msg = pf.buy("$BTCN", 500.0, 1.0)
    assert "INSUFFICIENT" in msg
    assert pf.cash == 100.0
