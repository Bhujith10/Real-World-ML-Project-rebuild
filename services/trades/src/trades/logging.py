"""Structured JSON logging configuration using loguru.

Why structured logging?
- Human-readable logs are fine for local dev
- In production, logs go to aggregation systems (Grafana Loki, ELK, CloudWatch)
- These systems need machine-parseable formats (JSON) to filter/search/alert
- loguru makes it easy to switch between human-friendly (dev) and JSON (prod)

Usage: import this module early in your service's entrypoint.
"""

import sys

from loguru import logger

from trades.config import settings


def setup_logging() -> None:
    """Configure loguru for structured JSON logging.

    In production (LOG_FORMAT=json): outputs machine-parseable JSON lines.
    In development (LOG_FORMAT=text): outputs colorful human-readable logs.
    """
    # Remove default handler
    logger.remove()

    log_format = getattr(settings, "log_format", "text")

    if log_format == "json":
        # JSON format for production — one JSON object per log line
        logger.add(
            sys.stdout,
            serialize=True,  # This is the magic — loguru outputs JSON
            level="INFO",
        )
    else:
        # Human-readable format for local development
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
