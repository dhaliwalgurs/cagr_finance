"""Configuration values and shared schema for the CAGR finance pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

NASDAQ_SERIES_ID = "NASDAQCOM"
SP500_SERIES_ID = "SP500"
CPI_SERIES_ID = "CPIAUCSL"

# Historical floor dates we intentionally enforce for modeled output.
NASDAQ_MIN_DATE = "1971-02-05"
SP500_MIN_DATE = "1957-03-04"

DATE_COL = "date"
NASDAQ_NOMINAL_COL = "NASDAQ nominal value"
SP500_NOMINAL_COL = "S&P nominal value"
CPI_INDEX_COL = "CPI index"
INFLATION_FACTOR_COL = "inflation factor"
NASDAQ_REAL_COL = "NASDAQ value in real terms"
SP500_REAL_COL = "S&P value in real terms"
TQQQ_NOMINAL_COL = "TQQQ in nominal terms"
UPRO_NOMINAL_COL = "UPRO in nominal terms"
QLD_NOMINAL_COL = "QLD in nominal terms"
TQQQ_REAL_COL = "TQQQ in real terms"
UPRO_REAL_COL = "UPRO in real terms"
QLD_REAL_COL = "QLD in real terms"

TRADING_DAYS_PER_YEAR = 252
DEFAULT_STARTING_NOMINAL_VALUE = 100.0

TQQQ_LEVERAGE = 3.0
UPRO_LEVERAGE = 3.0
QLD_LEVERAGE = 2.0

# Annual MER (expense ratio) used as a daily drag in synthetic return calculations.
TQQQ_MER_ANNUAL = 0.0084
UPRO_MER_ANNUAL = 0.0091
QLD_MER_ANNUAL = 0.0095

SUPPORTED_SECURITIES = ("TQQQ", "UPRO", "QLD", "NASDAQ", "SP500")
DEFAULT_SECURITY_ORDER = ("TQQQ", "UPRO", "QLD", "NASDAQ", "SP500")
SECURITY_ALIASES: Mapping[str, str] = {
    "TQQQ": "TQQQ",
    "UPRO": "UPRO",
    "QLD": "QLD",
    "NASDAQ": "NASDAQ",
    "SP500": "SP500",
    "S&P": "SP500",
    "S&P500": "SP500",
    "ALL": "ALL",
}

SECURITY_COLUMN_MAP: Mapping[str, tuple[str, str]] = {
    "TQQQ": (TQQQ_NOMINAL_COL, TQQQ_REAL_COL),
    "UPRO": (UPRO_NOMINAL_COL, UPRO_REAL_COL),
    "QLD": (QLD_NOMINAL_COL, QLD_REAL_COL),
    "NASDAQ": (NASDAQ_NOMINAL_COL, NASDAQ_REAL_COL),
    "SP500": (SP500_NOMINAL_COL, SP500_REAL_COL),
}


@dataclass(frozen=True)
class LeveragedSecuritySpec:
    """Configuration for building a synthetic leveraged security path."""

    symbol: str
    underlying_column: str
    output_nominal_column: str
    output_real_column: str
    leverage: float
    annual_mer: float


LEVERAGED_SECURITY_SPECS: tuple[LeveragedSecuritySpec, ...] = (
    LeveragedSecuritySpec(
        symbol="TQQQ",
        underlying_column=NASDAQ_NOMINAL_COL,
        output_nominal_column=TQQQ_NOMINAL_COL,
        output_real_column=TQQQ_REAL_COL,
        leverage=TQQQ_LEVERAGE,
        annual_mer=TQQQ_MER_ANNUAL,
    ),
    LeveragedSecuritySpec(
        symbol="UPRO",
        underlying_column=SP500_NOMINAL_COL,
        output_nominal_column=UPRO_NOMINAL_COL,
        output_real_column=UPRO_REAL_COL,
        leverage=UPRO_LEVERAGE,
        annual_mer=UPRO_MER_ANNUAL,
    ),
    LeveragedSecuritySpec(
        symbol="QLD",
        underlying_column=NASDAQ_NOMINAL_COL,
        output_nominal_column=QLD_NOMINAL_COL,
        output_real_column=QLD_REAL_COL,
        leverage=QLD_LEVERAGE,
        annual_mer=QLD_MER_ANNUAL,
    ),
)

OUTPUT_COLUMNS = [
    DATE_COL,
    NASDAQ_NOMINAL_COL,
    SP500_NOMINAL_COL,
    INFLATION_FACTOR_COL,
    NASDAQ_REAL_COL,
    SP500_REAL_COL,
    TQQQ_NOMINAL_COL,
    UPRO_NOMINAL_COL,
    QLD_NOMINAL_COL,
    TQQQ_REAL_COL,
    UPRO_REAL_COL,
    QLD_REAL_COL,
]


@dataclass(frozen=True)
class AppSettings:
    """Runtime settings for pulling, transforming, and writing market estimates."""

    leveraged_start_value: float = DEFAULT_STARTING_NOMINAL_VALUE

    output_csv_path: Path = Path("data/security_estimates.csv")
