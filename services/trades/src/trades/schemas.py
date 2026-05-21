"""Pydantic models for trade data.

These models define the shape of data flowing through our system.
Using Pydantic ensures:
- Type validation (catch bad data early)
- Easy serialization to JSON (for Kafka messages)
- Self-documenting data contracts between services
"""

from datetime import datetime

from pydantic import BaseModel


class Trade(BaseModel):
    """A single trade event from Kraken.

    Attributes:
        pair: Trading pair, e.g. "BTC/USD"
        price: Execution price of the trade
        volume: Amount of the base currency traded
        timestamp: When the trade occurred (Unix timestamp from Kraken)
        side: "buy" or "sell" — who initiated the trade
    """

    pair: str
    price: float
    volume: float
    timestamp: datetime
    side: str
