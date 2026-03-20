"""End-to-end orchestration for building and persisting CAGR estimation data."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from .config import (
    AppSettings,
    DATE_COL,
    LEVERAGED_SECURITY_SPECS,
    NASDAQ_100_NOMINAL_COL,
    NASDAQ_NOMINAL_COL,
    NASDAQ_REAL_COL,
    OUTPUT_COLUMNS,
    SP500_NOMINAL_COL,
    SP500_REAL_COL,
    TRADING_DAYS_PER_YEAR,
)
from .fred_client import fetch_default_series
from .leveraged import calculate_leveraged_series, overlay_actual_series
from .transform import add_real_terms_column, build_inflation_factor_frame


def build_security_dataset(
    *,
    settings: Optional[AppSettings] = None,
    start_date: str = "1900-01-01",
    end_date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Build the full dataset with nominal + real terms for index and synthetic ETF values."""

    active_settings = settings or AppSettings()
    raw = fetch_default_series(
        start_date=start_date,
        end_date=end_date,
        cpi_start_date="1900-01-01",
        cpi_end_date=None,
        session=session,
    )

    index_frame_by_column = {
        NASDAQ_NOMINAL_COL: raw.nasdaq,
        NASDAQ_100_NOMINAL_COL: raw.nasdaq100,
        SP500_NOMINAL_COL: raw.sp500,
    }
    actual_frame_by_symbol = {
        "TQQQ": raw.tqqq,
        "UPRO": raw.upro,
        "QLD": raw.qld,
    }
    leveraged_frames: list[pd.DataFrame] = []
    for spec in LEVERAGED_SECURITY_SPECS:
        source_frame = index_frame_by_column[spec.underlying_column]
        modeled_frame = (
            calculate_leveraged_series(
                source_frame,
                spec.underlying_column,
                leverage=spec.leverage,
                annual_mer=spec.annual_mer,
                start_value=active_settings.leveraged_start_value,
                trading_days_per_year=TRADING_DAYS_PER_YEAR,
                output_column=spec.output_nominal_column,
            )
        )
        leveraged_frames.append(
            overlay_actual_series(
                modeled_frame,
                actual_frame_by_symbol[spec.symbol],
                output_column=spec.output_nominal_column,
            )
        )

    combined = (
        raw.nasdaq.merge(raw.sp500, on=DATE_COL, how="outer")
        .sort_values(DATE_COL)
        .reset_index(drop=True)
    )
    for leveraged_frame in leveraged_frames:
        combined = combined.merge(leveraged_frame, on=DATE_COL, how="outer")
    combined = combined.sort_values(DATE_COL).reset_index(drop=True)

    inflation = build_inflation_factor_frame(raw.cpi, combined[DATE_COL])
    combined = combined.merge(inflation, on=DATE_COL, how="left")

    combined = add_real_terms_column(combined, NASDAQ_NOMINAL_COL, NASDAQ_REAL_COL)
    combined = add_real_terms_column(combined, SP500_NOMINAL_COL, SP500_REAL_COL)
    for spec in LEVERAGED_SECURITY_SPECS:
        combined = add_real_terms_column(
            combined,
            spec.output_nominal_column,
            spec.output_real_column,
        )

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
