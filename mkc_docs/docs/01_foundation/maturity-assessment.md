# Data Maturity Assessment

MKC is assessed against a 5-level data maturity model across six dimensions. The assessment reflects the **current state** and the **target state** after full platform delivery.

## Maturity Levels

| Level | Name | Description |
|-------|------|-------------|
| 1 | **Ad-hoc** | Manual, reactive, undocumented |
| 2 | **Repeatable** | Documented, consistent within teams |
| 3 | **Defined** | Standardised across the organisation |
| 4 | **Managed** | Measured, monitored, SLA-driven |
| 5 | **Optimised** | Automated, self-improving, predictive |

## Assessment by Dimension

### Data Ingestion

| Dimension | Current (Level) | Evidence | Target (Level) |
|-----------|----------------|---------|----------------|
| Source coverage | 2 — Repeatable | 7 SQL + 5 SaaS connected but ad-hoc | 4 — Managed |
| Incremental load | 1 — Ad-hoc | Full loads dominate; no watermark strategy | 4 — Managed |
| Real-time data | 1 — Ad-hoc | No streaming | 3 — Defined |
| Gateway resilience | 1 — Ad-hoc | Single gateway, no failover monitoring | 3 — Defined |

**Current: 1.25 / Target: 3.5**

---

### Data Quality

| Dimension | Current | Target |
|-----------|---------|--------|
| Schema validation | 1 — None | 4 — Enforced at Silver ingest |
| Null / completeness checks | 1 — None | 4 — Automated DQ rules |
| Referential integrity | 1 — None | 3 — Cross-layer FK checks |
| Anomaly detection | 1 — None | 3 — Statistical thresholds in Notebooks |

**Current: 1.0 / Target: 3.5**

---

### Governance & Lineage

| Dimension | Current | Target |
|-----------|---------|--------|
| Data catalog | 1 — None | 4 — Purview auto-scan |
| Lineage | 1 — None | 4 — Purview pipeline lineage |
| Sensitivity labels | 1 — None | 4 — Purview sensitivity classifications |
| Access control | 2 — Workspace-level | 5 — RLS + OLS per Entra group |

**Current: 1.25 / Target: 4.25**

---

### Analytics & BI

| Dimension | Current | Target |
|-----------|---------|--------|
| Metric consistency | 1 — Per-report definitions | 4 — Shared semantic models |
| Self-service | 2 — Limited | 4 — Governed self-service via semantic models |
| Report performance | 2 — Import mode delays | 5 — DirectLake sub-second |
| Mobile / portal | 1 — None | 3 — Power BI mobile + producer portal |

**Current: 1.5 / Target: 4.0**

---

### AI & Advanced Analytics

| Dimension | Current | Target |
|-----------|---------|--------|
| ML models in production | 1 — None | 3 — Yield + demand prediction |
| NL querying | 1 — None | 4 — Data Agents (GPT-4o) |
| Feature store | 1 — None | 3 — Gold Delta feature tables |
| LLM governance | 1 — None | 5 — Private endpoint + APIM + audit log |

**Current: 1.0 / Target: 3.75**

---

### DevOps & Automation

| Dimension | Current | Target |
|-----------|---------|--------|
| Source control | 1 — None | 4 — Fabric Git integration + ADO |
| CI/CD | 1 — None | 4 — GitHub Actions pipeline promotion |
| Environment isolation | 1 — None | 4 — Dev / Test / Prod workspaces |
| Automated testing | 1 — None | 3 — Data quality + notebook tests |

**Current: 1.0 / Target: 3.75**

---

## Maturity Radar Summary

| Dimension | Current | Target | Delta |
|-----------|---------|--------|-------|
| Data Ingestion | 1.25 | 3.50 | +2.25 |
| Data Quality | 1.00 | 3.50 | +2.50 |
| Governance & Lineage | 1.25 | 4.25 | +3.00 |
| Analytics & BI | 1.50 | 4.00 | +2.50 |
| AI & Advanced Analytics | 1.00 | 3.75 | +2.75 |
| DevOps & Automation | 1.00 | 3.75 | +2.75 |
| **Overall Average** | **1.17** | **3.79** | **+2.62** |

!!! success "Assessment Conclusion"
    MKC is at an early (Level 1–2) maturity baseline across all dimensions — typical for a co-operative of this size that has grown its analytics organically. The target platform delivers a **+2.6 level average improvement**, moving MKC from ad-hoc analytics to a managed, governed, AI-ready data platform.

---

## References

| Resource | Description |
|----------|-------------|
| [Microsoft Fabric adoption roadmap](https://learn.microsoft.com/en-us/power-bi/guidance/fabric-adoption-roadmap) | Guidance on driving organisational adoption of Microsoft Fabric |
| [Azure Cloud Adoption Framework — data](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/) | Cloud-scale analytics reference architecture and maturity model |
| [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/) | Five pillars of workload quality: reliability, security, cost, performance, operations |
| [Data management and analytics scenario](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/architectures/data-mesh-scenario) | Data mesh architecture pattern in the Azure Cloud Adoption Framework |
