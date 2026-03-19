# lib

Library modules for data ingestion, transformations, dataset generation, and CAGR analysis.

- `__init__.py`: package marker for cleaner imports
- `cagr_finance/config.py`: constants, security specs, and settings
- `cagr_finance/fred_client.py`: FRED pull logic via `pandas-datareader`
- `cagr_finance/leveraged.py`: synthetic leveraged return math
- `cagr_finance/transform.py`: inflation alignment and real-term conversion
- `cagr_finance/pipeline.py`: end-to-end dataset build and CSV write
- `cagr_finance/analysis.py`: date-window start/end value and CAGR analysis APIs
