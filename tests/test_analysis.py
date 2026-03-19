"""Unit tests for security-level CAGR analysis."""

from __future__ import annotations

import unittest

import pandas as pd

from lib.cagr_finance.analysis import (
    analyze_security_from_dataset,
    parse_security_selection,
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


if __name__ == "__main__":
    unittest.main()
