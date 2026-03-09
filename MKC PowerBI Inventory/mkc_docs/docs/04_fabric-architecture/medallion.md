# Medallion Layers

## Layer Strategy

| Layer | Fabric Component | Storage Format | Purpose | Key Design Decision |
|-------|-----------------|---------------|---------|---------------------|
| **Bronze** | Lakehouse | Delta Parquet, append-only | Raw replica of all sources, 7-year retention | Never modify Bronze; always re-processable from source |
| **Silver** | Lakehouse | Delta Parquet, MERGE INTO | Cleaned, deduped, typed, schema-enforced | Union MKCGP + MWFGP tables here, not at source |
| **Gold** | Lakehouse + Fabric Warehouse | Delta Parquet + External Tables | Business aggregates, KPIs, open access | External tables = zero-copy; Gold Delta readable via ADLS Gen2 REST by any engine |
| **Semantic Models** | Fabric Workspace Items (`.pbidataset`) | Stored in OneLake workspace folder | Star schema with RLS/OLS for BI | DirectLake mode: reads Delta directly from Gold — no import copy, sub-second refresh |
| **BI Reports** | Power BI Workspaces | In-memory / DirectLake | Self-service dashboards for 12 workspaces | Consumers need no Pro license inside F-SKU capacity |
| **Data Agents** | Fabric AI items | In-memory NL session | Natural-language querying per workspace | Governed by the same Entra RBAC as their parent semantic model |

## Transformation Engine Decisions

| Transition | Tool Chosen | Alternative Considered | Why This Tool |
|-----------|------------|----------------------|--------------|
| **Bronze → Silver** | Fabric Notebooks (PySpark `MERGE INTO`) | Dataflow Gen2 | Dataflow Gen2 lacks `MERGE INTO` (upsert). Hits ~1 GB memory limit on large transactional tables. Notebooks scale via Spark clusters with no memory ceiling |
| **Silver → Gold** | Fabric Notebooks (Spark SQL) | Dataflow Gen2 | Cross-source joins (MKCGP GP tables + AgVantage API data) exceed Dataflow Gen2 single-source scope. Spark SQL supports multi-source joins natively |
| **API / SP → Bronze** | Dataflow Gen2 (Power Query) | Notebooks | Small payloads (<100 MB). MKC already has 34 existing Power Query dataflows. Native scheduling, no cluster spin-up latency |
| **Gold → Semantic Model** | DirectLake (zero-ETL) | Import mode | DirectLake reads Delta files directly from OneLake. No data import copy, sub-second model refresh, no storage duplication |

## Bronze Layer Detail

Bronze is a **write-once, append-only** replica of every source system.

```python
# Bronze ingest pattern — Fabric Notebook
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Read from on-prem SQL via JDBC (through gateway)
df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", f"(SELECT * FROM {table} WHERE rowversion > {last_watermark}) AS t") \
    .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
    .load()

# Append to Bronze Delta table — never overwrite
df.withColumn("_ingested_at", current_timestamp()) \
  .write.format("delta").mode("append") \
  .save(f"abfss://Bronze@onelake.dfs.fabric.microsoft.com/Tables/{table}")
```

!!! warning "Bronze is Sacred"
    Bronze data is never modified after ingestion. If a source correction is needed, it arrives as a new row; Silver MERGE INTO logic handles deduplication and supersession.

## Silver Layer Detail

Silver applies **MERGE INTO** (upsert) semantics to keep exactly one clean record per business key:

```python
# Silver transform pattern — PySpark MERGE INTO
from delta.tables import DeltaTable

silver_table = DeltaTable.forPath(spark, silver_path)
silver_table.alias("target").merge(
    source=bronze_df.alias("source"),
    condition="target.transaction_id = source.transaction_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

Silver also:
- Casts all columns to explicit types (no implicit string coercions)
- Unions `MKCGP` and `MWFGP` tables with a `_source_company` discriminator column
- Runs DQ assertion functions before committing (see [Testing Strategy](../02_devops/testing.md))

## Gold Layer Detail

Gold contains **business aggregates** and **KPI tables** derived from Silver:

```sql
-- Gold aggregation — Spark SQL example
CREATE OR REPLACE TABLE Gold.FactGrainSales
USING DELTA AS
SELECT
    d.date_key,
    l.location_key,
    i.item_key,
    c.customer_key,
    SUM(s.quantity_bushels)   AS total_bushels,
    SUM(s.amount_usd)         AS total_revenue,
    AVG(s.price_per_bushel)   AS avg_price
FROM Silver.GrainSaleTransaction s
JOIN Silver.DimDate d ON s.transaction_date = d.full_date
JOIN Silver.DimLocation l ON s.location_id = l.location_id
JOIN Silver.DimItem i ON s.commodity_code = i.item_code
JOIN Silver.DimCustomer c ON s.customer_id = c.customer_id
GROUP BY d.date_key, l.location_key, i.item_key, c.customer_key;
```

Gold Lakehouse tables are exposed as **External Tables** in Fabric Warehouse, so any JDBC/ODBC client can query them via T-SQL without duplicating data.
