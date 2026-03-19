# Agent Context

Last updated: 2026-03-19

## Project Goal
Build a readable, modular Python application that estimates CAGR-related synthetic series for leveraged ETFs and indexes, including inflation-adjusted values, with data sourced from FRED.

## Current Architecture
- `lib/__init__.py`
  - Package marker so repository-level imports are cleaner.
- `lib/cagr_finance/config.py`
  - Central constants: FRED IDs, fixed MER/trading-day constants, security mappings, and output schema.
- `lib/cagr_finance/fred_client.py`
  - Pulls raw series via `pandas-datareader`; S&P has Stooq fallback for pre-2016 history due FRED licensing limits.
- `lib/cagr_finance/leveraged.py`
  - Computes synthetic leveraged ETF paths from daily index returns and MER drag.
- `lib/cagr_finance/transform.py`
  - CPI alignment to target dates and nominal-to-real conversion helpers.
- `lib/cagr_finance/pipeline.py`
  - End-to-end orchestration: fetch, calculate, inflation-adjust, merge, and write output CSV.
- `lib/cagr_finance/analysis.py`
  - Date-window analysis API for start/end nominal, start/end real, and CAGR values.
- `app/update_dataset.py`
  - CLI for refreshing dataset CSV (one-shot and interval mode).
- `app/analyze_cagr.py`
  - Main analysis CLI for CAGR-focused workflows.

## Output Schema (CSV)
- `date`
- `NASDAQ nominal value`
- `S&P nominal value`
- `inflation factor`
- `NASDAQ value in real terms`
- `S&P value in real terms`
- `TQQQ in nominal terms`
- `UPRO in nominal terms`
- `QLD in nominal terms`
- `TQQQ in real terms`
- `UPRO in real terms`
- `QLD in real terms`

## Fixed Constants
- `TRADING_DAYS_PER_YEAR = 252`
- `TQQQ_MER_ANNUAL = 0.0084`
- `UPRO_MER_ANNUAL = 0.0091`
- `QLD_MER_ANNUAL = 0.0095`
- `SP500_MIN_DATE = 1957-03-04`
- `NASDAQ_MIN_DATE = 1971-02-05`

These are intentionally constants, not CLI flags.

## Supported Analysis Securities
- `TQQQ`
- `UPRO`
- `QLD`
- `NASDAQ`
- `SP500` (aliases accepted: `S&P`, `S&P500`)

## Analysis API Outputs
`analysis.py` returns structured results (`SecurityAnalysisResult`) containing:
- requested + actual start/end dates
- start/end nominal values
- start/end real values
- nominal CAGR
- real CAGR

A print helper outputs the same values to command line while still returning results for reuse.

## Readability/Modularity Standards
- Keep business logic small and single-purpose per module.
- Keep constants centralized in `config.py`.
- Avoid hidden side effects inside utility functions.
- Use type hints and concise docstrings for non-trivial functions.
- Prefer deterministic unit tests for math-heavy logic.

## Next Planned Additions
- Backtesting tests comparing synthetic TQQQ/UPRO/QLD values against real ETF history over overlapping date ranges.
- Additional drag/adjustment factors beyond MER.
- Optional incremental update mode (append/update) if needed; current mode recomputes full CSV each run.

## Change Log
- 2026-03-19:
  - Created first full Python implementation for FRED ingestion + synthetic ETF calculation.
  - Added inflation adjustment and output CSV refresh pipeline.
  - Added initial unit tests for leveraged math and inflation transforms.
  - Documented run/test commands and module layout.
  - Fixed FRED CSV parser to support `observation_date` header format.
  - Verified CSV refresh end-to-end and generated `data/security_estimates.csv` (13,896 rows through 2026-03-18).
  - Added continuous refresh option with `--interval-seconds` for always-updating CSV behavior.
  - Installed and adopted `pandas-datareader` for FRED pulls.
  - Installed `pytest` and added it to project dependencies.
  - Added QLD synthetic series support (2x NASDAQ with fixed MER).
  - Added CAGR analysis API + CLI with start/end dates, security selection, and starting nominal value.
  - Locked MER and trading-day assumptions as constants (not CLI flags).
  - Added repository/package `__init__.py` markers to support cleaner imports.
  - Enforced historical floor dates: S&P/UPRO from 1957-03-04 and NASDAQ/TQQQ/QLD from 1971-02-05.
  - Added automatic S&P data-source fallback to Stooq when FRED history is truncated to ~10 years.
  - Rebased analysis real-value outputs so nominal and real start at the same value.
  - Updated CLI analysis formatting to currency (`$`) with 2 decimals and CAGR with 2 decimals.
  - Added nominal/real simple rate of return outputs for the selected date window.
