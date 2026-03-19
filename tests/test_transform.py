"""Unit tests for inflation factor alignment and real-term conversion."""

from __future__ import annotations

import unittest

import pandas as pd

from lib.cagr_finance.config import CPI_INDEX_COL, DATE_COL, INFLATION_FACTOR_COL
from lib.cagr_finance.transform import add_real_terms_column, build_inflation_factor_frame


class TransformTests(unittest.TestCase):
    def test_build_inflation_factor_frame_uses_latest_ratio(self) -> None:
        cpi = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
                CPI_INDEX_COL: [100.0, 110.0, 121.0],
            }
        )
        target_dates = pd.to_datetime(["2024-01-15", "2024-02-15", "2024-03-15"])

        result = build_inflation_factor_frame(cpi, target_dates)

        self.assertAlmostEqual(result[INFLATION_FACTOR_COL].iloc[0], 1.21, places=9)
        self.assertAlmostEqual(result[INFLATION_FACTOR_COL].iloc[1], 1.1, places=9)
        self.assertAlmostEqual(result[INFLATION_FACTOR_COL].iloc[2], 1.0, places=9)

    def test_add_real_terms_column(self) -> None:
        frame = pd.DataFrame(
            {
                "nominal": [100.0, 200.0],
                INFLATION_FACTOR_COL: [1.5, 0.5],
            }
        )

        result = add_real_terms_column(frame, "nominal", "real")

        self.assertAlmostEqual(result["real"].iloc[0], 150.0, places=9)
        self.assertAlmostEqual(result["real"].iloc[1], 100.0, places=9)


if __name__ == "__main__":
    unittest.main()
