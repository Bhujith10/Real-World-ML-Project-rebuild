"""Structured JSON logging configuration using loguru.

Same pattern as trades and candles services.
"""

import sys

from loguru import logger

from predictor.config import settings


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
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level="DEBUG",
            colorize=True,
        )
