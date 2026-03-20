"""Security-level CAGR analysis for user-specified date windows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable, Optional

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
LIGHT_ORANGE = "\033[38;5;215m"
ORANGE = "\033[38;5;208m"
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
    nominal_simple_return: float
    real_simple_return: float
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


def _expand_start_date_for_anchor(date_value: str | pd.Timestamp, days: int = 7) -> str:
    """Fetch a small buffer before the requested start so non-trading days can anchor."""

    return str((_parse_date(date_value) - pd.Timedelta(days=days)).date())


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


def _calculate_simple_return(*, start_value: float, end_value: float) -> float:
    if start_value <= 0:
        raise ValueError("Simple return requires a positive start value.")
    return (end_value / start_value) - 1.0


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
    security_frame = dataset[[DATE_COL, nominal_col, real_col]].dropna(subset=[nominal_col, real_col])
    security_frame = security_frame.sort_values(DATE_COL).reset_index(drop=True)

    start_window = security_frame.loc[security_frame[DATE_COL] <= requested_start]
    start_fallback_to_future = False
    if start_window.empty:
        start_window = security_frame.loc[security_frame[DATE_COL] >= requested_start]
        start_fallback_to_future = True

    end_window = security_frame.loc[security_frame[DATE_COL] <= requested_end]

    if start_window.empty or end_window.empty:
        raise ValueError(
            f"No data for {symbol} between {requested_start.date()} and {requested_end.date()}."
        )

    first = start_window.iloc[0] if start_fallback_to_future else start_window.iloc[-1]
    last = end_window.iloc[-1]
    if pd.Timestamp(first[DATE_COL]) >= pd.Timestamp(last[DATE_COL]):
        raise ValueError(
            f"No data for {symbol} between {requested_start.date()} and {requested_end.date()}."
        )

    start_nominal_value = float(first[nominal_col])
    end_nominal_value = float(last[nominal_col])
    start_real_raw = float(first[real_col])
    end_real_raw = float(last[real_col])

    # Rebase real values so nominal and real start from the same value.
    # This keeps comparisons intuitive while preserving real-return effects at the end date.
    real_growth_multiplier = end_real_raw / start_real_raw
    start_real_value = start_nominal_value
    end_real_value = start_real_value * real_growth_multiplier

    nominal_simple_return = _calculate_simple_return(
        start_value=start_nominal_value,
        end_value=end_nominal_value,
    )
    real_simple_return = _calculate_simple_return(
        start_value=start_real_value,
        end_value=end_real_value,
    )

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
        nominal_simple_return=nominal_simple_return,
        real_simple_return=real_simple_return,
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
    dataset_start_date = _expand_start_date_for_anchor(start_date)
    dataset = build_security_dataset(
        settings=settings,
        start_date=dataset_start_date,
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

    if len(results) == 1:
        return results

    common_actual_start = max(result.actual_start_date for result in results)
    common_actual_end = min(result.actual_end_date for result in results)
    if common_actual_start >= common_actual_end:
        raise ValueError("Selected securities do not share an overlapping actual date range.")

    standardized_results: list[SecurityAnalysisResult] = []
    for result in results:
        standardized = analyze_security_from_dataset(
            dataset,
            security=result.security,
            start_date=common_actual_start,
            end_date=common_actual_end,
        )
        standardized_results.append(
            replace(
                standardized,
                requested_start_date=result.requested_start_date,
                requested_end_date=result.requested_end_date,
            )
        )
    return standardized_results


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


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _format_percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def _build_results_table(
    results: list[SecurityAnalysisResult],
    *,
    starting_nominal_value: float,
) -> str:
    row_specs: list[tuple[str, str, Callable[[SecurityAnalysisResult], str]]] = [
        (
            "Nominal",
            GREEN,
            lambda result: _format_currency(starting_nominal_value * (1.0 + result.nominal_simple_return)),
        ),
        (
            "Real",
            GREEN,
            lambda result: _format_currency(starting_nominal_value * (1.0 + result.real_simple_return)),
        ),
        ("Nominal CAGR", ORANGE, lambda result: _format_percentage(result.nominal_cagr)),
        ("Real CAGR", ORANGE, lambda result: _format_percentage(result.real_cagr)),
        ("Nominal Return", LIGHT_ORANGE, lambda result: _format_percentage(result.nominal_simple_return)),
        ("Real Return", LIGHT_ORANGE, lambda result: _format_percentage(result.real_simple_return)),
    ]

    metric_header = "Metric"
    first_column_width = max(len(metric_header), *(len(label) for label, _, _ in row_specs))
    security_widths = []
    for result in results:
        values = [formatter(result) for _, _, formatter in row_specs]
        security_widths.append(max(len(result.security), *(len(value) for value in values)))

    def _format_row(cells: list[str]) -> str:
        padded_cells = [cells[0].ljust(first_column_width)]
        for index, cell in enumerate(cells[1:]):
            padded_cells.append(cell.ljust(security_widths[index]))
        return " | ".join(padded_cells)

    header_cells = [metric_header, *(result.security for result in results)]
    divider_cells = ["-" * first_column_width, *("-" * width for width in security_widths)]

    lines = [f"{BLUE}{_format_row(header_cells)}{RESET}", _format_row(divider_cells)]
    for label, color, formatter in row_specs:
        row_cells = [label, *(formatter(result) for result in results)]
        lines.append(f"{color}{_format_row(row_cells)}{RESET}")
    return "\n".join(lines)


def print_analysis_results(
    results: Iterable[SecurityAnalysisResult],
    *,
    starting_nominal_value: float,
) -> None:
    """Print analysis summaries to the command line."""

    materialized_results = list(results)
    if not materialized_results:
        return

    requested_start = materialized_results[0].requested_start_date
    requested_end = materialized_results[0].requested_end_date
    actual_start = materialized_results[0].actual_start_date
    actual_end = materialized_results[0].actual_end_date

    print(f"{RED}Requested window:{RESET} {requested_start.date()} to {requested_end.date()}")
    print(f"{RED}Actual window:{RESET}    {actual_start.date()} to {actual_end.date()}")
    print(f"{RED}Starting value:{RESET}   {_format_currency(starting_nominal_value)}")
    print()
    print(
        _build_results_table(
            materialized_results,
            starting_nominal_value=starting_nominal_value,
        )
    )
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
    print_analysis_results(results, starting_nominal_value=starting_nominal_value)
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
    print_analysis_results([result], starting_nominal_value=starting_nominal_value)
    return result
