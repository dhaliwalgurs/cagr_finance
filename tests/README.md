# tests

Unit tests currently validate deterministic math only.

- `test_leveraged.py`: leveraged compounding and MER drag behavior
- `test_transform.py`: CPI alignment and inflation conversion behavior

Run:
```bash
python3 -m unittest discover -s tests
```
