# Cost Optimization

Ten actionable recommendations to reduce MKC's Fabric platform costs without sacrificing capability.

---

## 1. Pause Dev/Test Capacity

Configure the Dev capacity (F8) to pause during non-working hours via an **Azure Logic App** calling the Fabric REST API.

| Schedule | Uptime | Monthly Cost (F8 PAYG) | Saving |
|----------|--------|----------------------|--------|
| Always on | 100% | $1,048 | — |
| Pause nights + weekends | ~40% | ~$420 | **$628/mo** |
| On-demand only | ~20% | ~$210 | **$838/mo** |

```python
# Logic App action — pause capacity
import requests

def pause_capacity(capacity_id: str, token: str):
    r = requests.post(
        f"https://api.fabric.microsoft.com/v1/capacities/{capacity_id}/suspend",
        headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
```

**Save: ~$380–840/month** on Dev F8.

---

## 2. Commit to 1-Year Reservations

After a 3-month PAYG pilot, commit to 1-year reserved capacity for Prod and Dev.

| SKU | PAYG/month | 1-yr Reserved/month | Saving |
|-----|-----------|---------------------|--------|
| F32 | $4,194 | $3,146 | $1,048/mo |
| F8 | $1,048 | $786 | $262/mo |
| **Combined F32+F8** | **$5,242** | **$3,932** | **$1,310/mo** |

**Save: ~$1,310/month (~25%)** — $15,720/year.

---

## 3. Use Existing On-Premises Gateway

Installing the On-Premises Data Gateway on an existing Windows Server in the same subnet as the SQL Servers eliminates Azure VM cost entirely.

| Option | Monthly Cost |
|--------|-------------|
| Azure D4s_v3 VM gateway | ~$308 |
| Existing on-prem server | $0 |

**Save: ~$300/month** if avoiding Azure VM gateway.

---

## 4. Delta Lake Optimisation (Liquid Clustering)

Enable Delta V2 liquid clustering on high-read Gold tables to reduce CU consumed per Notebook and semantic model scan:

```python
spark.sql("""
    ALTER TABLE Gold.FactGrainSales
    CLUSTER BY (date_key, location_key)
""")

-- Run OPTIMIZE periodically
spark.sql("OPTIMIZE Gold.FactGrainSales")
```

Liquid clustering co-locates related data, reducing the number of files scanned per query — fewer CUs consumed per Power BI report refresh.

**Save: 15–30% CU reduction** on Gold reads → defer F32→F64 upgrade.

---

## 5. External Tables — Zero Storage Duplication

Gold Lakehouse data is exposed as Fabric Warehouse **external tables** (no data copy). Semantic models use DirectLake mode (reads Delta directly). There is **no third copy** of any data.

| Approach | Storage | ETL Cost | Refresh Time |
|----------|---------|---------|-------------|
| Import mode | 3× data volume | High (full reload) | 30–60 min |
| DirectQuery | 1× | None | Real-time (slow) |
| **DirectLake** | **1×** | **None** | **Sub-second** |

**Save: significant storage and ETL compute** by staying in DirectLake mode.

---

## 6. Minimise Power BI Pro Licenses

With F-SKU capacity, only **content creators** (report developers) need Pro licenses. All report consumers (field staff, executives, managers) access reports license-free.

| Scenario | Pro licenses | Cost |
|----------|-------------|------|
| Everyone has Pro | 150 users | $1,500/month |
| Creators only (10) | 10 users | $100/month |

**Save: up to $1,400/month** by not assigning Pro to consumers.

---

## 7. Schedule Notebooks Off-Peak

Bronze→Silver and Silver→Gold Notebook jobs run at **midnight–6 AM CST** when Power BI interactive queries are minimal. Fabric's CU smoothing allows 10× burst for 10-minute windows — off-peak jobs get full burst capacity without throttling business-hours BI.

---

## 8. Cold-Tier Archival for Old Bronze Data

Move Bronze Delta partitions older than 5 years to OneLake cold storage tier:

```python
# Move old Bronze partitions to cold tier
# (done via ADLS Gen2 lifecycle policy in Azure Portal)
# Applies to: abfss://Bronze-Prod@onelake.dfs.fabric.microsoft.com/Tables/*/
# Condition: Last modified > 1,825 days (5 years)
# Action: Move to Archive tier
```

| Tier | Price/GB/month | 2 TB over 5 yrs |
|------|---------------|----------------|
| Standard LRS | $0.023 | $47/month |
| Cold/Archive | $0.00099 | $2/month |

**Save: ~$45/month per 2 TB archived** — cumulative savings grow as Bronze data ages.

---

## 9. Eventstream Only for Real-Time Needs

Eventstream consumes CUs **continuously** (even when idle). Only enable it for truly real-time sources:

| Source | Use Eventstream? | Alternative |
|--------|-----------------|------------|
| Grain price feeds (real-time) | Yes | — |
| IoT sensor telemetry | Yes | — |
| MKCGP SQL transactions | **No** | Fabric Pipeline CDC (hourly) |
| AgVantage API | **No** | Dataflow Gen2 (daily) |

Disabling unnecessary Eventstream items saves idle CU consumption.

---

## 10. Monitor with Fabric Capacity Metrics App

The **Microsoft Fabric Capacity Metrics app** (free, installable from AppSource) shows real-time and historical CU usage by workspace, item type, and operation. Use it to:

- Identify top CU consumers (usually large Spark jobs or heavy DirectQuery loads)
- Catch CU throttling events before they impact users
- Right-size the F-SKU decision (upgrade vs. optimise existing workload)
- Detect runaway Notebooks or misconfigured Eventstream items

```
Install: Power BI AppSource → "Microsoft Fabric Capacity Metrics"
Connect to: Your Fabric capacity workspace
```

---

## Optimization Impact Summary

| Optimization | Monthly Saving | Effort |
|-------------|---------------|--------|
| 1. Pause Dev capacity | $380–840 | Low |
| 2. 1-yr reservation | $1,310 | Low |
| 3. On-prem gateway | $300 | Low |
| 4. Delta clustering | 15–30% CU | Medium |
| 5. DirectLake (no import) | Storage + ETL | Low (default) |
| 6. Minimize Pro licenses | Up to $1,400 | Low |
| 7. Off-peak scheduling | CU headroom | Low |
| 8. Cold-tier archival | $45+ (grows) | Medium |
| 9. Targeted Eventstream | CU headroom | Low |
| 10. Capacity Metrics app | Diagnostic | Low |
| **Total potential saving** | **~$3,400+/month** | |
