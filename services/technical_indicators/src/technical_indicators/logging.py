"""Structured logging setup for the technical_indicators service.

Same pattern as trades/candles services — will be moved to a shared package later.
"""

import sys

from loguru import logger

from technical_indicators.config import settings


def setup_logging() -> None:
    """Configure loguru based on LOG_FORMAT env var.

    - "json" → machine-parseable JSON (production, Grafana Loki, etc.)
    - "text" → human-readable colorful output (local dev)
    """
    logger.remove()

    if settings.log_format == "json":
        logger.add(sys.stdout, serialize=True, level="INFO")
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level="INFO",
            colorize=True,
        )
