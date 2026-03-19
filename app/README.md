# app

CLI entrypoints.

- `update_dataset.py`
  - Refreshes `data/security_estimates.csv` from FRED.
  - Supports one-shot and interval modes via `--interval-seconds`.
- `analyze_cagr.py`
  - Main analysis CLI.
  - Accepts `--start-date`, `--end-date`, `--security`, and `--starting-nominal-value`.
  - Prints start/end nominal + real values and CAGR outputs.
