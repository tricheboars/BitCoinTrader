"""Portfolio edge cases — accounting, greed clamp, sell-all, error paths."""
from __future__ import annotations

import math

from bitcointrader.trader.portfolio import Portfolio


def test_buy_zero_or_negative_dollars_rejected():
    pf = Portfolio(cash=1000.0)
    assert "positive" in pf.buy("$X", 0.0, 1.0).lower()
    assert "positive" in pf.buy("$X", -10.0, 1.0).lower()
    assert pf.cash == 1000.0
    assert pf.positions == {}


def test_buy_with_exact_cash_works():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 100.0, 2.0)
    assert pf.cash == 0.0
    assert pf.positions["$X"].shares == 50.0


def test_buy_more_than_cash_rejected():
    pf = Portfolio(cash=50.0)
    msg = pf.buy("$X", 100.0, 1.0)
    assert "INSUFFICIENT" in msg
    assert pf.cash == 50.0


def test_sell_unknown_ticker_returns_no_position():
    pf = Portfolio(cash=100.0)
    msg = pf.sell("$X", 1.0, 1.0)
    assert "NO POSITION" in msg


def test_sell_more_shares_than_held_rejected():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 50.0, 1.0)  # 50 shares
    msg = pf.sell("$X", 100.0, 1.0)
    assert "INSUFFICIENT SHARES" in msg


def test_sell_zero_or_negative_shares_rejected():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 50.0, 1.0)
    assert "positive" in pf.sell("$X", 0.0, 1.0).lower()
    assert "positive" in pf.sell("$X", -1.0, 1.0).lower()


def test_full_sell_clears_position():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 100.0, 2.0)  # 50 shares @ 2.0
    pf.sell("$X", 50.0, 4.0)  # sell all @ 4.0 -> 200 cash
    assert pf.cash == 200.0
    assert "$X" not in pf.positions


def test_sell_almost_all_collapses_below_dust_threshold():
    """1e-7 shares left after a sell should trigger the dust deletion."""
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 100.0, 1.0)  # 100 shares
    pf.sell("$X", 100.0 - 1e-7, 1.0)
    assert "$X" not in pf.positions


def test_cost_basis_averages_across_multiple_buys():
    pf = Portfolio(cash=10000.0)
    pf.buy("$X", 1000.0, 1.0)   # 1000 shares @ 1.0
    pf.buy("$X", 1000.0, 4.0)   # 250 shares @ 4.0
    pos = pf.positions["$X"]
    assert math.isclose(pos.shares, 1250.0)
    # total cost = 2000, avg = 2000 / 1250 = 1.60
    assert math.isclose(pos.cost_basis, 1.60, rel_tol=1e-9)


def test_greed_clamps_at_100():
    pf = Portfolio(cash=10_000_000.0)
    # one massive buy would otherwise push greed way past 100
    pf.buy("$X", 9_000_000.0, 1.0)
    assert pf.greed == 100


def test_greed_increments_at_least_one_per_trade():
    pf = Portfolio(cash=10_000.0)
    pf.buy("$X", 50.0, 1.0)  # 50/500 == 0 by int(); should still bump by 1
    assert pf.greed == 1


def test_value_uses_zero_for_missing_price():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 50.0, 1.0)
    # No price for $X in this lookup → contributes 0 to value (only cash counts).
    assert pf.value({}) == 50.0


def test_value_counts_cash_plus_holdings():
    pf = Portfolio(cash=100.0)
    pf.buy("$X", 50.0, 1.0)  # 50 shares
    assert pf.value({"$X": 3.0}) == 50.0 + 50.0 * 3.0


def test_buy_rejects_nan_amount_without_corrupting_state():
    pf = Portfolio(cash=1000.0)
    msg = pf.buy("$X", float("nan"), 1.0)
    assert "finite" in msg.lower()
    assert pf.cash == 1000.0
    assert pf.positions == {}


def test_buy_rejects_inf_amount_without_corrupting_state():
    pf = Portfolio(cash=1000.0)
    # +inf gets caught by INSUFFICIENT FUNDS today, but the finite guard
    # is the more defensible message and runs first.
    msg = pf.buy("$X", float("inf"), 1.0)
    assert "finite" in msg.lower() or "INSUFFICIENT" in msg
    assert pf.cash == 1000.0


def test_sell_rejects_nan_shares_without_corrupting_state():
    pf = Portfolio(cash=1000.0)
    pf.buy("$X", 100.0, 1.0)
    msg = pf.sell("$X", float("nan"), 1.0)
    assert "finite" in msg.lower()
    assert pf.cash == 900.0
    assert pf.positions["$X"].shares == 100.0


def test_buy_then_full_sell_at_same_price_conserves_cash():
    pf = Portfolio(cash=1000.0)
    pf.buy("$X", 700.0, 2.5)
    pf.sell("$X", pf.positions["$X"].shares, 2.5)
    assert math.isclose(pf.cash, 1000.0, rel_tol=1e-12)
    assert pf.positions == {}
