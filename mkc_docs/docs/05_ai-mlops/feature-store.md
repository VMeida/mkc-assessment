# Feature Store

## What is the Feature Store?

The MKC Feature Store is a collection of **Delta tables in the Gold Lakehouse** that contain pre-computed, ML-ready feature vectors. Storing features in Delta format means:

- Features are **versioned** (time travel for reproducible training)
- Features are **portable** (readable by any Delta-compatible engine, not just Fabric)
- Features **share computation** — one feature pipeline feeds multiple models
- Features are **governed** by the same Purview policies as Gold business data

## Feature Store Layout

```
MKC-Gold-Prod.Lakehouse/
└── Tables/
    ├── features_grain_price/      ← Grain price rolling statistics
    ├── features_producer_activity/← Producer engagement signals
    ├── features_inventory_pattern/← Inventory movement patterns
    └── features_gl_anomaly/       ← GL transaction anomaly signals
```

## Feature Table Catalogue

### `features_grain_price`

| Feature | Type | Description | Updated |
|---------|------|-------------|---------|
| `date_key` | int | Surrogate date key | Daily |
| `item_key` | int | Commodity surrogate key | Daily |
| `location_key` | int | Location surrogate key | Daily |
| `price_7d_avg` | float | 7-day rolling average price/bushel | Daily |
| `price_30d_avg` | float | 30-day rolling average price/bushel | Daily |
| `price_momentum` | float | Current price / 7d avg (> 1 = above trend) | Daily |
| `price_volatility_30d` | float | Std dev of price over 30 days | Daily |
| `volume_7d_avg` | float | 7-day rolling average sales volume (bushels) | Daily |
| `season_index` | float | Seasonal factor (0–1, based on fiscal calendar) | Daily |

### `features_producer_activity`

| Feature | Type | Description | Updated |
|---------|------|-------------|---------|
| `producer_key` | int | Producer surrogate key | Daily |
| `days_since_last_contract` | int | Days since last grain contract | Daily |
| `contracts_ytd` | int | Number of contracts year-to-date | Daily |
| `acres_enrolled_ratio` | float | Enrolled acres / total farm acres | Daily |
| `agworld_logins_30d` | int | AgWorld portal logins in last 30 days | Daily |
| `avg_application_score` | float | Weighted agronomy service score | Weekly |
| `churn_risk_score` | float | ML model output (0–1, 1 = high risk) | Weekly |

## Reading Features in Training Notebooks

```python
from pyspark.sql import functions as F

# Load grain price features
price_features = spark.read.format("delta") \
    .load("abfss://MKC-Gold-Prod@onelake.dfs.fabric.microsoft.com/Tables/features_grain_price")

# Load producer activity features
producer_features = spark.read.format("delta") \
    .load("abfss://MKC-Gold-Prod@onelake.dfs.fabric.microsoft.com/Tables/features_producer_activity")

# Join for combined training set
training_df = price_features.join(producer_features, on=["date_key", "location_key"], how="left")

print(f"Training set: {training_df.count():,} rows, {len(training_df.columns)} features")
```

## Point-in-Time Correctness

For backtesting and reproducible training, features are accessed using Delta time travel to avoid data leakage:

```python
# Load features as they were on the training cutoff date
training_cutoff = "2024-06-30"
price_features_historical = spark.read.format("delta") \
    .option("timestampAsOf", training_cutoff) \
    .load(feature_store_price_path)
```

## Feature Freshness SLAs

| Feature Table | Maximum Staleness | Alert If Exceeded |
|---------------|------------------|-------------------|
| `features_grain_price` | 26 hours | Yes — Azure Monitor alert |
| `features_producer_activity` | 26 hours | Yes |
| `features_inventory_pattern` | 26 hours | Yes |
| `features_gl_anomaly` | 3 days | Yes — weekly batch |

---

## References

| Resource | Description |
|----------|-------------|
| [Delta Lake time travel](https://learn.microsoft.com/en-us/azure/databricks/delta/history) | Querying historical snapshots with VERSION AS OF and TIMESTAMP AS OF |
| [Fabric Lakehouse overview](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview) | Delta table storage, SQL analytics endpoint, and governance in OneLake |
| [PySpark window functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/window.html) | Rolling aggregations, lag, lead, and partition-based feature computation |
| [OneLake access patterns](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api) | abfss:// path conventions and authentication for reading OneLake Delta tables |
| [Azure Monitor alerts](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-overview) | Configuring metric and log-based alerts for feature freshness SLA monitoring |
