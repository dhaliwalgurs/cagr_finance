"""Unit tests for market data client date-range behavior and fallbacks."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from lib.cagr_finance.config import DATE_COL, SP500_NOMINAL_COL
from lib.cagr_finance.fred_client import fetch_default_series, fetch_sp500_nominal_series


class FredClientTests(unittest.TestCase):
    @patch("lib.cagr_finance.fred_client.fetch_sp500_nominal_series")
    @patch("lib.cagr_finance.fred_client.fetch_fred_series")
    def test_fetch_default_series_enforces_history_floors(
        self,
        mock_fetch_fred_series,
        mock_fetch_sp500_nominal_series,
    ) -> None:
        def _frame_for(output_column: str) -> pd.DataFrame:
            return pd.DataFrame({DATE_COL: [pd.Timestamp("2020-01-01")], output_column: [1.0]})

        mock_fetch_fred_series.side_effect = (
            lambda _series_id, output_column, **_kwargs: _frame_for(output_column)
        )
        mock_fetch_sp500_nominal_series.return_value = _frame_for(SP500_NOMINAL_COL)

        fetch_default_series(start_date="1900-01-01", end_date="2020-01-02")

        nasdaq_call = mock_fetch_fred_series.call_args_list[0]
        cpi_call = mock_fetch_fred_series.call_args_list[1]

        self.assertEqual(nasdaq_call.kwargs["start_date"], "1971-02-05")
        self.assertEqual(cpi_call.kwargs["start_date"], "1900-01-01")

        mock_fetch_sp500_nominal_series.assert_called_once()
        sp500_call = mock_fetch_sp500_nominal_series.call_args_list[0]
        self.assertEqual(sp500_call.kwargs["start_date"], "1957-03-04")

    @patch("lib.cagr_finance.fred_client.fetch_stooq_close_series")
    @patch("lib.cagr_finance.fred_client.fetch_fred_series")
    def test_sp500_uses_stooq_when_fred_history_is_too_short(
        self,
        mock_fetch_fred_series,
        mock_fetch_stooq_close_series,
    ) -> None:
        mock_fetch_fred_series.return_value = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["2016-03-21", "2016-03-22"]),
                SP500_NOMINAL_COL: [2051.6, 2049.8],
            }
        )
        mock_fetch_stooq_close_series.return_value = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["1957-03-04", "1957-03-05"]),
                SP500_NOMINAL_COL: [44.06, 44.22],
            }
        )

        frame = fetch_sp500_nominal_series(start_date="1957-03-04", end_date="2020-01-02")

        mock_fetch_stooq_close_series.assert_called_once()
        self.assertEqual(frame[DATE_COL].min(), pd.Timestamp("1957-03-04"))

    @patch("lib.cagr_finance.fred_client.fetch_stooq_close_series")
    @patch("lib.cagr_finance.fred_client.fetch_fred_series")
    def test_sp500_keeps_fred_when_history_is_long_enough(
        self,
        mock_fetch_fred_series,
        mock_fetch_stooq_close_series,
    ) -> None:
        mock_fetch_fred_series.return_value = pd.DataFrame(
            {
                DATE_COL: pd.to_datetime(["1957-03-04", "1957-03-05"]),
                SP500_NOMINAL_COL: [44.06, 44.22],
            }
        )

        frame = fetch_sp500_nominal_series(start_date="1957-03-04", end_date="2020-01-02")

        mock_fetch_stooq_close_series.assert_not_called()
        self.assertEqual(frame[DATE_COL].min(), pd.Timestamp("1957-03-04"))


if __name__ == "__main__":
    unittest.main()
