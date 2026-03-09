# MKC Microsoft Fabric Architecture — Cost Guide

> **Reference date:** February 2026
> **Region:** East US (most common baseline; West Europe ~5–8 % higher)
> All prices are estimates based on Microsoft public pricing. Actual costs depend on data volumes, user counts, and negotiated Enterprise Agreements (EA).

---

## 1. Microsoft Fabric Capacity (F-SKUs)

Fabric runs on **Capacity Units (CU)**. Every analytics workload (Pipelines, Notebooks, Dataflow Gen2, Power BI Premium, Warehouses, Lakehouse) consumes CU from a single capacity pool — you pay for the pool, not per workload.

### 1.1 SKU Reference Table

| SKU   | CU  | Power BI Premium equivalent | PAYG / month | 1-yr Reserved / month | Free OneLake Storage |
|-------|-----|-----------------------------|--------------|-----------------------|----------------------|
| F2    | 2   | —                           | ~$262        | ~$197                 | 1 TB                 |
| F4    | 4   | —                           | ~$524        | ~$393                 | 1 TB                 |
| F8    | 8   | P1 (≈)                      | ~$1,048      | ~$786                 | 2 TB                 |
| F16   | 16  | P2 (≈)                      | ~$2,097      | ~$1,573               | 4 TB                 |
| F32   | 32  | P3 (≈)                      | ~$4,194      | ~$3,146               | 8 TB                 |
| F64   | 64  | P4 (≈)                      | ~$8,388      | ~$6,292               | 16 TB                |
| F128  | 128 | P5 (≈)                      | ~$16,776     | ~$12,582              | 32 TB                |
| F256  | 256 | —                           | ~$33,552     | ~$25,164              | 64 TB                |

> **Notes:**
> - F64+ enables **Fabric Copilot** (NL → DAX/SQL) and advanced AI/ML features.
> - F-SKU capacities can be **paused** (dev/test) to stop billing; resuming takes ~1 min.
> - Power BI Pro licenses (~$10/user/month) are **NOT required** for Power BI workspaces inside an F-SKU capacity — workspace access is license-free for consumers.
>   Exception: Users who publish reports or create content in workspaces **outside** this capacity still need Pro or PPU.
> - 1-yr reservations require upfront or monthly commitment and save ~25 %.

### 1.2 What Is Included in Capacity

| Included | Not Included |
|----------|-------------|
| All Fabric workloads (Pipelines, Notebooks, Dataflow Gen2, Lakehouses, Warehouses, Eventstream, Semantic Models, Power BI Premium) | OneLake storage **beyond** the free tier |
| Concurrent query execution (governed by CU smoothing — 10× burst over 10-min window) | Azure SQL Managed Instance (separate Azure resource) |
| OneLake free storage (scales with SKU — see table) | Azure Monitor / Log Analytics ingestion & retention |
| Fabric Copilot (F64+) | Key Vault operations (minimal cost) |
| MLflow experiment tracking, Fabric Notebooks | Outbound data egress from Azure region |
| Git integration & CICD support | External compute (e.g. Azure Functions for model serving) |

---

## 2. OneLake Storage

OneLake is ADLS Gen2 under the hood. You pay for storage beyond the free tier.

| Tier | Price / GB / month |
|------|--------------------|
| Standard LRS (default) | $0.023 |
| Geo-redundant (BCDR, RA-GRS) | $0.0414 |
| Cold tier (archival) | $0.00099 |

### MKC Estimated Storage

| Layer | Estimated Size | Notes |
|-------|---------------|-------|
| Bronze (raw + 7-yr retention) | ~500 GB–2 TB | GP transactions history, grain/feed, payroll; Delta with Parquet compression ~40–60% reduction vs original |
| Silver (cleaned Delta) | ~200–700 GB | Deduped, typed; smaller than Bronze |
| Gold (aggregates) | ~50–200 GB | Pre-aggregated KPIs; smallest layer |
| Feature Store | ~20–50 GB | Agronomic + CRM features for ML |
| **Total estimated** | **~800 GB – 3 TB** | Well within F32 free tier (8 TB) |

**Likely cost for MKC:** $0/month for storage (within F32 8 TB free tier).

---

## 3. On-Premises Data Gateway

The On-Premises Data Gateway (Standard Mode) connects mkc-sqlcall and CARDTROLSVR-01 to Fabric Pipelines and Dataflow Gen2 over an outbound encrypted tunnel (no inbound firewall rules required).

### Option A: Use Existing On-Premises Server (Recommended for MKC)

Host the gateway on the same subnet as the SQL Servers, on an existing Windows Server machine.

| Item | Cost |
|------|------|
| Gateway software license | Free |
| Azure resource overhead | None |
| On-prem server hardware (existing) | $0 additional |
| Internet egress (data to Fabric) | ~$0.01–0.05/GB (ISP or MPLS) |

**Recommendation:** Use existing on-prem infrastructure. Install gateway on a dedicated Windows service account. No Azure VM cost.

### Option B: Azure VM Hosting (Fallback)

If MKC wants to move the gateway off-premises (e.g. after server decommission or co-location):

| VM Size | vCPUs | RAM | PAYG / month | Notes |
|---------|-------|-----|--------------|-------|
| D2s_v3  | 2     | 8 GB | ~$154        | Light loads, <5 concurrent pipelines |
| D4s_v3  | 4     | 16 GB | ~$308       | Recommended for 7+ source databases, parallel CDC |
| D8s_v3  | 8     | 32 GB | ~$616       | Heavy parallel ingestion (20+ tables simultaneous) |

> Azure Hybrid Benefit (if MKC has Windows Server SA licenses) reduces VM cost by ~40%.

---

## 4. Azure SQL Managed Instance (Optional Lift-and-Shift)

If MKC migrates on-prem SQL Servers to Azure SQL MI (removes need for on-prem gateway for migrated DBs):

| Configuration | Price / month | Notes |
|---------------|--------------|-------|
| General Purpose, 4 vCores | ~$780 | Standard; suited for MKCGP / MWFGP workloads |
| General Purpose, 4 vCores + Azure Hybrid Benefit | ~$390 | Requires existing SQL Server SA licenses |
| General Purpose, 8 vCores + Hybrid Benefit | ~$780 | If consolidating multiple DBs |
| Business Critical, 4 vCores | ~$1,560 | High availability, in-memory OLTP |
| Storage (per 32 GB increment) | ~$23 | Included 32 GB; additional at $0.115/GB/mo |

> **Recommendation:** Keep on-prem SQL Servers as-is initially, use gateway. Only migrate to SQL MI if hardware refresh or DR requirements demand it.

---

## 5. Supporting Azure Services

### 5.1 Azure Monitor + Log Analytics

Monitors Fabric capacity utilization, pipeline alerts, and gateway health.

| Resource | Price |
|----------|-------|
| Log Analytics ingestion | First 5 GB/day free, then $2.30/GB |
| Log Analytics retention | 31 days free, then $0.10/GB/month |
| Azure Monitor alerts | First 1,000 metric alerts free, then $0.10/alert/month |
| MKC estimated ingestion | ~1–3 GB/day (pipeline runs, capacity metrics, audit logs) |
| **MKC estimated total** | **~$30–60/month** |

### 5.2 Azure Key Vault

Stores SPN credentials, gateway passwords, and connection strings.

| Resource | Price |
|----------|-------|
| Secrets operations | $0.03/10,000 operations |
| Keys (RSA 2048) | $0.03/10,000 operations |
| **MKC estimated total** | **<$5/month** |

### 5.3 Azure Functions (ML Model Serving)

Hosts trained ML models (yield prediction, churn, anomaly detection) as REST endpoints.

| Plan | Price |
|------|-------|
| Consumption plan | First 1M executions free; $0.20/million after |
| Premium EP1 (always-warm, VNet) | ~$175/month |
| **MKC estimated total** | **$0–$175/month** depending on call volume |

### 5.4 Data Egress

| Scenario | Price |
|----------|-------|
| Inbound to Azure | Free |
| Outbound from Azure to internet | First 100 GB/month free, then $0.08/GB |
| Within same Azure region | Free |

**MKC estimate:** Minimal — Power BI is served from Fabric (same region); on-prem data flows inbound. ~$0–10/month.

---

## 6. Power BI Licensing

| License | Price / user / month | Notes |
|---------|---------------------|-------|
| Power BI Free | $0 | View only, no workspace sharing |
| Power BI Pro | ~$10 | Required for publishing to shared workspaces **outside** F-SKU capacity |
| Power BI Premium Per User (PPU) | ~$20 | Individual Premium features; not needed with F-SKU |
| F-SKU (any tier) | Included | All workspace consumers get Premium-equivalent access for free |

> **Key insight:** With an F-SKU capacity, **report consumers do NOT need Pro licenses** to view reports published in that capacity's workspaces. Pro licenses are only needed by content creators publishing from their personal workspace.
>
> **MKC:** ~5–15 content creators (report developers) need Pro. Report consumers (field staff, executives) do not. Estimated: 10–15 × $10 = **$100–150/month**.

---

## 7. Three Deployment Scenarios

### Scenario A — Small (F8 Prod + F4 Dev/Test)

Best for: Early adoption / pilot phase, <50 active users, limited concurrent processing.

| Component | Monthly Cost |
|-----------|-------------|
| F8 Prod capacity (PAYG) | $1,048 |
| F4 Dev capacity (paused nights/weekends, ~60% usage) | $314 |
| OneLake storage (within free tier) | $0 |
| On-prem Gateway (existing server) | $0 |
| Azure Monitor + Log Analytics | $30 |
| Key Vault | $3 |
| Power BI Pro (30 content creators) | $300 |
| **Total** | **~$1,695/month (~$20,340/yr)** |
| With 1-yr reservation (F8+F4) | **~$1,257/month** |

Limitations: Limited concurrency for Notebooks + Pipelines + Power BI simultaneous usage. No Copilot.

---

### Scenario B — Medium / Recommended (F32 Prod + F8 Dev)

Best for: MKC production rollout, 50–150 active users, full medallion pipeline, self-service BI.

| Component | Monthly Cost |
|-----------|-------------|
| F32 Prod capacity (PAYG) | $4,194 |
| F8 Dev capacity (paused nights/weekends, ~60% usage) | $629 |
| OneLake storage (within free 8 TB tier) | $0 |
| On-prem Gateway (existing server) | $0 |
| Azure Monitor + Log Analytics | $45 |
| Key Vault | $3 |
| Power BI Pro (80 content creators) | $800 |
| Azure Functions (model serving, consumption plan) | $10 |
| **Total** | **~$5,681/month (~$68,172/yr)** |
| With 1-yr reservation (F32+F8) | **~$4,536/month (~$54,432/yr)** |

Includes: Full Bronze→Silver→Gold pipeline, all 22 workspaces, 170 reports, ML notebooks, feature store. No Copilot.

---

### Scenario C — Large (F64 Prod + F16 Dev)

Best for: Growth phase, 150–500 users, Fabric Copilot (NL→DAX/SQL), advanced ML, production-grade SLA.

| Component | Monthly Cost |
|-----------|-------------|
| F64 Prod capacity (PAYG) | $8,388 |
| F16 Dev capacity (paused nights/weekends, ~60% usage) | $1,258 |
| OneLake storage (within free 16 TB tier) | $0 |
| On-prem Gateway (existing server) | $0 |
| Azure Monitor + Log Analytics | $60 |
| Key Vault | $3 |
| Power BI Pro (0 — all in F64 capacity) | $0 |
| Azure Functions (model serving, EP1 plan) | $175 |
| Azure SQL MI 4 vCores + Hybrid Benefit (if migrated) | $390 |
| **Total** | **~$10,274/month (~$123,288/yr)** |
| With 1-yr reservation (F64+F16) | **~$7,484/month (~$89,808/yr)** |

Includes: Fabric Copilot, high-concurrency processing, production ML inference endpoint, optional SQL MI migration.

---

## 8. Break-Even Analysis: Pro Licenses vs F64

At F32, content creators still need Pro licenses (~$10/user). At F64, no Pro licenses needed for any user in that capacity.

| Metric | F32 + Pro | F64 |
|--------|-----------|-----|
| Capacity cost (PAYG) | $4,194 | $8,388 |
| Pro licenses (N users) | N × $10 | $0 |
| Break-even users | **≈ 419 users** | — |
| Break-even (1-yr reserved) | F32 reserved $3,146 + F64 reserved $6,292 → **(6292-3146)/10 ≈ 315 users** | — |

> **For MKC today:** F32 is more cost-effective until user count exceeds ~300–400. Upgrade to F64 when Copilot adoption or high user concurrency justifies it.

---

## 9. Cost Optimization Recommendations

1. **Pause Dev/Test capacity** — F8 dev capacity paused 16 hrs/day + weekends saves ~60% of dev cost (~$380/mo on F8 PAYG).

2. **Use 1-year reserved capacities** — ~25% savings on prod capacity. Commit once production architecture is stable (after 3-month pilot on PAYG).

3. **On-prem gateway on existing server** — Eliminates Azure VM cost (~$150–300/mo). Only migrate to Azure VM if on-prem hardware is decommissioned.

4. **Delta Lake V2 / liquid clustering** — Reduces scan costs for Gold layer aggregations; less CU consumed per Notebook run.

5. **External tables (no data copy)** — Gold Lakehouse data exposed via Fabric Warehouse external tables. No storage duplication; no ETL cost for semantic model refresh (DirectLake = zero-copy).

6. **Minimize Power BI Pro licenses** — With F-SKU capacity, only content creators need Pro (~10–15 licenses). All 150+ report consumers access for free.

7. **Schedule Notebooks off-peak** — Bronze→Silver and Silver→Gold Notebook jobs run during off-hours (midnight–6 AM). CU smoothing allows 10× burst for 10 min; scheduling off-peak avoids throttling during business-hours Power BI usage.

8. **Cold-tier archival for Bronze 5+ yr data** — Move Delta partitions older than 5 years to OneLake cold tier ($0.00099/GB vs $0.023/GB standard). Saves ~95% on archival storage.

9. **Eventstream only for real-time needs** — Eventstream consumes CU continuously. Only enable for grain price feeds and IoT telemetry. Batch CDC via Pipelines for transactional systems.

10. **Monitor with Fabric Capacity Metrics app** — Free built-in app shows CU usage by workspace and operation. Identify top CU consumers and schedule or optimize before upgrading SKU.

---

## 10. Summary Comparison

| | Scenario A (Small) | Scenario B (Medium) ⭐ | Scenario C (Large) |
|---|---|---|---|
| **F-SKU (Prod)** | F8 | F32 | F64 |
| **F-SKU (Dev)** | F4 | F8 | F16 |
| **Copilot** | No | No | Yes |
| **Max concurrent users** | ~30 | ~150 | ~500 |
| **PAYG / month** | ~$1,695 | ~$5,681 | ~$10,274 |
| **1-yr reserved / month** | ~$1,257 | ~$4,536 | ~$7,484 |
| **Best for** | Pilot / PoC | MKC production rollout | Scale-out + AI |

> ⭐ **Recommended for MKC:** Start on **F32 Prod + F8 Dev** (Scenario B) at ~$4,536/month with 1-yr reservation. This covers all 22 workspaces, 170 reports, full medallion pipeline, and room for ML notebooks. Upgrade to F64 when Copilot or user growth demands it.

---

## 11. Architecture Component Map (Full Cost Breakdown)

| Fabric/Azure Component | Fabric SKU included? | Additional Cost |
|------------------------|----------------------|----------------|
| Fabric Pipelines (ADF-equivalent) | Yes | $0 |
| Dataflow Gen2 (37 shared flows) | Yes | $0 |
| On-Premises Data Gateway | Yes (license) | $0 (on existing server) |
| Bronze Lakehouse (OneLake Delta) | Yes | $0 (within free storage) |
| Silver Lakehouse (OneLake Delta) | Yes | $0 |
| Gold Lakehouse (OneLake Delta) | Yes | $0 |
| Fabric Warehouse (external tables) | Yes | $0 |
| Semantic Models (DirectLake) | Yes | $0 |
| Power BI Workspaces (22) | Yes | $0 |
| Eventstream (real-time grain/IoT) | Yes | $0 |
| Fabric Notebooks (PySpark) | Yes | $0 |
| ML Experiments (MLflow) | Yes | $0 |
| Feature Store (Gold Delta) | Yes | $0 |
| Fabric Copilot (NL→DAX/SQL) | F64+ only | $0 (if on F64) |
| OneLake storage (ADLS Gen2) | Yes up to free tier | $0.023/GB beyond free |
| Microsoft Purview (Data Catalog) | Yes (basic lineage) | $0–$100+ for advanced |
| Azure Monitor + Log Analytics | No | ~$30–60/month |
| Azure Key Vault | No | ~$3–5/month |
| Azure Functions (model serving) | No | $0–$175/month |
| Power BI Pro (content creators) | No | ~$10/user/month |
| Azure SQL MI (optional) | No | ~$390–780/month |
| On-prem Data Gateway VM (optional) | No (if on Azure VM) | ~$154–308/month |

---

*Prices sourced from Microsoft Azure public pricing calculator (East US, February 2026). All figures are estimates; consult Microsoft or a Microsoft partner for EA/CSP pricing.*
