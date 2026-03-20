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
    NASDAQ_MIN_DATE,
    NASDAQ_100_MIN_DATE,
    NASDAQ_100_NOMINAL_COL,
    NASDAQ_100_SERIES_ID,
    NASDAQ_NOMINAL_COL,
    NASDAQ_SERIES_ID,
    QLD_NOMINAL_COL,
    QLD_STOOQ_SYMBOL,
    SP500_MIN_DATE,
    SP500_NOMINAL_COL,
    SP500_SERIES_ID,
    TQQQ_NOMINAL_COL,
    TQQQ_STOOQ_SYMBOL,
    UPRO_NOMINAL_COL,
    UPRO_STOOQ_SYMBOL,
)


@dataclass(frozen=True)
class RawSeriesBundle:
    """Container for the raw time series used by the application."""

    nasdaq: pd.DataFrame
    nasdaq100: pd.DataFrame
    sp500: pd.DataFrame
    cpi: pd.DataFrame
    tqqq: pd.DataFrame
    upro: pd.DataFrame
    qld: pd.DataFrame


def _max_start_date(requested_start: str, enforced_floor: str) -> str:
    """Return the later of a requested date and an enforced minimum date."""

    requested = pd.Timestamp(requested_start).normalize()
    floor = pd.Timestamp(enforced_floor).normalize()
    return str(max(requested, floor).date())


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


def fetch_stooq_close_series(
    symbol: str,
    output_column: str,
    *,
    start_date: str,
    end_date: Optional[str] = None,
    allow_missing_close: bool = False,
) -> pd.DataFrame:
    """Fetch close prices from Stooq and normalize schema."""

    frame = pdr.DataReader(symbol, "stooq", start=start_date, end=end_date).reset_index()
    if "Close" not in frame.columns:
        if allow_missing_close:
            return pd.DataFrame(columns=[DATE_COL, output_column])
        raise ValueError(f"Stooq response for {symbol} missing column: Close")

    frame = frame.rename(columns={frame.columns[0]: DATE_COL, "Close": output_column})
    frame[DATE_COL] = pd.to_datetime(frame[DATE_COL], errors="coerce")
    frame[output_column] = pd.to_numeric(frame[output_column], errors="coerce")

    frame = (
        frame.dropna(subset=[DATE_COL, output_column])
        .sort_values(DATE_COL)
        .drop_duplicates(subset=[DATE_COL], keep="last")
        .reset_index(drop=True)
    )
    return frame


def fetch_sp500_nominal_series(
    *,
    start_date: str,
    end_date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """
    Fetch S&P nominal series with a historical fallback.

    FRED currently exposes only ~10 years of daily SP500 history due licensing.
    For older ranges we fall back to Stooq's daily S&P 500 close series.
    """

    fred_frame = fetch_fred_series(
        SP500_SERIES_ID,
        SP500_NOMINAL_COL,
        start_date=start_date,
        end_date=end_date,
        session=session,
    )
    if fred_frame.empty:
        return fetch_stooq_close_series("^SPX", SP500_NOMINAL_COL, start_date=start_date, end_date=end_date)

    earliest_fred_date = fred_frame[DATE_COL].min()
    if earliest_fred_date > pd.Timestamp(start_date):
        return fetch_stooq_close_series("^SPX", SP500_NOMINAL_COL, start_date=start_date, end_date=end_date)

    return fred_frame


def fetch_default_series(
    *,
    start_date: str = "1900-01-01",
    end_date: Optional[str] = None,
    cpi_start_date: str = "1900-01-01",
    cpi_end_date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> RawSeriesBundle:
    """Fetch core index, CPI, and actual ETF series using default identifiers."""

    nasdaq_start = _max_start_date(start_date, NASDAQ_MIN_DATE)
    nasdaq100_start = _max_start_date(start_date, NASDAQ_100_MIN_DATE)
    sp500_start = _max_start_date(start_date, SP500_MIN_DATE)

    return RawSeriesBundle(
        nasdaq=fetch_fred_series(
            NASDAQ_SERIES_ID,
            NASDAQ_NOMINAL_COL,
            start_date=nasdaq_start,
            end_date=end_date,
            session=session,
        ),
        nasdaq100=fetch_fred_series(
            NASDAQ_100_SERIES_ID,
            NASDAQ_100_NOMINAL_COL,
            start_date=nasdaq100_start,
            end_date=end_date,
            session=session,
        ),
        sp500=fetch_sp500_nominal_series(
            start_date=sp500_start,
            end_date=end_date,
            session=session,
        ),
        cpi=fetch_fred_series(
            CPI_SERIES_ID,
            CPI_INDEX_COL,
            start_date=cpi_start_date,
            end_date=cpi_end_date,
            session=session,
        ),
        tqqq=fetch_stooq_close_series(
            TQQQ_STOOQ_SYMBOL,
            TQQQ_NOMINAL_COL,
            start_date=start_date,
            end_date=end_date,
            allow_missing_close=True,
        ),
        upro=fetch_stooq_close_series(
            UPRO_STOOQ_SYMBOL,
            UPRO_NOMINAL_COL,
            start_date=start_date,
            end_date=end_date,
            allow_missing_close=True,
        ),
        qld=fetch_stooq_close_series(
            QLD_STOOQ_SYMBOL,
            QLD_NOMINAL_COL,
            start_date=start_date,
            end_date=end_date,
            allow_missing_close=True,
        ),
    )
