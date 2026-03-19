"""CLI entry point for refreshing the security estimation CSV."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.cagr_finance.config import AppSettings, DATE_COL
from lib.cagr_finance.pipeline import refresh_dataset_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh NASDAQ/S&P/TQQQ/UPRO/QLD nominal and real-term estimates into a CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (defaults to data/security_estimates.csv).",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=0.0,
        help="If > 0, keep refreshing forever with this delay between updates.",
    )
    return parser.parse_args()


def run_once(args: argparse.Namespace) -> None:
    settings = AppSettings()
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
