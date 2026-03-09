# Testing Strategy

## Test Pyramid

```
                  ┌─────────────────┐
                  │  E2E (Report)   │  ← Manual UAT + Power BI visual tests
                  └────────┬────────┘
               ┌───────────┴────────────┐
               │  Integration (DQ)      │  ← Row counts, referential integrity, freshness
               └───────────┬────────────┘
          ┌─────────────────┴─────────────────┐
          │     Unit (Notebook functions)      │  ← pytest on transformation functions
          └────────────────────────────────────┘
```

## Unit Test Roadmap

Fabric Notebooks are not natively testable with vanilla pytest inside a Spark cluster. The recommended approach extracts logic progressively to enable local testing.

### Phase 1 — Now (low friction)

Extract all transformation logic into a `src/` pure-Python package (no Spark imports). This allows full local and CI testing with no Fabric connection:

- **Structure:** `src/transforms/` contains pure functions; notebooks import from `src/`
- **Tools:** `pytest`, `pytest-cov`, `ruff` (already in CI), `pandas` mocks
- **Coverage gate:** CI fails if `src/` coverage drops below 80% (`pytest --cov=src --cov-fail-under=80`)
- **Target:** 80% coverage on all `src/transforms/` functions

### Phase 2 — Medium term

Test DataFrame transforms and notebooks without a live Spark cluster:

- **`pytest-spark`** or a local **DuckDB** fixture for DataFrame-level transform tests
- **`nbmake`** — runs notebooks as tests end-to-end without Spark
- **`papermill`** — parameterized notebook execution for environment-based testing
- **Gate:** same 80% threshold enforced in CI; extend coverage to DataFrame-level tests

### Phase 3 — Future

- **Microsoft Fabric native test execution** for Notebooks (currently on roadmap; evaluate when GA)
- **Fabric Data Factory unit testing** once generally available
- **Great Expectations** or **Soda Core** at the DQ layer for declarative data contracts

---

## 1. Unit Tests — Notebook Functions

PySpark transformation functions are extracted into testable Python modules and tested with **pytest**:

```python
# tests/test_transforms.py
import pytest
from transforms.silver import clean_grain_sale

def test_clean_grain_sale_removes_negative_qty():
    row = {"quantity": -5, "price": 10.0, "location": "Moundridge"}
    result = clean_grain_sale(row)
    assert result is None  # negative qty should be filtered out

def test_clean_grain_sale_normalises_location():
    row = {"quantity": 100, "price": 8.5, "location": "moundridge "}
    result = clean_grain_sale(row)
    assert result["location"] == "Moundridge"
```

Run with: `pytest tests/ -v --tb=short`

## 2. Data Quality Checks — Silver Ingest

After each Bronze → Silver MERGE INTO, the notebook runs a DQ check block:

```python
from pyspark.sql import functions as F

def assert_dq(df, table_name: str):
    checks = {}
    # Row count
    checks["row_count"] = df.count()
    # Null checks on key columns
    for col in ["transaction_id", "date_key", "location_key"]:
        null_pct = df.filter(F.col(col).isNull()).count() / checks["row_count"]
        checks[f"null_{col}_pct"] = null_pct
        assert null_pct < 0.01, f"{table_name}: {col} has {null_pct:.1%} nulls — exceeds 1% threshold"
    # Date range sanity
    min_date = df.agg(F.min("transaction_date")).collect()[0][0]
    assert min_date >= "2018-01-01", f"{table_name}: min date {min_date} is before 2018"
    print(f"[DQ PASS] {table_name}: {checks}")
```

## 3. Integration Tests — Pipeline Smoke Tests

After each pipeline run, a lightweight smoke test verifies that data flowed end-to-end:

```python
# scripts/dq_check.py
import pyodbc, os

conn = pyodbc.connect(os.environ["SQL_CONNECTION_STRING"])
cursor = conn.cursor()

checks = [
    ("Bronze row count > 0",
     "SELECT COUNT(*) FROM Bronze.FactGrainSales WHERE load_date = CAST(GETDATE() AS DATE)"),
    ("Silver freshness < 2 hours",
     "SELECT DATEDIFF(HOUR, MAX(updated_at), GETUTCDATE()) FROM Silver.FactGrainSales"),
    ("Gold KPI not null",
     "SELECT COUNT(*) FROM Gold.FactGrainSales WHERE grain_bushels IS NULL"),
]

failures = []
for name, sql in checks:
    val = cursor.execute(sql).fetchone()[0]
    if val == 0 or val > 2:
        failures.append(f"FAIL: {name} returned {val}")
    else:
        print(f"PASS: {name}")

if failures:
    raise SystemExit("\n".join(failures))
```

## 4. Semantic Model Tests

After Gold → Semantic Model refresh, DAX queries verify key measures:

```dax
-- Test: Total grain bushels matches sum of FactGrainSales
EVALUATE
ROW(
    "TotalBushels", [Total Grain Bushels],
    "Expected", CALCULATE(SUM(FactGrainSales[quantity_bushels]))
)
```

Tests are run via the **Tabular Editor** command-line or the Fabric REST API (`POST /datasets/{id}/executeQueries`).

## 5. Test Coverage Targets

| Layer | Test Type | Coverage Target |
|-------|-----------|----------------|
| Silver transforms | Unit (pytest) | 80% of transformation functions |
| Bronze → Silver | DQ checks | 100% of key columns, all tables |
| Pipeline end-to-end | Smoke test | All 7 source pipelines |
| Semantic Models | DAX measure tests | All KPI measures |
| BI Reports | UAT (manual) | Core reports per workspace |
