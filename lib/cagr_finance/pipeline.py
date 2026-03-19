"""End-to-end orchestration for building and persisting CAGR estimation data."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from .config import (
    AppSettings,
    DATE_COL,
    NASDAQ_NOMINAL_COL,
    NASDAQ_REAL_COL,
    OUTPUT_COLUMNS,
    SP500_NOMINAL_COL,
    SP500_REAL_COL,
    TQQQ_NOMINAL_COL,
    TQQQ_REAL_COL,
    UPRO_NOMINAL_COL,
    UPRO_REAL_COL,
)
from .fred_client import fetch_default_series
from .leveraged import calculate_leveraged_series
from .transform import add_real_terms_column, build_inflation_factor_frame


def build_security_dataset(
    *,
    settings: Optional[AppSettings] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Build the full dataset with nominal + real terms for index and synthetic ETF values."""

    active_settings = settings or AppSettings()
    raw = fetch_default_series(session=session)

    tqqq_frame = calculate_leveraged_series(
        raw.nasdaq,
        NASDAQ_NOMINAL_COL,
        leverage=active_settings.tqqq_leverage,
        annual_mer=active_settings.tqqq_mer_annual,
        start_value=active_settings.leveraged_start_value,
        trading_days_per_year=active_settings.trading_days_per_year,
        output_column=TQQQ_NOMINAL_COL,
    )

    upro_frame = calculate_leveraged_series(
        raw.sp500,
        SP500_NOMINAL_COL,
        leverage=active_settings.upro_leverage,
        annual_mer=active_settings.upro_mer_annual,
        start_value=active_settings.leveraged_start_value,
        trading_days_per_year=active_settings.trading_days_per_year,
        output_column=UPRO_NOMINAL_COL,
    )

    combined = (
        raw.nasdaq.merge(raw.sp500, on=DATE_COL, how="outer")
        .merge(tqqq_frame, on=DATE_COL, how="outer")
        .merge(upro_frame, on=DATE_COL, how="outer")
        .sort_values(DATE_COL)
        .reset_index(drop=True)
    )

    inflation = build_inflation_factor_frame(raw.cpi, combined[DATE_COL])
    combined = combined.merge(inflation, on=DATE_COL, how="left")

    combined = add_real_terms_column(combined, NASDAQ_NOMINAL_COL, NASDAQ_REAL_COL)
    combined = add_real_terms_column(combined, SP500_NOMINAL_COL, SP500_REAL_COL)
    combined = add_real_terms_column(combined, TQQQ_NOMINAL_COL, TQQQ_REAL_COL)
    combined = add_real_terms_column(combined, UPRO_NOMINAL_COL, UPRO_REAL_COL)

    combined = combined[OUTPUT_COLUMNS]
    return combined


def refresh_dataset_csv(
    *,
    output_path: Optional[str | Path] = None,
    settings: Optional[AppSettings] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Build dataset and overwrite the CSV database file with latest values."""

    active_settings = settings or AppSettings()
    destination = Path(output_path) if output_path is not None else active_settings.output_csv_path

    frame = build_security_dataset(settings=active_settings, session=session)

    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False, date_format="%Y-%m-%d")
    return frame
