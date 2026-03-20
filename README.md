# cagr_finance

Estimate CAGR and start/end values for index-linked leveraged securities across arbitrary date ranges.

## Focus
- Clean, modular Python code with reusable functions.
- FRED- and Stooq-backed source data.
- Hybrid leveraged paths for `TQQQ`, `UPRO`, and `QLD`:
  - synthetic before ETF inception
  - actual ETF close history from inception onward
- Date-window analysis for:
  - `TQQQ`
  - `UPRO`
  - `QLD`
  - `NASDAQ`
  - `SP500`

## Data + Modeling Notes
- FRED series IDs:
  - `NASDAQCOM`
  - `NASDAQ100`
  - `SP500`
  - `CPIAUCSL`
- Source behavior:
  - NASDAQ Composite, NASDAQ-100, and CPI are fetched from FRED.
  - S&P uses FRED when full history is available, with automatic Stooq fallback for pre-2016 history (FRED daily licensing currently limits SP500 to ~10 years).
  - TQQQ, UPRO, and QLD actual close history is fetched from Stooq and scaled to the modeled path at first overlap.
- Enforced historical floors:
  - `SP500` and `UPRO` modeled from `1957-03-04`
  - `NASDAQ` modeled from `1971-02-05`
  - `TQQQ` and `QLD` synthetic history is limited by NASDAQ-100 availability
- Leveraged formula (daily):
  - `leveraged_return = leverage * index_daily_return - (annual_mer / trading_days_per_year)`
- Analysis windows anchor the start of a request to the last available market close on or before the requested start date.
- Constants (not CLI flags):
  - `TRADING_DAYS_PER_YEAR = 252`
  - `TQQQ_MER_ANNUAL = 0.0084`
  - `UPRO_MER_ANNUAL = 0.0091`
  - `QLD_MER_ANNUAL = 0.0095`

## Output CSV Columns
`data/security_estimates.csv` contains:
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

## Install
```bash
pip install -r requirements.txt
```

## Refresh CSV Database
Run once:
```bash
python3 app/update_dataset.py
```

Continuous mode:
```bash
python3 app/update_dataset.py --interval-seconds 3600
```

## Analyze CAGR (Main Purpose)
Single security:
```bash
python3 app/analyze_cagr.py --security TQQQ --start-date 2012-01-01 --end-date 2020-12-31 --starting-nominal-value 100
```

Multiple securities:
```bash
python3 app/analyze_cagr.py --security TQQQ,UPRO,QLD,NASDAQ,SP500 --start-date 2015-01-01 --end-date 2025-01-01 --starting-nominal-value 100
```

All supported securities:
```bash
python3 app/analyze_cagr.py --security ALL --start-date 2005-01-01 --end-date 2025-01-01 --starting-nominal-value 100
```

CLI output includes:
- start nominal value
- end nominal value
- start real value
- end real value
- nominal simple return
- real simple return
- nominal CAGR
- real CAGR

Example formatting:
```text
Nominal: $100.00 -> $492.13
Real: $100.00 -> $494.28
Nominal Return: 392.13%
Real Return: 394.28%
Nominal CAGR: 22.40%
Real CAGR: 22.48%
```

## Function API Example
```python
from lib.cagr_finance.analysis import analyze_securities_period_and_print

results = analyze_securities_period_and_print(
    start_date="2015-01-01",
    end_date="2025-01-01",
    securities=["TQQQ", "UPRO", "QLD", "NASDAQ", "SP500"],
    starting_nominal_value=100.0,
)

# `results` is a list of SecurityAnalysisResult objects for downstream use.
```

## Test
```bash
python3 -m unittest discover -s tests
```

or

```bash
pytest tests
```
