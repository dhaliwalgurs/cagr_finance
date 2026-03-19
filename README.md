# cagr_finance

Estimate index-linked leveraged ETF behavior (TQQQ and UPRO) beyond their full recorded histories.

## What This Project Does
- Pulls maximum available FRED data for:
  - NASDAQ Composite (`NASDAQCOM`)
  - S&P 500 (`SP500`)
  - CPI (`CPIAUCSL`)
  - via `pandas-datareader`
- Builds synthetic nominal paths for:
  - `TQQQ in nominal terms` from 3x daily NASDAQ changes minus daily MER drag
  - `UPRO in nominal terms` from 3x daily S&P changes minus daily MER drag
- Computes inflation factor from CPI and converts all nominal series to real terms.
- Overwrites a CSV database file with the latest full dataset.

## Output CSV Columns
The generated CSV uses this exact schema:
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

## Run
Install dependencies:
```bash
pip install -r requirements.txt
```

Run once:
```bash
python3 app/update_dataset.py
```

Optional flags:
```bash
python3 app/update_dataset.py --output data/security_estimates.csv --start-value 100 --tqqq-mer 0.0084 --upro-mer 0.0091 --trading-days 252
```

Continuous refresh mode:
```bash
python3 app/update_dataset.py --interval-seconds 3600
```

## Test
```bash
python3 -m unittest discover -s tests
```

or

```bash
pytest tests
```
