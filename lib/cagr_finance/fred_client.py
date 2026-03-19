"""Utilities for downloading market and inflation data from FRED."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from pandas_datareader import data as pdr
import requests

from .config import (
    CPI_INDEX_COL,
    CPI_SERIES_ID,
    DATE_COL,
    NASDAQ_NOMINAL_COL,
    NASDAQ_SERIES_ID,
    SP500_NOMINAL_COL,
    SP500_SERIES_ID,
)


@dataclass(frozen=True)
class RawSeriesBundle:
    """Container for the raw time series used by the application."""

    nasdaq: pd.DataFrame
    sp500: pd.DataFrame
    cpi: pd.DataFrame


def fetch_fred_series(
    series_id: str,
    output_column: str,
    *,
    start_date: str = "1900-01-01",
    end_date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch a FRED series with pandas-datareader and normalize schema."""

    frame = pdr.DataReader(
        series_id,
        "fred",
        start=start_date,
        end=end_date,
        session=session,
    ).reset_index()

    if series_id not in frame.columns:
        raise ValueError(f"FRED response for {series_id} missing column: {series_id}")

    frame = frame.rename(columns={frame.columns[0]: DATE_COL, series_id: output_column})
    frame[DATE_COL] = pd.to_datetime(frame[DATE_COL], errors="coerce")
    frame[output_column] = pd.to_numeric(frame[output_column], errors="coerce")

    frame = (
        frame.dropna(subset=[DATE_COL, output_column])
        .sort_values(DATE_COL)
        .drop_duplicates(subset=[DATE_COL], keep="last")
        .reset_index(drop=True)
    )
    return frame


def fetch_default_series(*, session: Optional[requests.Session] = None) -> RawSeriesBundle:
    """Fetch NASDAQ, S&P 500, and CPI using default FRED series identifiers."""

    return RawSeriesBundle(
        nasdaq=fetch_fred_series(NASDAQ_SERIES_ID, NASDAQ_NOMINAL_COL, session=session),
        sp500=fetch_fred_series(SP500_SERIES_ID, SP500_NOMINAL_COL, session=session),
        cpi=fetch_fred_series(CPI_SERIES_ID, CPI_INDEX_COL, session=session),
    )
