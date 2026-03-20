"""Unit tests for leveraged synthetic return calculations."""

from __future__ import annotations

import unittest

import pandas as pd

from lib.cagr_finance.config import DATE_COL
from lib.cagr_finance.leveraged import calculate_leveraged_series, overlay_actual_series


class CalculateLeveragedSeriesTests(unittest.TestCase):
    def test_three_x_compounding_without_mer(self) -> None:
        frame = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "index": [100.0, 110.0, 99.0],
            }
        )

        result = calculate_leveraged_series(
            frame,
            "index",
            leverage=3.0,
            annual_mer=0.0,
            start_value=100.0,
            trading_days_per_year=252,
            output_column="synthetic",
        )

        self.assertAlmostEqual(result["synthetic"].iloc[0], 100.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[1], 130.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[2], 91.0, places=9)

    def test_mer_is_applied_as_daily_drag(self) -> None:
        frame = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "index": [100.0, 100.0, 100.0],
            }
        )

        result = calculate_leveraged_series(
            frame,
            "index",
            leverage=3.0,
            annual_mer=0.252,
            start_value=100.0,
            trading_days_per_year=252,
            output_column="synthetic",
        )

        self.assertAlmostEqual(result["synthetic"].iloc[0], 100.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[1], 99.9, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[2], 99.8001, places=7)

    def test_actual_series_overrides_modeled_path_from_first_overlap(self) -> None:
        modeled = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(
                    ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
                ),
                "synthetic": [100.0, 110.0, 121.0, 133.1],
            }
        )
        actual = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
                "synthetic": [10.0, 11.0, 12.0],
            }
        )

        result = overlay_actual_series(modeled, actual, output_column="synthetic")

        self.assertAlmostEqual(result["synthetic"].iloc[0], 100.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[1], 110.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[2], 121.0, places=9)
        self.assertAlmostEqual(result["synthetic"].iloc[3], 132.0, places=9)


if __name__ == "__main__":
    unittest.main()
