"""Per-WebSocket trader session."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from bitcointrader.engine.tick import MarketEngine
from bitcointrader.server import config
from bitcointrader.server.text import BANNER, HELP, MARGIN_CALL_TEXT, MASTER_TEXT
from bitcointrader.trader.portfolio import Portfolio

log = logging.getLogger(__name__)

WIN_TARGET = 1_000_000.0


class TraderSession:
    def __init__(self, market: MarketEngine, ws: WebSocket):
        self.market = market
        self.ws = ws
        self.portfolio = Portfolio(cash=config.START_CASH)
        self.queue: asyncio.Queue | None = None
        self.ended = False

    async def run(self) -> None:
        self.queue = self.market.subscribe()
        try:
            await self._send({"type": "out", "text": BANNER})
            await self._send_initial_market()
            await self._send_state()

            send_task = asyncio.create_task(self._send_loop())
            recv_task = asyncio.create_task(self._recv_loop())
            done, pending = await asyncio.wait(
                {send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
            for t in done:
                exc = t.exception()
                if exc and not isinstance(exc, WebSocketDisconnect):
                    log.exception("session task failed", exc_info=exc)
        finally:
            if self.queue is not None:
                self.market.unsubscribe(self.queue)

    async def _send(self, msg: dict) -> None:
        try:
            await self.ws.send_text(json.dumps(msg))
        except (WebSocketDisconnect, RuntimeError):
            self.ended = True

    async def _send_initial_market(self) -> None:
        await self._send({
            "type": "snapshot",
            "prices": dict(self.market.prices),
            "assets": {
                t: {"name": a.name, "flavor": a.flavor, "description": a.description}
                for t, a in self.market.assets.items()
            },
        })

    async def _send_loop(self) -> None:
        assert self.queue is not None
        while not self.ended:
            msg = await self.queue.get()
            await self._send(msg)
            if msg["type"] in ("tick", "news"):
                await self._send_state()
                await self._check_endings()

    async def _recv_loop(self) -> None:
        while not self.ended:
            try:
                text = await self.ws.receive_text()
            except WebSocketDisconnect:
                self.ended = True
                return
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if data.get("type") == "cmd":
                await self._handle_cmd(str(data.get("cmd", "")))

    async def _handle_cmd(self, cmd: str) -> None:
        parts = cmd.strip().split()
        if not parts:
            return
        op = parts[0].lower()

        if op == "help":
            await self._out(HELP)
        elif op == "market":
            await self._out(self._format_market())
        elif op == "portfolio":
            await self._out(self._format_portfolio())
        elif op == "news":
            await self._out("the news fires automatically every 30–90s. watch the wire.")
        elif op == "clear":
            await self._send({"type": "clear"})
        elif op == "buy" and len(parts) == 3:
            await self._out(self._do_buy(parts[1], parts[2]))
        elif op == "sell" and len(parts) == 3:
            await self._out(self._do_sell(parts[1], parts[2]))
        else:
            await self._out(f"unknown command: '{cmd}'. type 'help'.")

        await self._send_state()
        await self._check_endings()

    async def _out(self, text: str) -> None:
        await self._send({"type": "out", "text": text})

    def _normalize_ticker(self, raw: str) -> str:
        t = raw.upper()
        if not t.startswith("$"):
            t = "$" + t
        return t

    def _do_buy(self, raw_ticker: str, amount_str: str) -> str:
        ticker = self._normalize_ticker(raw_ticker)
        if ticker not in self.market.prices:
            return f"unknown ticker: {ticker}"
        try:
            amount = float(amount_str.lstrip("$").replace(",", ""))
        except ValueError:
            return f"bad amount: {amount_str}"
        return self.portfolio.buy(ticker, amount, self.market.prices[ticker])

    def _do_sell(self, raw_ticker: str, amount_str: str) -> str:
        ticker = self._normalize_ticker(raw_ticker)
        if ticker not in self.market.prices:
            return f"unknown ticker: {ticker}"
        if amount_str.lower() == "all":
            pos = self.portfolio.positions.get(ticker)
            if pos is None:
                return f"NO POSITION IN {ticker}."
            shares = pos.shares
        else:
            try:
                shares = float(amount_str.replace(",", ""))
            except ValueError:
                return f"bad amount: {amount_str}"
        return self.portfolio.sell(ticker, shares, self.market.prices[ticker])

    def _format_market(self) -> str:
        lines = [
            "TICKER    NAME                          PRICE       FLAVOR",
            "─" * 64,
        ]
        for t, asset in self.market.assets.items():
            p = self.market.prices[t]
            lines.append(f"{t:<9} {asset.name:<28}  ${p:>10,.4f}   {asset.flavor}")
        return "\n".join(lines)

    def _format_portfolio(self) -> str:
        prices = self.market.prices
        lines = [
            f"CASH:  ${self.portfolio.cash:,.2f}",
            "─" * 70,
        ]
        if not self.portfolio.positions:
            lines.append("(no open positions — hit 'market' and BUY something)")
        else:
            lines.append(
                f"{'TICKER':<9}{'SHARES':>14}  {'COST':>10}  {'PRICE':>10}  {'VALUE':>12}  {'P/L':>12}"
            )
            for t, pos in self.portfolio.positions.items():
                cur = prices.get(t, 0.0)
                value = pos.shares * cur
                cost = pos.shares * pos.cost_basis
                pnl = value - cost
                lines.append(
                    f"{t:<9}{pos.shares:>14,.4f}  ${pos.cost_basis:>9,.4f}  "
                    f"${cur:>9,.4f}  ${value:>11,.2f}  ${pnl:>+11,.2f}"
                )
        total = self.portfolio.value(prices)
        lines.append("─" * 70)
        lines.append(f"NET WORTH: ${total:,.2f}        GREED: {self.portfolio.greed}/100")
        return "\n".join(lines)

    async def _send_state(self) -> None:
        prices = self.market.prices
        await self._send({
            "type": "state",
            "cash": self.portfolio.cash,
            "value": self.portfolio.value(prices),
            "greed": self.portfolio.greed,
            "positions": {
                t: {"shares": p.shares, "cost_basis": p.cost_basis}
                for t, p in self.portfolio.positions.items()
            },
        })

    async def _check_endings(self) -> None:
        if self.ended:
            return
        prices = self.market.prices
        total = self.portfolio.value(prices)
        if total >= WIN_TARGET:
            await self._send({"type": "ending", "kind": "master", "message": MASTER_TEXT})
            self.ended = True
        elif self.portfolio.cash <= 0 and not self.portfolio.positions:
            await self._send({"type": "ending", "kind": "margin_call", "message": MARGIN_CALL_TEXT})
            self.ended = True
