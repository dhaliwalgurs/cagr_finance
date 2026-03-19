"""CLI entry point for refreshing the security estimation CSV."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from cagr_finance.config import AppSettings, DATE_COL  # noqa: E402
from cagr_finance.pipeline import refresh_dataset_csv  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh NASDAQ/S&P/TQQQ/UPRO nominal and real-term estimates into a CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (defaults to data/security_estimates.csv).",
    )
    parser.add_argument(
        "--start-value",
        type=float,
        default=100.0,
        help="Starting value for synthetic TQQQ/UPRO series.",
    )
    parser.add_argument(
        "--tqqq-mer",
        type=float,
        default=0.0084,
        help="Annual MER for TQQQ synthetic series as decimal (for example 0.0084).",
    )
    parser.add_argument(
        "--upro-mer",
        type=float,
        default=0.0091,
        help="Annual MER for UPRO synthetic series as decimal (for example 0.0091).",
    )
    parser.add_argument(
        "--trading-days",
        type=int,
        default=252,
        help="Trading days per year used to convert annual MER to daily drag.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=0.0,
        help="If > 0, keep refreshing forever with this delay between updates.",
    )
    return parser.parse_args()


def run_once(args: argparse.Namespace) -> None:
    settings = AppSettings(
        leveraged_start_value=args.start_value,
        trading_days_per_year=args.trading_days,
        tqqq_mer_annual=args.tqqq_mer,
        upro_mer_annual=args.upro_mer,
    )

    frame = refresh_dataset_csv(output_path=args.output, settings=settings)
    output_path = Path(args.output) if args.output else settings.output_csv_path

    latest_date = frame[DATE_COL].max() if not frame.empty else "N/A"
    print(f"Wrote {len(frame)} rows to {output_path}")
    print(f"Latest date in dataset: {latest_date}")


def main() -> None:
    args = parse_args()

    if args.interval_seconds <= 0:
        run_once(args)
        return

    while True:
        run_once(args)
        print(f"Sleeping for {args.interval_seconds} seconds before next refresh...")
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
