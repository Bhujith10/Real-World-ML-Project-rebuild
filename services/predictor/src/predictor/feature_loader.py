"""Load features from RisingWave for model training.

Two modes:
1. Query RisingWave's mv_features materialized view (live data)
2. Read from a Parquet file (offline / backup data)

The training script uses this module to get a DataFrame of features + targets.
"""

import polars as pl
import psycopg2
from loguru import logger

from predictor.config import settings


def load_from_risingwave(limit: int | None = None) -> pl.DataFrame:
    """Query mv_features from RisingWave and return a Polars DataFrame.

    Args:
        limit: Optional row limit. None = all available rows.

    Returns:
        Polars DataFrame with columns:
        pair, window_start_ms, window_end_ms, current_close,
        ema_14, rsi_14, macd_line, macd_signal, macd_histogram
    """
    conn = psycopg2.connect(
        host=settings.risingwave_host,
        port=settings.risingwave_port,
        dbname=settings.risingwave_db,
        user=settings.risingwave_user,
    )

    query = """
        SELECT pair, window_start_ms, window_end_ms, current_close,
               ema_14, rsi_14, macd_line, macd_signal, macd_histogram
        FROM mv_features
        ORDER BY window_start_ms ASC
    """
    if limit:
        query += f" LIMIT {limit}"

    logger.info(f"Querying RisingWave for training features (limit={limit})...")

    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pl.DataFrame(rows, schema=columns, orient="row")
    logger.info(f"Loaded {len(df)} rows from RisingWave")
    return df


def load_from_parquet(path: str) -> pl.DataFrame:
    """Load features from a Parquet file.

    Use this when RisingWave is unavailable or for reproducible training
    with a fixed dataset.
    """
    logger.info(f"Loading features from {path}...")
    df = pl.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows from Parquet")
    return df


def export_to_parquet(df: pl.DataFrame, path: str) -> None:
    """Save a DataFrame to Parquet for backup / reproducible training."""
    df.write_parquet(path)
    logger.info(f"Exported {len(df)} rows to {path}")
