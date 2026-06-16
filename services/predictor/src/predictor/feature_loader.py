"""Load features from RisingWave and manage local Parquet archive.

Workflow:
1. Pull latest data from RisingWave → save to data/raw/ as timestamped Parquet
2. Read all raw Parquet files → concat → deduplicate → sort by timestamp
3. Return the clean canonical DataFrame for training

The raw/ folder is an append-only archive. Each training run adds a new file.
Deduplication handles overlapping exports.
"""

from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import psycopg2
from loguru import logger

from predictor.config import settings


def _ensure_dirs() -> tuple[Path, Path]:
    """Create the data directory structure if it doesn't exist.

    Returns:
        (data_dir, raw_dir) as Path objects.
    """
    data_dir = Path(settings.data_dir)
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return data_dir, raw_dir


def pull_from_risingwave() -> pl.DataFrame:
    """Query all rows from mv_features in RisingWave.

    Returns a Polars DataFrame sorted by window_start_ms.
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

    logger.info("Querying RisingWave for all features...")

    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pl.DataFrame(rows, schema=columns, orient="row")
    logger.info(f"Pulled {len(df)} rows from RisingWave")
    return df


def export_raw_parquet(df: pl.DataFrame) -> Path:
    """Save a DataFrame as a timestamped Parquet file in data/raw/.

    Returns the path to the created file.
    """
    _, raw_dir = _ensure_dirs()
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d_%H%M%S")
    path = raw_dir / f"features_{timestamp}.parquet"
    df.write_parquet(path)
    logger.info(f"Exported {len(df)} rows → {path}")
    return path


def build_canonical_dataset() -> pl.DataFrame:
    """Read all raw Parquet files, concat, deduplicate, and sort.

    Deduplication key: (pair, window_start_ms).
    Sort: by window_start_ms ascending.

    Returns the clean, deduplicated DataFrame.
    """
    _, raw_dir = _ensure_dirs()
    parquet_files = sorted(raw_dir.glob("*.parquet"))

    if not parquet_files:
        logger.error(f"No Parquet files found in {raw_dir}")
        return pl.DataFrame()

    logger.info(f"Found {len(parquet_files)} raw Parquet file(s)")
    for f in parquet_files:
        logger.info(f"  - {f.name}")

    # Read and concatenate all files
    dfs = [pl.read_parquet(f) for f in parquet_files]
    df = pl.concat(dfs)
    logger.info(f"Concatenated: {len(df)} total rows")

    # Deduplicate by (pair, window_start_ms) — keep first occurrence
    before = len(df)
    df = df.unique(subset=["pair", "window_start_ms"], keep="first")
    dupes = before - len(df)
    if dupes > 0:
        logger.info(f"Removed {dupes} duplicate rows")

    # Sort by timestamp
    df = df.sort("window_start_ms")
    logger.info(f"Canonical dataset: {len(df)} rows")

    return df


def detect_gaps(df: pl.DataFrame) -> pl.DataFrame:
    """Add a 'gap_group' column that increments at each gap boundary.

    A gap is defined as consecutive rows where the timestamp difference
    exceeds gap_threshold_minutes. Rows in the same contiguous block
    share the same gap_group value.

    This is used during target engineering to avoid creating targets
    that cross time gaps.
    """
    threshold_ms = settings.gap_threshold_minutes * 60 * 1000

    df = df.with_columns(
        (pl.col("window_start_ms").diff().fill_null(0) > threshold_ms).cum_sum().alias("gap_group"),
    )

    n_groups = df["gap_group"].n_unique()
    if n_groups > 1:
        logger.warning(
            f"Detected {n_groups} contiguous blocks (gaps in data). "
            "Targets will not be engineered across gap boundaries."
        )
        # Log each group's time range
        for group_id in sorted(df["gap_group"].unique().to_list()):
            block = df.filter(pl.col("gap_group") == group_id)
            start = datetime.fromtimestamp(block["window_start_ms"].min() / 1000, tz=UTC)
            end = datetime.fromtimestamp(block["window_start_ms"].max() / 1000, tz=UTC)
            logger.info(f"  Block {group_id}: {start} → {end} ({len(block)} rows)")
    else:
        logger.info("No gaps detected — data is contiguous")

    return df
