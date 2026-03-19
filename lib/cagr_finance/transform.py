"""Data alignment and inflation-adjustment helpers."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .config import CPI_INDEX_COL, DATE_COL, INFLATION_FACTOR_COL


def _normalize_date_series(dates: Iterable[pd.Timestamp]) -> pd.DataFrame:
    normalized = pd.DataFrame({DATE_COL: pd.to_datetime(pd.Series(dates), errors="coerce")})
    normalized = (
        normalized.dropna(subset=[DATE_COL])
        .sort_values(DATE_COL)
        .drop_duplicates(subset=[DATE_COL], keep="last")
        .reset_index(drop=True)
    )
    return normalized


def build_inflation_factor_frame(cpi_frame: pd.DataFrame, target_dates: Iterable[pd.Timestamp]) -> pd.DataFrame:
    """
    Align monthly CPI observations onto target dates and convert to an inflation factor.

    Inflation factor is defined as: latest_cpi / cpi_on_target_date.
    """

    cpi = cpi_frame[[DATE_COL, CPI_INDEX_COL]].copy()
    cpi[DATE_COL] = pd.to_datetime(cpi[DATE_COL], errors="coerce")
    cpi[CPI_INDEX_COL] = pd.to_numeric(cpi[CPI_INDEX_COL], errors="coerce")
    cpi = (
        cpi.dropna(subset=[DATE_COL, CPI_INDEX_COL])
        .sort_values(DATE_COL)
        .drop_duplicates(subset=[DATE_COL], keep="last")
        .reset_index(drop=True)
    )
    if cpi.empty:
        return pd.DataFrame(columns=[DATE_COL, INFLATION_FACTOR_COL])

    target = _normalize_date_series(target_dates)
    if target.empty:
        return pd.DataFrame(columns=[DATE_COL, INFLATION_FACTOR_COL])

    # Use the latest available CPI at or before each target date.
    aligned = pd.merge_asof(target, cpi, on=DATE_COL, direction="backward")

    latest_cpi = cpi[CPI_INDEX_COL].iloc[-1]
    aligned[INFLATION_FACTOR_COL] = latest_cpi / aligned[CPI_INDEX_COL]

    return aligned[[DATE_COL, INFLATION_FACTOR_COL]]


def add_real_terms_column(
    frame: pd.DataFrame,
    nominal_column: str,
    real_column: str,
    *,
    inflation_column: str = INFLATION_FACTOR_COL,
) -> pd.DataFrame:
    """Add a real-terms value column by multiplying nominal value by inflation factor."""

    result = frame.copy()
    result[real_column] = result[nominal_column] * result[inflation_column]
    return result
