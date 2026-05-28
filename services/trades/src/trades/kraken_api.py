"""Kraken WebSocket v2 client for streaming live trades.

How the Kraken WebSocket API works:
1. You open a WebSocket connection to wss://ws.kraken.com/v2
2. You send a JSON "subscribe" message specifying what data you want (trades for BTC/USD)
3. Kraken starts pushing trade events to you in real-time
4. Each message contains one or more trades with price, volume, side, timestamp

We use Python's `websockets` library for async WebSocket communication.
The function is an async generator — it yields Trade objects one at a time.
"""

import json
from collections.abc import AsyncGenerator
from datetime import datetime

import websockets

from trades.config import settings
from trades.schemas import Trade


async def stream_trades() -> AsyncGenerator[Trade, None]:
    """Connect to Kraken WebSocket v2 and yield Trade objects as they arrive.

    This is an async generator:
    - It maintains a persistent WebSocket connection
    - Each time Kraken sends a trade message, we parse it and yield Trade objects
    - If the connection drops, it raises an exception (caller should reconnect)
    """
    pairs = [p.strip() for p in settings.pairs.split(",")]

    async for ws in websockets.connect(settings.kraken_ws_url, ping_interval=30):
        try:
            # Subscribe to the "trade" channel for our pairs
            subscribe_msg = {
                "method": "subscribe",
                "params": {
                    "channel": "trade",
                    "symbol": pairs,
                },
            }
            await ws.send(json.dumps(subscribe_msg))

            # Process incoming messages
            async for raw_msg in ws:
                msg = json.loads(raw_msg)

                # Skip non-trade messages (heartbeats, subscription confirmations, etc.)
                if msg.get("channel") != "trade" or msg.get("type") == "snapshot":
                    continue

                # Each message can contain multiple trades in the "data" array
                for trade_data in msg.get("data", []):
                    yield Trade(
                        pair=trade_data["symbol"],
                        price=float(trade_data["price"]),
                        volume=float(trade_data["qty"]),
                        timestamp=datetime.fromisoformat(trade_data["timestamp"]),
                        side=trade_data["side"],
                    )

        except websockets.ConnectionClosed:
            # websockets.connect with `async for` will auto-reconnect
            continue
