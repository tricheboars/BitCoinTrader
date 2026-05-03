"""HTTP + WebSocket integration tests against the FastAPI app."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from bitcointrader.server import config


@pytest.fixture
def client(monkeypatch):
    # Long tick + no news so the engine doesn't push noise during the test.
    monkeypatch.setattr(config, "TICK_MS", 60_000)
    monkeypatch.setattr(config, "NEWS_ENABLED", False)
    monkeypatch.setattr(config, "SEED", 1234)
    monkeypatch.setattr(config, "START_CASH", 10_000.0)
    from bitcointrader.server.app import app
    with TestClient(app) as c:
        yield c


def _drain_until(ws, kind: str, max_msgs: int = 10) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == kind:
            return msg
    raise AssertionError(f"never saw a {kind} message")


def _drain_state_after_cmd(ws, cmd: str) -> tuple[str, dict]:
    """Send a cmd, then return (stdout text, state msg)."""
    ws.send_json({"type": "cmd", "cmd": cmd})
    out = _drain_until(ws, "out")
    state = _drain_until(ws, "state")
    return out["text"], state


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower() or "<!doctype" in r.text.lower()


def test_ws_initial_messages(client):
    with client.websocket_connect("/ws") as ws:
        banner = ws.receive_json()
        snapshot = ws.receive_json()
        state = ws.receive_json()
    assert banner["type"] == "out"
    assert "GREED IS GOOD" in banner["text"]

    assert snapshot["type"] == "snapshot"
    assert "$BTCN" in snapshot["prices"]
    assert "$BTCN" in snapshot["assets"]
    assert snapshot["assets"]["$BTCN"]["name"] == "BitCorn"

    assert state["type"] == "state"
    assert state["cash"] == 10_000.0
    assert state["positions"] == {}


def test_ws_help_command(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")  # banner
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, state = _drain_state_after_cmd(ws, "help")
    assert "COMMANDS" in text
    assert state["cash"] == 10_000.0


def test_ws_market_command_lists_all_tickers(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "market")
    for t in ["$BTCN", "$MUSK", "$RUGZ", "$TULP"]:
        assert t in text


def test_ws_unknown_command(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "yeet")
    assert "unknown command" in text


def test_ws_buy_then_sell_all(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        snapshot = _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        btcn_price = snapshot["prices"]["$BTCN"]

        text, state = _drain_state_after_cmd(ws, "buy $BTCN 1000")
        assert "BUY" in text
        assert state["cash"] == pytest.approx(9_000.0)
        assert "$BTCN" in state["positions"]
        expected_shares = 1000.0 / btcn_price
        assert state["positions"]["$BTCN"]["shares"] == pytest.approx(expected_shares)

        text, state = _drain_state_after_cmd(ws, "sell $BTCN all")
        assert "SELL" in text
        # Sold at the same price (no tick fired, news disabled) — cash restored.
        assert state["cash"] == pytest.approx(10_000.0)
        assert state["positions"] == {}


def test_ws_buy_lowercase_no_dollar_normalizes(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, state = _drain_state_after_cmd(ws, "buy btcn 500")
    assert "BUY" in text
    assert "$BTCN" in state["positions"]


def test_ws_buy_with_comma_amount(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, state = _drain_state_after_cmd(ws, "buy $BTCN 1,500")
    assert "BUY" in text
    assert state["cash"] == pytest.approx(8_500.0)


def test_ws_buy_with_dollar_prefix_amount(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, state = _drain_state_after_cmd(ws, "buy $BTCN $750")
    assert "BUY" in text
    assert state["cash"] == pytest.approx(9_250.0)


def test_ws_buy_unknown_ticker(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "buy $NOPE 100")
    assert "unknown ticker" in text


def test_ws_buy_bad_amount(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "buy $BTCN abc")
    assert "bad amount" in text


def test_ws_sell_with_no_position(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "sell $BTCN all")
    assert "NO POSITION" in text


def test_ws_clear_command(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        ws.send_json({"type": "cmd", "cmd": "clear"})
        msg = ws.receive_json()
        assert msg["type"] == "clear"
        # state still follows the clear
        state = _drain_until(ws, "state")
        assert state["cash"] == 10_000.0


def test_ws_malformed_json_is_ignored(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        ws.send_text("not json {{{")
        # Connection must still be alive — issue a real command after.
        text, _ = _drain_state_after_cmd(ws, "help")
        assert "COMMANDS" in text


def test_ws_non_cmd_payload_ignored(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        ws.send_json({"type": "ping"})
        text, _ = _drain_state_after_cmd(ws, "help")
        assert "COMMANDS" in text


def test_ws_portfolio_empty_then_populated(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "portfolio")
        assert "no open positions" in text
        _drain_state_after_cmd(ws, "buy $BTCN 250")
        text, _ = _drain_state_after_cmd(ws, "portfolio")
        assert "$BTCN" in text
        assert "TICKER" in text


def test_ws_news_command_help_text(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, _ = _drain_state_after_cmd(ws, "news")
    assert "watch the wire" in text


def test_ws_buy_nan_does_not_kill_session(client):
    """Regression: 'buy btcn nan' used to crash the session and corrupt cash."""
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        text, state = _drain_state_after_cmd(ws, "buy btcn nan")
        assert "finite" in text.lower()
        assert state["cash"] == 10_000.0
        assert state["positions"] == {}
        # Connection still alive — issue another command.
        text, _ = _drain_state_after_cmd(ws, "help")
        assert "COMMANDS" in text


def test_ws_sell_nan_does_not_kill_session(client):
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        _drain_state_after_cmd(ws, "buy btcn 500")
        text, state = _drain_state_after_cmd(ws, "sell btcn nan")
        assert "finite" in text.lower()
        # Position untouched.
        assert state["positions"]["$BTCN"]["shares"] > 0
        text, _ = _drain_state_after_cmd(ws, "help")
        assert "COMMANDS" in text


def test_ws_disconnect_cleans_up_subscriber(client):
    """After a client disconnects, the engine should drop its queue."""
    from bitcointrader.server.app import app
    market = app.state.market
    before = len(market._subscribers)
    with client.websocket_connect("/ws") as ws:
        _drain_until(ws, "out")
        _drain_until(ws, "snapshot")
        _drain_until(ws, "state")
        assert len(market._subscribers) == before + 1
    # Give the server a beat to process the disconnect.
    import time
    for _ in range(20):
        if len(market._subscribers) == before:
            break
        time.sleep(0.05)
    assert len(market._subscribers) == before
