# candles service

**What:** Consumes raw trades from Kafka and aggregates them into 1-minute OHLCV candles using a tumbling window.

**Architecture:**
```
Kafka topic: "trades"
        |
        v
   +----------+
   | candles  |  <- this service
   +----------+
        |
        v
  Kafka topic: "candles"
```

## How to run (local dev)

```bash
cd services/candles

# Install dependencies
uv sync

# Set environment variables (or use defaults for in-cluster)
export KAFKA_BROKER_ADDRESS="localhost:9092"
export KAFKA_INPUT_TOPIC="trades"
export KAFKA_OUTPUT_TOPIC="candles"

# Run
uv run python -m candles
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BROKER_ADDRESS` | `kafka-0.kafka-headless.kafka.svc.cluster.local:9092` | Kafka bootstrap server |
| `KAFKA_INPUT_TOPIC` | `trades` | Topic to consume from |
| `KAFKA_OUTPUT_TOPIC` | `candles` | Topic to produce to |
| `KAFKA_CONSUMER_GROUP` | `candles-service` | Consumer group ID |

## Message format (output JSON in Kafka)

```json
{
  "pair": "BTC/USD",
  "open": 67234.5,
  "high": 67250.0,
  "low": 67200.1,
  "close": 67245.3,
  "volume": 1.234,
  "window_start_ms": 1700000000000,
  "window_end_ms": 1700000060000
}
```

## How it works

Uses Quixstreams `tumbling_window(duration_ms=60000)` to aggregate trades into 1-minute candles. Each candle contains the open, high, low, close prices and total volume for that minute.
