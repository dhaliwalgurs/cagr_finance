# Agent Context

Last updated: 2026-03-19

## Project Goal
Build a readable, modular Python application that estimates CAGR-related synthetic series for leveraged ETFs (TQQQ and UPRO), including inflation-adjusted values, with data sourced from FRED.

## Current Architecture
- `lib/cagr_finance/config.py`
  - Central constants: FRED series IDs, CSV schema column names, and runtime settings (`AppSettings`).
- `lib/cagr_finance/fred_client.py`
  - Pulls raw series from FRED via `pandas-datareader`.
- `lib/cagr_finance/leveraged.py`
  - Computes synthetic leveraged ETF paths from daily index returns and MER drag.
- `lib/cagr_finance/transform.py`
  - CPI alignment to target dates and nominal-to-real conversion helpers.
- `lib/cagr_finance/pipeline.py`
  - End-to-end orchestration: fetch, calculate, inflation-adjust, merge, and write output.
- `app/update_dataset.py`
  - CLI for refreshing dataset CSV (one-shot and interval mode).

## Output Schema (CSV)
- `date`
- `NASDAQ nominal value`
- `S&P nominal value`
- `inflation factor`
- `NASDAQ value in real terms`
- `S&P value in real terms`
- `TQQQ in nominal terms`
- `UPRO in nominal terms`
- `TQQQ in real terms`
- `UPRO in real terms`

## Assumptions In Place
- FRED series:
  - NASDAQ: `NASDAQCOM`
  - S&P 500: `SP500`
  - CPI: `CPIAUCSL`
- Synthetic leverage calculation:
  - TQQQ uses `3x` NASDAQ daily return.
  - UPRO uses `3x` S&P daily return.
- MER treatment:
  - Daily drag = `annual_mer / trading_days_per_year`.
  - Applied in return formula as subtraction from leveraged daily return.
- Inflation factor:
  - `latest_cpi / cpi_on_date`.
  - Monthly CPI aligned to target dates using the latest available CPI observation at or before each date.

## Readability/Modularity Standards
- Keep business logic small and single-purpose per module.
- Keep constants centralized in `config.py`.
- Avoid hidden side effects inside utility functions.
- Use type hints and concise docstrings for non-trivial functions.
- Prefer deterministic unit tests for math-heavy logic.

## Dependency Notes
- Runtime:
  - `pandas`
  - `pandas-datareader` (primary FRED integration)
  - `requests` (session support and network stack)
- Testing:
  - `pytest` (optional alongside built-in `unittest`)

## Next Planned Additions
- Backtesting tests comparing synthetic TQQQ/UPRO values against real ETF history over overlapping date ranges.
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
