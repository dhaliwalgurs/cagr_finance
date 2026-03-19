# lib

Library modules for data ingestion, transformations, and dataset generation.

- `cagr_finance/config.py`: constants and runtime settings
- `cagr_finance/fred_client.py`: FRED pull logic via `pandas-datareader`
- `cagr_finance/leveraged.py`: synthetic leveraged return math
- `cagr_finance/transform.py`: inflation alignment and real-term conversion
- `cagr_finance/pipeline.py`: end-to-end orchestration and CSV write
