# app

CLI entrypoints for running data refresh workflows.

- `update_dataset.py`: Pulls FRED data, computes synthetic TQQQ/UPRO, inflation-adjusts values, and writes CSV output.
  - Supports one-shot mode and continuous mode via `--interval-seconds`.
