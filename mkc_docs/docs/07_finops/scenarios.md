# Deployment Scenarios

Three deployment configurations are modelled for MKC, covering the pilot, production, and scale-out phases.

## Scenario Comparison

| | Scenario A (Small) | Scenario B (Medium) ⭐ | Scenario C (Large) |
|---|---|---|---|
| **Prod F-SKU** | F8 | F32 | F64 |
| **Dev F-SKU** | F4 | F8 | F16 |
| **Max concurrent users** | ~30 | ~150 | ~500 |
| **Fabric Copilot** | No | No | Yes (F64+) |
| **PAYG/month** | ~$1,695 | ~$5,681 | ~$10,274 |
| **1-yr reserved/month** | ~$1,257 | **~$4,536** | ~$7,484 |
| **Best for** | Pilot / PoC | MKC production rollout | Scale-out + AI |

> ⭐ **Recommended for MKC:** Scenario B — F32 Prod + F8 Dev. Start on PAYG for 3 months, then commit to 1-yr reservation.

---

## Scenario A — Small (F8 Prod + F4 Dev)

Best for early adoption / pilot phase with < 50 active users and limited concurrent processing.

| Component | Monthly Cost |
|-----------|-------------|
| F8 Prod capacity (PAYG) | $1,048 |
| F4 Dev capacity (paused nights/weekends, ~60% uptime) | $314 |
| OneLake storage (within 2 TB free tier) | $0 |
| On-Premises Data Gateway (existing on-prem server) | $0 |
| Azure Monitor + Log Analytics | $30 |
| Azure Key Vault | $3 |
| Power BI Pro (30 content creators) | $300 |
| **Total (PAYG)** | **~$1,695/month (~$20,340/yr)** |
| **Total (1-yr reserved)** | **~$1,257/month (~$15,084/yr)** |

**Limitations:** Limited concurrency for simultaneous Notebooks + Pipelines + Power BI. No Copilot. Not suitable for production Silver→Gold Spark jobs alongside interactive BI queries.

---

## Scenario B — Medium / Recommended (F32 Prod + F8 Dev)

Best for MKC's production rollout: 50–150 active users, full medallion pipeline, self-service BI across all 12 workspaces.

| Component | Monthly Cost |
|-----------|-------------|
| F32 Prod capacity (PAYG) | $4,194 |
| F8 Dev capacity (paused nights/weekends, ~60% uptime) | $629 |
| OneLake storage (within 8 TB free tier) | $0 |
| On-Premises Data Gateway (existing on-prem server) | $0 |
| Azure Monitor + Log Analytics | $45 |
| Azure Key Vault | $3 |
| Power BI Pro (80 content creators) | $800 |
| Azure Functions (ML model serving, consumption plan) | $10 |
| **Total (PAYG)** | **~$5,681/month (~$68,172/yr)** |
| **Total (1-yr reserved)** | **~$4,536/month (~$54,432/yr)** |

**Includes:** Full Bronze→Silver→Gold pipeline, all 12 workspaces, 40 reports, ML Notebooks, Feature Store, Data Agents (4 agents via Azure OpenAI — tokens billed separately, see [AI Cost Scenarios](../05_ai-mlops/cost-scenarios.md)).

---

## Scenario C — Large (F64 Prod + F16 Dev)

Best for growth phase: 150–500 users, Fabric Copilot, advanced ML, production-grade SLA, optional Azure SQL MI migration.

| Component | Monthly Cost |
|-----------|-------------|
| F64 Prod capacity (PAYG) | $8,388 |
| F16 Dev capacity (paused nights/weekends, ~60% uptime) | $1,258 |
| OneLake storage (within 16 TB free tier) | $0 |
| On-Premises Data Gateway (existing on-prem server) | $0 |
| Azure Monitor + Log Analytics | $60 |
| Azure Key Vault | $3 |
| Power BI Pro (0 — all users within F64 capacity) | $0 |
| Azure Functions (ML model serving, EP1 plan, always-warm) | $175 |
| Azure SQL MI 4 vCores + Hybrid Benefit (if migrated) | $390 |
| **Total (PAYG)** | **~$10,274/month (~$123,288/yr)** |
| **Total (1-yr reserved)** | **~$7,484/month (~$89,808/yr)** |

**Adds:** Fabric Copilot (F64+ requirement), high-concurrency processing, always-warm ML inference endpoint, optional elimination of on-prem SQL Servers via Azure SQL MI.

---

## Break-Even Analysis: F32+Pro vs F64

At F32, content creators still need Power BI Pro licenses (~$10/user/month). At F64, no Pro licenses are required for any user in the capacity.

| Metric | F32 PAYG + Pro | F64 PAYG |
|--------|---------------|---------|
| Capacity cost | $4,194 | $8,388 |
| Pro licenses (N users) | N × $10 | $0 |
| **PAYG break-even** | **≈ 419 users** | |
| F32 reserved + Pro vs F64 reserved | $3,146 + N×$10 | $6,292 |
| **Reserved break-even** | **≈ 315 users** | |

**For MKC today:** F32 is more cost-effective until the user count exceeds ~300–400. Upgrade to F64 when Copilot adoption, high user concurrency, or user count growth justifies it.

---

## Supporting Services Summary

| Service | Scenario A | Scenario B | Scenario C |
|---------|-----------|-----------|-----------|
| Azure Monitor + Log Analytics | $30 | $45 | $60 |
| Azure Key Vault | $3 | $3 | $3 |
| Azure Functions (model serving) | $0 | $10 | $175 |
| Azure SQL MI (optional) | $0 | $0 | $390 |
| Data egress | ~$0–5 | ~$0–10 | ~$5–20 |
