"""Synthetic leveraged ETF calculations."""

from __future__ import annotations

import pandas as pd

from .config import DATE_COL


def calculate_leveraged_series(
    index_frame: pd.DataFrame,
    index_column: str,
    *,
    leverage: float,
    annual_mer: float,
    start_value: float,
    trading_days_per_year: int,
    output_column: str,
) -> pd.DataFrame:
    """
    Convert an index price series into a leveraged synthetic series.

    Formula per day:
    leveraged_return = (leverage * index_daily_return) - (annual_mer / trading_days_per_year)
    """

    frame = index_frame[[DATE_COL, index_column]].copy()
    frame = (
        frame.dropna(subset=[DATE_COL, index_column])
        .sort_values(DATE_COL)
        .reset_index(drop=True)
    )
    if frame.empty:
        return pd.DataFrame(columns=[DATE_COL, output_column])

    daily_index_returns = frame[index_column].pct_change()
    daily_mer_drag = annual_mer / float(trading_days_per_year)
    leveraged_returns = (leverage * daily_index_returns) - daily_mer_drag

    # Avoid impossible losses below -100% that can occur in synthetic stress cases.
    leveraged_returns = leveraged_returns.clip(lower=-0.999999)
    leveraged_returns.iloc[0] = 0.0

    frame[output_column] = start_value * (1.0 + leveraged_returns).cumprod()
    return frame[[DATE_COL, output_column]]


def overlay_actual_series(
    modeled_frame: pd.DataFrame,
    actual_frame: pd.DataFrame,
    *,
    output_column: str,
) -> pd.DataFrame:
    """
    Replace modeled values with actual prices from the first overlap onward.

    Actual prices are rescaled so the first overlapping actual close matches the
    modeled level, preserving continuity and the requested synthetic start value.
    """

    modeled = modeled_frame[[DATE_COL, output_column]].copy()
    modeled = modeled.dropna(subset=[DATE_COL, output_column]).sort_values(DATE_COL)

    actual = actual_frame[[DATE_COL, output_column]].copy()
    actual = actual.dropna(subset=[DATE_COL, output_column]).sort_values(DATE_COL)

    if modeled.empty or actual.empty:
        return modeled.reset_index(drop=True)

    merged = modeled.merge(
        actual,
        on=DATE_COL,
        how="outer",
        suffixes=("_modeled", "_actual"),
    ).sort_values(DATE_COL)

    overlap = merged.dropna(subset=[f"{output_column}_modeled", f"{output_column}_actual"])
    if overlap.empty:
        return modeled.reset_index(drop=True)

    first_overlap = overlap.iloc[0]
    scale_factor = (
        float(first_overlap[f"{output_column}_modeled"])
        / float(first_overlap[f"{output_column}_actual"])
    )

    merged[output_column] = merged[f"{output_column}_modeled"]
    actual_mask = merged[f"{output_column}_actual"].notna()
    merged.loc[actual_mask, output_column] = (
        merged.loc[actual_mask, f"{output_column}_actual"] * scale_factor
    )

    return merged[[DATE_COL, output_column]].reset_index(drop=True)
