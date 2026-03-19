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
