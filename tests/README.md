# tests

Unit tests validate deterministic math and analysis behavior.

- `test_leveraged.py`: leveraged compounding and MER drag behavior
- `test_transform.py`: CPI alignment and inflation conversion behavior
- `test_analysis.py`: security selection and date-window CAGR output behavior
- `test_fred_client.py`: enforced historical start-date floors by series

Run:
```bash
python3 -m unittest discover -s tests
```

or

```bash
pytest tests
```
