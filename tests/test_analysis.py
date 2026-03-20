"""Unit tests for security-level CAGR analysis."""

from __future__ import annotations

import io
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from lib.cagr_finance.analysis import (
    SecurityAnalysisResult,
    analyze_securities_period,
    analyze_security_from_dataset,
    parse_security_selection,
    print_analysis_results,
)
from lib.cagr_finance.config import (
    DATE_COL,
    NASDAQ_NOMINAL_COL,
    NASDAQ_REAL_COL,
    QLD_NOMINAL_COL,
    QLD_REAL_COL,
    SP500_NOMINAL_COL,
    SP500_REAL_COL,
    TQQQ_NOMINAL_COL,
    TQQQ_REAL_COL,
    UPRO_NOMINAL_COL,
    UPRO_REAL_COL,
)


class AnalysisTests(unittest.TestCase):
    TQQQ_ANNUAL_RETURNS = {
        2025: 34.37,
        2024: 58.23,
        2023: 198.26,
        2022: -79.08,
        2021: 82.98,
        2020: 110.05,
        2019: 133.83,
        2018: -19.81,
        2017: 118.06,
        2016: 11.38,
        2015: 17.23,
        2014: 57.09,
        2013: 139.73,
        2012: 52.29,
        2011: -8.05,
    }
    TQQQ_ANNUAL_TOLERANCE_PERCENT = 1.0

    def test_parse_security_selection_with_all(self) -> None:
        result = parse_security_selection("ALL")
        self.assertEqual(result, ["TQQQ", "UPRO", "QLD", "NASDAQ", "SP500"])

    def test_analyze_security_from_dataset_returns_expected_values(self) -> None:
        frame = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-02", "2024-07-02", "2025-01-02"]),
                TQQQ_NOMINAL_COL: [100.0, 110.0, 121.0],
                TQQQ_REAL_COL: [125.0, 135.0, 147.5],
                UPRO_NOMINAL_COL: [100.0, 105.0, 110.0],
                UPRO_REAL_COL: [100.0, 103.0, 108.0],
                QLD_NOMINAL_COL: [100.0, 108.0, 116.0],
                QLD_REAL_COL: [100.0, 106.0, 113.0],
                NASDAQ_NOMINAL_COL: [15000.0, 16000.0, 17000.0],
                NASDAQ_REAL_COL: [15000.0, 15800.0, 16600.0],
                SP500_NOMINAL_COL: [4500.0, 4700.0, 4900.0],
                SP500_REAL_COL: [4500.0, 4650.0, 4800.0],
            }
        )

        result = analyze_security_from_dataset(
            frame,
            security="TQQQ",
            start_date="2024-01-01",
            end_date="2025-01-31",
        )

        self.assertEqual(result.security, "TQQQ")
        self.assertEqual(result.actual_start_date, pd.Timestamp("2024-01-02"))
        self.assertEqual(result.actual_end_date, pd.Timestamp("2025-01-02"))
        self.assertAlmostEqual(result.start_nominal_value, 100.0, places=9)
        self.assertAlmostEqual(result.end_nominal_value, 121.0, places=9)
        self.assertAlmostEqual(result.start_real_value, 100.0, places=9)
        self.assertAlmostEqual(result.end_real_value, 118.0, places=9)
        self.assertAlmostEqual(result.nominal_simple_return, 0.21, places=9)
        self.assertAlmostEqual(result.real_simple_return, 0.18, places=9)

        # Real series is rebased to nominal start value.
        self.assertNotAlmostEqual(float(frame[TQQQ_REAL_COL].iloc[0]), result.start_real_value, places=9)

        self.assertGreater(result.nominal_cagr, 0.0)
        self.assertGreater(result.real_cagr, 0.0)

    def test_analyze_security_from_dataset_uses_previous_available_start_date(self) -> None:
        frame = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-12-31", "2025-01-02", "2025-12-31"]),
                TQQQ_NOMINAL_COL: [100.0, 110.0, 117.23],
                TQQQ_REAL_COL: [100.0, 110.0, 117.23],
                UPRO_NOMINAL_COL: [100.0, 100.0, 100.0],
                UPRO_REAL_COL: [100.0, 100.0, 100.0],
                QLD_NOMINAL_COL: [100.0, 100.0, 100.0],
                QLD_REAL_COL: [100.0, 100.0, 100.0],
                NASDAQ_NOMINAL_COL: [100.0, 100.0, 100.0],
                NASDAQ_REAL_COL: [100.0, 100.0, 100.0],
                SP500_NOMINAL_COL: [100.0, 100.0, 100.0],
                SP500_REAL_COL: [100.0, 100.0, 100.0],
            }
        )

        result = analyze_security_from_dataset(
            frame,
            security="TQQQ",
            start_date="2025-01-01",
            end_date="2026-01-01",
        )

        self.assertEqual(result.actual_start_date, pd.Timestamp("2024-12-31"))
        self.assertEqual(result.actual_end_date, pd.Timestamp("2025-12-31"))
        self.assertAlmostEqual(result.nominal_simple_return * 100.0, 17.23, places=9)

    def test_tqqq_annual_returns_match_benchmark_table_within_tolerance(self) -> None:
        dataset = pd.read_csv(
            Path("data/security_estimates.csv"),
            parse_dates=[DATE_COL],
        )

        for year, expected_return in self.TQQQ_ANNUAL_RETURNS.items():
            result = analyze_security_from_dataset(
                dataset,
                security="TQQQ",
                start_date=f"{year}-01-01",
                end_date=f"{year + 1}-01-01",
            )

            actual_return_percent = result.nominal_simple_return * 100.0
            self.assertAlmostEqual(
                actual_return_percent,
                expected_return,
                delta=self.TQQQ_ANNUAL_TOLERANCE_PERCENT,
            )

    @patch("lib.cagr_finance.analysis.build_security_dataset")
    def test_multi_security_analysis_standardizes_actual_window(self, mock_build_security_dataset) -> None:
        mock_build_security_dataset.return_value = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-01", "2024-01-02", "2024-12-31"]),
                TQQQ_NOMINAL_COL: [None, 100.0, 120.0],
                TQQQ_REAL_COL: [None, 100.0, 118.0],
                UPRO_NOMINAL_COL: [100.0, 101.0, 121.2],
                UPRO_REAL_COL: [100.0, 101.0, 119.0],
                QLD_NOMINAL_COL: [None, 100.0, 115.0],
                QLD_REAL_COL: [None, 100.0, 113.0],
                NASDAQ_NOMINAL_COL: [100.0, 101.0, 110.0],
                NASDAQ_REAL_COL: [100.0, 101.0, 108.0],
                SP500_NOMINAL_COL: [100.0, 100.5, 108.0],
                SP500_REAL_COL: [100.0, 100.5, 106.0],
            }
        )

        results = analyze_securities_period(
            start_date="2024-01-01",
            end_date="2025-01-01",
            securities=["ALL"],
            starting_nominal_value=100.0,
        )

        self.assertEqual([result.actual_start_date for result in results], [pd.Timestamp("2024-01-02")] * 5)
        self.assertEqual([result.actual_end_date for result in results], [pd.Timestamp("2024-12-31")] * 5)

    def test_print_analysis_results_renders_table(self) -> None:
        results = [
            SecurityAnalysisResult(
                security="TQQQ",
                requested_start_date=pd.Timestamp("2024-01-01"),
                requested_end_date=pd.Timestamp("2025-01-01"),
                actual_start_date=pd.Timestamp("2024-01-02"),
                actual_end_date=pd.Timestamp("2024-12-31"),
                start_nominal_value=100.0,
                end_nominal_value=120.0,
                start_real_value=100.0,
                end_real_value=118.0,
                nominal_simple_return=0.20,
                real_simple_return=0.18,
                nominal_cagr=0.20,
                real_cagr=0.18,
            ),
            SecurityAnalysisResult(
                security="UPRO",
                requested_start_date=pd.Timestamp("2024-01-01"),
                requested_end_date=pd.Timestamp("2025-01-01"),
                actual_start_date=pd.Timestamp("2024-01-02"),
                actual_end_date=pd.Timestamp("2024-12-31"),
                start_nominal_value=100.0,
                end_nominal_value=110.0,
                start_real_value=100.0,
                end_real_value=108.0,
                nominal_simple_return=0.10,
                real_simple_return=0.08,
                nominal_cagr=0.10,
                real_cagr=0.08,
            ),
        ]

        stream = io.StringIO()
        with redirect_stdout(stream):
            print_analysis_results(results, starting_nominal_value=100.0)

        rendered = re.sub(r"\x1b\[[0-9;]*m", "", stream.getvalue())
        self.assertIn("Requested window: 2024-01-01 to 2025-01-01", rendered)
        self.assertIn("Actual window:    2024-01-02 to 2024-12-31", rendered)
        self.assertIn("Starting value:   $100.00", rendered)
        self.assertIn("Metric", rendered)
        self.assertIn("TQQQ", rendered)
        self.assertIn("UPRO", rendered)
        self.assertIn("Nominal Return", rendered)
        self.assertIn("20.00%", rendered)
        self.assertIn("Nominal        | $120.00", rendered)
        self.assertNotIn("$100.00 -> $120.00", rendered)


if __name__ == "__main__":
    unittest.main()
