"""CLI for CAGR, start/end nominal, and start/end real analysis by security."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.cagr_finance.analysis import analyze_securities_period_and_print
from lib.cagr_finance.config import DEFAULT_STARTING_NOMINAL_VALUE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze CAGR and start/end nominal-real values for TQQQ, UPRO, QLD, NASDAQ, and SP500."
        )
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--security",
        default="ALL",
        help=(
            "Security selection. Use one symbol or comma-separated list: "
            "TQQQ, UPRO, QLD, NASDAQ, SP500, S&P500, or ALL."
        ),
    )
    parser.add_argument(
        "--starting-nominal-value",
        type=float,
        default=DEFAULT_STARTING_NOMINAL_VALUE,
        help=(
            "Starting nominal value for synthetic leveraged securities (TQQQ/UPRO/QLD). "
            "Indexes use observed index levels."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyze_securities_period_and_print(
        start_date=args.start_date,
        end_date=args.end_date,
        securities=[args.security],
        starting_nominal_value=args.starting_nominal_value,
    )


if __name__ == "__main__":
    main()
