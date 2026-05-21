"""Kafka producer for sending trade messages.

How Kafka producers work:
- A producer connects to a Kafka broker (bootstrap server)
- It serializes your data (we use JSON) and sends it to a topic
- Each message has a key (optional) and a value (the trade JSON)
- We use the trading pair as the key — this ensures all trades for the same pair
  go to the same partition, preserving ordering per pair.

We use `kafka-python-ng` — a maintained fork of the original kafka-python library.
"""

import json

from kafka import KafkaProducer
from loguru import logger

from trades.config import settings
from trades.schemas import Trade


def create_producer() -> KafkaProducer:
    """Create and return a configured KafkaProducer instance.

    Key configuration:
    - bootstrap_servers: where to find Kafka (our cluster service DNS)
    - value_serializer: converts Python dicts to JSON bytes before sending
    - key_serializer: converts the string key (pair name) to bytes
    - acks='all': wait for all replicas to confirm (most durable, slightly slower)
    """
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_broker_address,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3,
    )
    logger.info(
        f"Kafka producer connected to {settings.kafka_broker_address}"
    )
    return producer


def produce_trade(producer: KafkaProducer, trade: Trade) -> None:
    """Send a single trade to the Kafka topic.

    Args:
        producer: The KafkaProducer instance
        trade: A validated Trade object
    """
    producer.send(
        topic=settings.kafka_topic,
        key=trade.pair,
        value=trade.model_dump(mode="json"),
    )
