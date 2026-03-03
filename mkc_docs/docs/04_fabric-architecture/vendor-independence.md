# Vendor Independence Strategy

MKC's platform is designed so that **no proprietary vendor format or API creates an irreversible dependency**. Every architectural choice has an explicit mitigation for the lock-in scenario.

## Lock-in Risk Matrix

| Risk Area | Lock-in Scenario | Mitigation | Portability Score |
|-----------|-----------------|------------|:-----------------:|
| **Storage** | Fabric-proprietary format makes data inaccessible without a Fabric license | All data stored as **Delta Parquet** on ADLS Gen2 (OneLake). Readable by Databricks, DuckDB, Apache Spark, Trino, Azure Synapse — no Fabric license needed | ⭐⭐⭐⭐⭐ |
| **Warehousing** | T-SQL queries only work inside Fabric Warehouse | Gold Lakehouse data exposed as Fabric Warehouse **external tables** (no data copy). The underlying Delta files remain independently accessible | ⭐⭐⭐⭐⭐ |
| **BI** | Power BI is the only consumer of semantic models | Gold Warehouse T-SQL views can be queried by Tableau, Looker, Excel, or any JDBC/ODBC client | ⭐⭐⭐⭐ |
| **Ingestion** | Fabric Pipelines use proprietary connectors | Standard connector ecosystem (JDBC, REST, OData). Equivalent pipelines exist in Azure Data Factory, dbt, Airbyte, Apache Airflow | ⭐⭐⭐⭐ |
| **LLM** | Azure OpenAI API is the only LLM endpoint | Azure OpenAI API is OpenAI-compatible (`/v1/chat/completions`). Switch to other GPT-compatible endpoints (Azure AI Foundry, open-source via Ollama) with one config change | ⭐⭐⭐⭐ |
| **Feature Store** | ML features in a proprietary store | Features stored as Delta tables in OneLake (Gold layer). Portable to any Delta-compatible ML platform | ⭐⭐⭐⭐⭐ |
| **Semantic Models** | `.pbidataset` items are Fabric-native | DirectLake reads standard Delta Parquet files. If Fabric is replaced, the underlying Gold Delta data is fully available to any analytical engine | ⭐⭐⭐ |

## Exit Scenarios

### Scenario A: Migrate off Fabric to Databricks

Steps:
1. Mount existing OneLake ADLS Gen2 paths in Databricks Unity Catalog — **no data copy needed**
2. Recreate Silver → Gold notebooks in Databricks notebooks (PySpark code is identical)
3. Point BI tools at Databricks SQL Warehouse instead of Fabric Warehouse
4. Re-implement RLS in Databricks Unity Catalog column masking policies

**Estimated migration effort:** 4–6 weeks for platform; reports re-pointed with connection string change only.

### Scenario B: Migrate LLM from Azure OpenAI to Ollama (on-premises)

Steps:
1. Change APIM backend URL from Azure OpenAI Private Endpoint to Ollama endpoint
2. Update model name in Data Agent configuration (`gpt-4o` → `llama3.1`)
3. No changes to Fabric Data Agent logic or semantic model connections

**Estimated migration effort:** 1–2 days.

### Scenario C: Add Tableau as a second BI tool

Steps:
1. Provision a Tableau Server or Tableau Cloud connection
2. Point Tableau at the Fabric Warehouse SQL connection string (TDS/ODBC)
3. Gold External Tables are immediately queryable — no data movement

**Estimated effort:** Hours (connection configuration only).

## Open Standards Used

| Standard | Used For | Governing Body |
|----------|---------|---------------|
| **Delta Lake** | Storage format for all layers | Linux Foundation |
| **Apache Parquet** | Column-oriented file format | Apache Software Foundation |
| **OpenAI API spec** (`/v1/chat/completions`) | LLM inference | OpenAI (de facto standard) |
| **JDBC / ODBC** | SQL access to Gold Warehouse | Open standards |
| **OData v4** | CRM and API ingestion | OASIS |
| **OAuth2** | SaaS API authentication | IETF |
