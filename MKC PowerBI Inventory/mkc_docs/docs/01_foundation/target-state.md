# Target State

## Architecture Vision

The target platform consolidates all MKC data sources into a **Microsoft Fabric** capacity with **OneLake** as the single storage layer. Every byte of data is stored as **Delta Parquet** — an open, Linux Foundation-governed format readable by any analytical engine without a Fabric license.

![MKC Target Architecture](../assets/mkc_fabric_architecture_v1.png)

> Full legend: [mkc_fabric_legend.png](../assets/mkc_fabric_legend.png)

## Platform Layers

| Layer | Fabric Component | Format | Purpose |
|-------|-----------------|--------|---------|
| **Bronze** | Lakehouse | Delta Parquet, append-only | Raw replica of all sources, 7-year retention |
| **Silver** | Lakehouse | Delta Parquet + MERGE INTO | Cleaned, deduped, schema-enforced, conformed |
| **Gold** | Lakehouse + Fabric Warehouse | Delta Parquet + External Tables | Business aggregates, KPIs, open access via T-SQL |
| **Semantic Models** | Fabric Workspace Items | `.pbidataset` on OneLake | Governed star schema — RLS/OLS — DirectLake mode |
| **BI Reports** | Power BI Workspaces | In-memory / DirectLake | Self-service dashboards, 12 workspaces, 40 reports |
| **Data Agents** | Fabric AI items | NL session | Natural-language querying per workspace group |

## Design Principles

### 1. Never Modify Bronze
Bronze is an append-only raw replica. If source data is corrected, a new version is appended. Bronze data is always re-processable from source — it never becomes the authoritative record, just the audit trail.

### 2. Single Conforming Layer
Silver is the only place where MKCGP and MWFGP tables are unioned. This prevents diverging definitions of shared entities (customers, locations, items) from proliferating into downstream layers.

### 3. Open Format, Zero Lock-in
All data lives as Delta Parquet on ADLS Gen2. If MKC ever moves away from Microsoft Fabric, the data is immediately accessible by Databricks, Apache Spark, DuckDB, Trino, Azure Synapse, or any S3/ADLS-compatible engine.

### 4. DirectLake — No Import Copies
Semantic models use DirectLake mode: they read Delta files directly from OneLake without creating an imported copy. This means reports are always current (no scheduled refresh needed) and storage is never duplicated.

### 5. Governed Identity
All access — from ETL pipelines to end-user reports to AI agents — is governed by Microsoft Entra ID. Row-Level Security (RLS) and Object-Level Security (OLS) are enforced at the semantic model layer using Entra group membership.

## Capability Comparison

| Capability | Current | Target |
|-----------|---------|--------|
| Raw data preservation | None | Bronze Lakehouse (7-year retention) |
| Data quality enforcement | None | Silver-layer schema checks + MERGE INTO |
| Unified business metrics | Per-report definitions | Gold Lakehouse + shared Semantic Models |
| Report refresh | Scheduled import (30–60 min) | DirectLake (sub-second, always current) |
| Row-level security | None | DAX RLS per Entra group |
| Column-level security | None | OLS per Entra role |
| Natural language queries | None | Fabric Data Agents (GPT-4o) |
| Data lineage | None | Microsoft Purview automatic lineage |
| Vendor independence | High lock-in | Delta Parquet + ADLS Gen2 |
