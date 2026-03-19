"""Configuration values and shared schema for the CAGR finance pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

NASDAQ_SERIES_ID = "NASDAQCOM"
SP500_SERIES_ID = "SP500"
CPI_SERIES_ID = "CPIAUCSL"

DATE_COL = "date"
NASDAQ_NOMINAL_COL = "NASDAQ nominal value"
SP500_NOMINAL_COL = "S&P nominal value"
CPI_INDEX_COL = "CPI index"
INFLATION_FACTOR_COL = "inflation factor"
NASDAQ_REAL_COL = "NASDAQ value in real terms"
SP500_REAL_COL = "S&P value in real terms"
TQQQ_NOMINAL_COL = "TQQQ in nominal terms"
UPRO_NOMINAL_COL = "UPRO in nominal terms"
TQQQ_REAL_COL = "TQQQ in real terms"
UPRO_REAL_COL = "UPRO in real terms"

OUTPUT_COLUMNS = [
    DATE_COL,
    NASDAQ_NOMINAL_COL,
    SP500_NOMINAL_COL,
    INFLATION_FACTOR_COL,
    NASDAQ_REAL_COL,
    SP500_REAL_COL,
    TQQQ_NOMINAL_COL,
    UPRO_NOMINAL_COL,
    TQQQ_REAL_COL,
    UPRO_REAL_COL,
]


@dataclass(frozen=True)
class AppSettings:
    """Runtime settings for pulling, transforming, and writing market estimates."""

    leveraged_start_value: float = 100.0
    trading_days_per_year: int = 252

    tqqq_leverage: float = 3.0
    upro_leverage: float = 3.0

    # Annual MER (expense ratio) used as a daily drag in synthetic return calculations.
    tqqq_mer_annual: float = 0.0084
    upro_mer_annual: float = 0.0091

    output_csv_path: Path = Path("data/security_estimates.csv")
