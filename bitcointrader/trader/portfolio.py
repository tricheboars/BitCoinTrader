"""Portfolio — cash, positions, cost basis, greed meter."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Position:
    ticker: str
    shares: float
    cost_basis: float


@dataclass
class Portfolio:
    cash: float = 10000.0
    positions: dict[str, Position] = field(default_factory=dict)
    greed: int = 0

    def buy(self, ticker: str, dollars: float, price: float) -> str:
        if dollars <= 0:
            return "amount must be positive."
        if dollars > self.cash:
            return f"INSUFFICIENT FUNDS. cash: ${self.cash:,.2f}"
        shares = dollars / price
        self.cash -= dollars
        if ticker in self.positions:
            old = self.positions[ticker]
            total_cost = old.cost_basis * old.shares + dollars
            total_shares = old.shares + shares
            old.shares = total_shares
            old.cost_basis = total_cost / total_shares
        else:
            self.positions[ticker] = Position(ticker, shares, price)
        self.greed = min(100, self.greed + max(1, int(dollars / 500)))
        return f"BUY  {shares:>12,.4f} × {ticker} @ ${price:,.4f} = ${dollars:,.2f}"

    def sell(self, ticker: str, shares: float, price: float) -> str:
        if ticker not in self.positions:
            return f"NO POSITION IN {ticker}."
        pos = self.positions[ticker]
        if shares <= 0:
            return "amount must be positive."
        if shares > pos.shares + 1e-9:
            return f"INSUFFICIENT SHARES. holding {pos.shares:,.4f}."
        proceeds = shares * price
        self.cash += proceeds
        pos.shares -= shares
        if pos.shares < 1e-6:
            del self.positions[ticker]
        self.greed = min(100, self.greed + max(1, int(proceeds / 500)))
        return f"SELL {shares:>12,.4f} × {ticker} @ ${price:,.4f} = ${proceeds:,.2f}"

    def value(self, prices: dict[str, float]) -> float:
        v = self.cash
        for t, p in self.positions.items():
            v += p.shares * prices.get(t, 0.0)
        return v
