"""Security-level CAGR analysis for user-specified date windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd
import requests

from .config import (
    AppSettings,
    DATE_COL,
    DEFAULT_SECURITY_ORDER,
    DEFAULT_STARTING_NOMINAL_VALUE,
    SECURITY_ALIASES,
    SECURITY_COLUMN_MAP,
)
from .pipeline import build_security_dataset

GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"


@dataclass(frozen=True)
class SecurityAnalysisResult:
    """Computed summary metrics for one security over a requested date range."""

    security: str
    requested_start_date: pd.Timestamp
    requested_end_date: pd.Timestamp
    actual_start_date: pd.Timestamp
    actual_end_date: pd.Timestamp
    start_nominal_value: float
    end_nominal_value: float
    start_real_value: float
    end_real_value: float
    nominal_cagr: float
    real_cagr: float


def normalize_security_symbol(symbol: str) -> str:
    """Normalize security aliases and enforce supported symbols."""

    normalized = symbol.strip().upper()
    if normalized not in SECURITY_ALIASES:
        supported = ", ".join(DEFAULT_SECURITY_ORDER)
        raise ValueError(f"Unsupported security '{symbol}'. Supported: {supported}, ALL")
    return SECURITY_ALIASES[normalized]


def parse_security_selection(selection: str) -> list[str]:
    """Parse comma-separated security input into canonical symbols."""

    raw_tokens = [token.strip() for token in selection.split(",") if token.strip()]
    if not raw_tokens:
        raise ValueError("Security selection cannot be empty.")

    normalized_tokens = [normalize_security_symbol(token) for token in raw_tokens]
    if "ALL" in normalized_tokens:
        return list(DEFAULT_SECURITY_ORDER)

    seen: set[str] = set()
    ordered_unique: list[str] = []
    for token in normalized_tokens:
        if token not in seen:
            ordered_unique.append(token)
            seen.add(token)
    return ordered_unique


def _parse_date(date_value: str | pd.Timestamp) -> pd.Timestamp:
    parsed = pd.Timestamp(date_value)
    if pd.isna(parsed):
        raise ValueError(f"Invalid date value: {date_value}")
    return parsed.normalize()


def _calculate_cagr(
    *,
    start_value: float,
    end_value: float,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> float:
    if start_value <= 0 or end_value <= 0:
        raise ValueError("CAGR requires positive start and end values.")

    elapsed_days = (end_date - start_date).days
    if elapsed_days <= 0:
        raise ValueError("CAGR requires at least two distinct dates with non-null values.")

    elapsed_years = elapsed_days / 365.2425
    return (end_value / start_value) ** (1.0 / elapsed_years) - 1.0


def analyze_security_from_dataset(
    dataset: pd.DataFrame,
    *,
    security: str,
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
) -> SecurityAnalysisResult:
    """Compute start/end values and CAGR for one security from a prepared dataset."""

    symbol = normalize_security_symbol(security)
    if symbol == "ALL":
        raise ValueError("Use a specific security symbol, not ALL, for single-security analysis.")

    requested_start = _parse_date(start_date)
    requested_end = _parse_date(end_date)
    if requested_start > requested_end:
        raise ValueError("start_date must be earlier than or equal to end_date.")

    nominal_col, real_col = SECURITY_COLUMN_MAP[symbol]
    window = dataset.loc[
        (dataset[DATE_COL] >= requested_start) & (dataset[DATE_COL] <= requested_end),
        [DATE_COL, nominal_col, real_col],
    ].dropna(subset=[nominal_col, real_col])

    if window.empty:
        raise ValueError(
            f"No data for {symbol} between {requested_start.date()} and {requested_end.date()}."
        )

    window = window.sort_values(DATE_COL).reset_index(drop=True)
    first = window.iloc[0]
    last = window.iloc[-1]

    start_nominal_value = float(first[nominal_col])
    end_nominal_value = float(last[nominal_col])
    start_real_raw = float(first[real_col])
    end_real_raw = float(last[real_col])

    # Rebase real values so nominal and real start from the same value.
    # This keeps comparisons intuitive while preserving real-return effects at the end date.
    real_growth_multiplier = end_real_raw / start_real_raw
    start_real_value = start_nominal_value
    end_real_value = start_real_value * real_growth_multiplier

    nominal_cagr = _calculate_cagr(
        start_value=start_nominal_value,
        end_value=end_nominal_value,
        start_date=pd.Timestamp(first[DATE_COL]),
        end_date=pd.Timestamp(last[DATE_COL]),
    )
    real_cagr = _calculate_cagr(
        start_value=start_real_value,
        end_value=end_real_value,
        start_date=pd.Timestamp(first[DATE_COL]),
        end_date=pd.Timestamp(last[DATE_COL]),
    )

    return SecurityAnalysisResult(
        security=symbol,
        requested_start_date=requested_start,
        requested_end_date=requested_end,
        actual_start_date=pd.Timestamp(first[DATE_COL]),
        actual_end_date=pd.Timestamp(last[DATE_COL]),
        start_nominal_value=start_nominal_value,
        end_nominal_value=end_nominal_value,
        start_real_value=start_real_value,
        end_real_value=end_real_value,
        nominal_cagr=nominal_cagr,
        real_cagr=real_cagr,
    )


def analyze_securities_period(
    *,
    start_date: str,
    end_date: str,
    securities: Iterable[str],
    starting_nominal_value: float = DEFAULT_STARTING_NOMINAL_VALUE,
    session: Optional[requests.Session] = None,
) -> list[SecurityAnalysisResult]:
    """Build windowed data once, then analyze one or more securities."""

    if starting_nominal_value <= 0:
        raise ValueError("starting_nominal_value must be positive.")

    requested_symbols: list[str] = []
    for security in securities:
        requested_symbols.extend(parse_security_selection(security))

    if not requested_symbols:
        raise ValueError("At least one security must be provided.")

    deduped_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in requested_symbols:
        if symbol not in seen:
            deduped_symbols.append(symbol)
            seen.add(symbol)

    settings = AppSettings(leveraged_start_value=starting_nominal_value)
    dataset = build_security_dataset(
        settings=settings,
        start_date=start_date,
        end_date=end_date,
        session=session,
    )

    results: list[SecurityAnalysisResult] = []
    for symbol in deduped_symbols:
        results.append(
            analyze_security_from_dataset(
                dataset,
                security=symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )
    return results


def analyze_security_period(
    *,
    start_date: str,
    end_date: str,
    security: str,
    starting_nominal_value: float = DEFAULT_STARTING_NOMINAL_VALUE,
    session: Optional[requests.Session] = None,
) -> SecurityAnalysisResult:
    """Analyze one security and return structured output for reuse elsewhere."""

    results = analyze_securities_period(
        start_date=start_date,
        end_date=end_date,
        securities=[security],
        starting_nominal_value=starting_nominal_value,
        session=session,
    )
    return results[0]


def print_analysis_results(results: Iterable[SecurityAnalysisResult]) -> None:
    """Print analysis summaries to the command line."""

    for result in results:
        print(f"{RED}Security: {result.security}{RESET}")
        print(
            "Requested window: "
            f"{result.requested_start_date.date()} to {result.requested_end_date.date()}"
        )
        print(
            "Actual window: "
            f"{result.actual_start_date.date()} to {result.actual_end_date.date()}"
        )
        print(
            f"{GREEN}Nominal: ${result.start_nominal_value:,.2f} -> "
            f"${result.end_nominal_value:,.2f}{RESET}"
        )
        print(
            f"{GREEN}Real: ${result.start_real_value:,.2f} -> "
            f"${result.end_real_value:,.2f}{RESET}"
        )
        print(f"{BLUE}Nominal CAGR: {result.nominal_cagr * 100:.2f}%{RESET}")
        print(f"{BLUE}Real CAGR: {result.real_cagr * 100:.2f}%{RESET}")
        print()


def analyze_securities_period_and_print(
    *,
    start_date: str,
    end_date: str,
    securities: Iterable[str],
    starting_nominal_value: float = DEFAULT_STARTING_NOMINAL_VALUE,
    session: Optional[requests.Session] = None,
) -> list[SecurityAnalysisResult]:
    """Run security analysis and print summaries while returning structured outputs."""

    results = analyze_securities_period(
        start_date=start_date,
        end_date=end_date,
        securities=securities,
        starting_nominal_value=starting_nominal_value,
        session=session,
    )
    print_analysis_results(results)
    return results


def analyze_security_period_and_print(
    *,
    start_date: str,
    end_date: str,
    security: str,
    starting_nominal_value: float = DEFAULT_STARTING_NOMINAL_VALUE,
    session: Optional[requests.Session] = None,
) -> SecurityAnalysisResult:
    """Analyze one security, print CLI output, and return structured results."""

    result = analyze_security_period(
        start_date=start_date,
        end_date=end_date,
        security=security,
        starting_nominal_value=starting_nominal_value,
        session=session,
    )
    print_analysis_results([result])
    return result
