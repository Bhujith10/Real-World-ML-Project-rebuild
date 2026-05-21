# trades service

**What:** Connects to Kraken's public WebSocket API and streams live BTC/USD trades into a Kafka topic.

**Architecture:**
```
Kraken WebSocket (wss://ws.kraken.com/v2)
        │
        ▼
   ┌──────────┐
   │  trades  │  ← this service
   └──────────┘
        │
        ▼
  Kafka topic: "trades"
```

## How to run (local dev)

```bash
cd services/trades

# Install dependencies
uv sync

# Set environment variables (or use defaults for in-cluster)
export KAFKA_BROKER_ADDRESS="localhost:9092"
export KAFKA_TOPIC="trades"
export PAIRS="BTC/USD"

# Run
uv run python -m trades.main
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BROKER_ADDRESS` | `kafka-0.kafka-headless.kafka.svc.cluster.local:9092` | Kafka bootstrap server |
| `KAFKA_TOPIC` | `trades` | Topic to produce to |
| `KRAKEN_WS_URL` | `wss://ws.kraken.com/v2` | Kraken WebSocket endpoint |
| `PAIRS` | `BTC/USD` | Comma-separated trading pairs |

## Message format (JSON in Kafka)

```json
{
  "pair": "BTC/USD",
  "price": 67234.5,
  "volume": 0.0012,
  "timestamp": "2024-01-15T10:30:00.123Z",
  "side": "buy"
}
```
