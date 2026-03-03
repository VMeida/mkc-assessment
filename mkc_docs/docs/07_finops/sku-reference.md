# SKU Reference

## F-SKU Pricing Table

Microsoft Fabric runs on **Capacity Units (CU)**. Every analytics workload (Pipelines, Notebooks, Dataflow Gen2, Power BI Premium, Warehouses, Lakehouses, Eventstream, Semantic Models) consumes CU from a single shared pool. You pay for the pool — not per workload or per user.

| SKU | CU | Power BI Premium Equiv. | PAYG/month | 1-yr Reserved/month | Free OneLake Storage |
|-----|----|--------------------------|------------|---------------------|----------------------|
| F2 | 2 | — | ~$262 | ~$197 | 1 TB |
| F4 | 4 | — | ~$524 | ~$393 | 1 TB |
| **F8** | **8** | P1 (≈) | **~$1,048** | **~$786** | **2 TB** |
| F16 | 16 | P2 (≈) | ~$2,097 | ~$1,573 | 4 TB |
| **F32** | **32** | P3 (≈) | **~$4,194** | **~$3,146** | **8 TB** |
| **F64** | **64** | P4 (≈) | **~$8,388** | **~$6,292** | **16 TB** |
| F128 | 128 | P5 (≈) | ~$16,776 | ~$12,582 | 32 TB |
| F256 | 256 | — | ~$33,552 | ~$25,164 | 64 TB |

**Bold rows** = relevant to MKC scenarios.

!!! info "Key Notes"
    - **F64+ enables Fabric Copilot** (NL → DAX/SQL) and advanced AI/ML workloads
    - Capacities can be **paused** (dev/test environments) to stop billing; resuming takes ~1 minute
    - **Power BI Pro licenses are NOT required** for report consumers on an F-SKU capacity
    - 1-yr reservations save ~25% vs. PAYG — commit after 3-month PAYG pilot

## What Is Included in Capacity

| Included | Not Included (billed separately) |
|----------|----------------------------------|
| Fabric Pipelines (ADF-equivalent) | OneLake storage beyond free tier |
| Fabric Notebooks (PySpark / SparkSQL) | Azure SQL Managed Instance |
| Dataflow Gen2 (Power Query) | Azure Monitor / Log Analytics ingestion |
| OneLake Lakehouses | Key Vault operations (minimal) |
| Fabric Warehouse (T-SQL endpoint) | Outbound data egress from Azure region |
| Eventstream (real-time streaming) | External compute (Azure Functions for model serving) |
| Semantic Models (DirectLake) | On-Premises Data Gateway software (**free**) |
| Power BI Premium reporting | Azure OpenAI tokens (separate variable cost) |
| MLflow experiment tracking | |
| Fabric Copilot (**F64+ only**) | |
| Git integration | |

## OneLake Storage Pricing

Storage beyond the free tier is billed at ADLS Gen2 rates:

| Tier | Price/GB/month | When to Use |
|------|---------------|-------------|
| Standard LRS | $0.023 | Default — all active Delta tables |
| Geo-redundant (RA-GRS) | $0.0414 | BCDR requirement |
| Cold tier | $0.00099 | Bronze data > 5 years old |

**MKC storage estimate:**

| Layer | Estimated Size | Notes |
|-------|---------------|-------|
| Bronze (7-yr retention) | ~500 GB–2 TB | Delta Parquet with 40–60% compression vs raw |
| Silver | ~200–700 GB | Deduped, typed |
| Gold | ~50–200 GB | Aggregated KPIs |
| Feature Store | ~20–50 GB | ML feature vectors |
| **Total** | **~800 GB–3 TB** | **Within F32 free tier (8 TB)** |

**Likely MKC storage cost: $0/month** (well within 8 TB free tier on F32).

## Power BI Licensing

| License | Price/user/month | Notes |
|---------|-----------------|-------|
| Power BI Free | $0 | View only, no workspace sharing |
| Power BI Pro | ~$10 | Required for content creators publishing outside F-SKU capacity |
| Power BI PPU | ~$20 | Per-user Premium; not needed with F-SKU |
| F-SKU consumers | Included | All workspace viewers get Premium access free |

**MKC estimate:** ~10–15 content creators × $10 = **$100–150/month** for Pro licenses only. All other users are license-free within the F-SKU capacity.

## On-Premises Data Gateway

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| Existing on-prem server | $0 | Install gateway software on Windows Server in same subnet as SQL |
| Azure D2s_v3 VM | ~$154 | Light loads, <5 concurrent pipelines |
| Azure D4s_v3 VM | ~$308 | Recommended if on-prem hardware decommissioned, 7+ source DBs |
| Azure D8s_v3 VM | ~$616 | Heavy parallel ingestion (20+ tables simultaneous) |

> Apply **Azure Hybrid Benefit** if MKC has Windows Server Software Assurance licenses — reduces VM cost by ~40%.
