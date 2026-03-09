# Microsoft Purview

## Role in MKC's Platform

Microsoft Purview provides three governance capabilities for the MKC Fabric platform:

1. **Data Catalog** — Searchable inventory of all tables, columns, and reports across OneLake
2. **Lineage** — Automatic end-to-end data flow tracking (source → Bronze → Silver → Gold → Semantic Model → Report)
3. **Sensitivity Labels** — Microsoft Information Protection (MIP) labels applied to sensitive columns and files

## Data Catalog

Purview auto-scans OneLake lakehouses and registers all Delta tables as **data assets** in the unified catalog:

```
Purview Data Catalog
├── mkc-sqlcall (SQL Server — scanned via Purview connector)
│   ├── MKCGP.dbo.IV30300 (Inventory transactions)
│   ├── MKCGP.dbo.RM00101 (Customer master)
│   └── ...
├── MKC-Bronze-Prod.Lakehouse (OneLake — auto-scanned)
│   ├── mkcgp_iv30300 (Bronze inventory table)
│   └── ...
├── MKC-Silver-Prod.Lakehouse
│   └── fact_inventory (Silver cleaned table)
├── MKC-Gold-Prod.Lakehouse
│   └── FactInventory (Gold aggregate table)
└── MKC-SemanticModels-Prod
    └── Operations.SemanticModel → FactInventory
```

Each asset in the catalog shows:
- **Schema** (column names, types, descriptions)
- **Owner** (Entra user or group)
- **Sensitivity label** (Public, Internal, Confidential, Highly Confidential)
- **Lineage** (upstream and downstream connections)
- **Last refreshed** (scan timestamp)

## Automatic Lineage

Purview captures lineage automatically from:

| Source | Lineage Mechanism |
|--------|------------------|
| Fabric Pipelines | Pipeline activity logs → Purview connector |
| Fabric Notebooks (PySpark) | Spark lineage plugin auto-traces `read()` and `write()` |
| Dataflow Gen2 | Power Query data source + sink registration |
| Semantic Models | Power BI lineage scanner |
| Reports | Power BI dataset → report lineage |

End-to-end lineage view for a grain sales KPI:
```
mkc-sqlcall.MKCGP.SOP10100 (Sales Order Header)
    → Fabric Pipeline (hourly CDC)
    → Bronze.mkcgp_sop10100
        → Silver Notebook (MERGE INTO)
        → Silver.grain_sale_transaction
            → Gold Notebook (Spark SQL aggregation)
            → Gold.FactGrainSales
                → Sales Semantic Model
                    → Sales BI Workspace (8 reports)
```

## Sensitivity Labels

MIP sensitivity labels are applied at the column level:

| Label | Definition | Columns |
|-------|-----------|---------|
| **Public** | No restrictions | Report names, location names |
| **Internal** | MKC employees only | Sales volumes, grain prices |
| **Confidential** | Named roles only | Cost margins, customer credit limits |
| **Highly Confidential** | HR/Finance leadership only | Salary amounts, hourly rates |

Labels are applied in Purview and propagate to:
- OneLake Delta column metadata
- Power BI semantic model columns
- Export and sharing restrictions (Confidential+ cannot be exported to Excel by default)

## Purview Scan Schedule

| Asset Type | Scan Frequency |
|------------|---------------|
| On-prem SQL sources | Weekly full scan |
| OneLake Bronze | Daily incremental |
| OneLake Silver / Gold | Daily incremental |
| Semantic Models (Power BI scanner) | Daily |
| Fabric Pipeline definitions | On-change (webhook) |

---

## Estimated Cost

!!! warning "Budget Impact"
    Purview costs are **not included in the base Fabric capacity**. Plan for an additional $200–450/month depending on scan frequency and on-prem connectivity requirements.

| Component | Cost |
|-----------|------|
| Data Map Capacity Units (4 CU baseline, always-on) | ~$143/month |
| Scanning throughput (8 CU burst during active scans) | ~$286/month |
| Self-hosted Integration Runtime (on-prem SQL scans via Azure VM) | ~$75–150/month |
| **Estimated total for MKC scope** | **~$200–450/month** |

**Pricing basis:** Data Map CU at $0.496/CU-hour × 4 CU × 24h × 30 days = ~$143/month baseline. Burst to 8 CU during weekly full scans raises peak cost. A Self-Hosted Integration Runtime (SHIR) or Azure VM is required to scan the on-prem GP SQL Server (~$75–150/month additional).

---

## Purview vs. Fabric Native — Capability-by-Capability

For an organisation at MKC's current maturity level, full Purview may be over-engineered for Phase 1. The sections below break down each governance capability individually so the decision to adopt or skip Purview (or a specific alternative) can be made per feature.

---

### Capability 1 — End-to-End Lineage (including on-prem SQL)

**Fabric Native:** Shows data flow *inside* Fabric only. On-prem sources appear as "External Data Source" — no drill-through to `mkc-sqlcall.MKCGP.SOP10100`. The lineage chain is broken at the Dataflow/Pipeline ingestion point.

**What Purview adds:** Closes the gap via SHIR + SQL Server connector. Full chain: `mkc-sqlcall → Pipeline → Bronze → Silver → Gold → Semantic Model → Report`.

**Free / cheaper alternatives:**

- **Manual documentation (current `app.py` + MkDocs)** — Free. MKC already maintains this. Not automatic; requires discipline to keep up to date.
- **OpenLineage + Marquez** (OSS) — Free + ~$30/month Azure hosting. OpenLineage is the open standard for lineage events; Marquez is the free UI/backend. Fabric does not emit OpenLineage events natively — requires a custom Spark listener in notebooks (~2–3 days engineering effort). Best ROI if the team has Python skills.
- **OpenMetadata** — ~$50/month hosting. Has Fabric/Power BI connector (partial); on-prem SQL lineage requires a custom connector. Less complete than Purview but significantly cheaper.
- **dbt** — Free (OSS) or ~$50/month (dbt Cloud). Only applicable if dbt is used for SQL transformations; not relevant for Spark Notebook transforms.

!!! tip "MKC Verdict"
    Manual docs (`app.py`) cover the immediate need at $0. If automated lineage from GP SQL becomes a priority, evaluate OpenLineage + Marquez (~$30/month, engineering effort) before committing to Purview.

---

### Capability 2 — Cross-Workspace Searchable Catalog

**Fabric Native:** Each workspace shows its own item list in the portal. There is no cross-workspace search by column name, data type, or owner. Finding "which table has a `grain_price` column across all lakehouses" requires opening each workspace manually.

**What Purview adds:** Unified catalog searchable by column name, owner, sensitivity label, business term, or classification tag across all workspaces simultaneously.

**Free / cheaper alternatives:**

- **MkDocs inventory pages (current)** — Free. The `03_data-consumption/` section auto-generated from Excel serves this purpose at zero cost. Not interactive but sufficient for MKC's ~12 workspaces.
- **OpenMetadata** — ~$50/month Azure hosting. Has a Power BI connector (scans workspaces, datasets, reports) and OneLake connector (via ADLS Gen2). Provides a searchable UI, glossary, and ownership model. Best free-tier alternative to Purview catalog.
- **DataHub (LinkedIn OSS)** — ~$50–100/month. Similar to OpenMetadata; slightly steeper learning curve but a stronger lineage model.

!!! tip "MKC Verdict"
    MkDocs covers this at $0 for now. If demand grows beyond ~15 workspaces or users start asking "where is field X?", OpenMetadata at ~$50/month is the right step before Purview.

---

### Capability 3 — Automated PII / Sensitive Column Detection

**Fabric Native:** None. Sensitivity labels must be applied manually — Fabric does not scan column values to detect CPF, account numbers, or financial data automatically.

**What Purview adds:** Data Map auto-scans column values during scheduled scans and flags columns containing patterns matching PII classifiers (CPF, CNPJ, credit card numbers, email addresses, etc.). No human review needed for initial classification.

**Free / cheaper alternatives:**

- **No turnkey free alternative** — this is Purview's unique differentiator in the Microsoft ecosystem for automatic classification.
- **Presidio (Microsoft OSS)** — Free. Runs PII detection on DataFrames in Python/Spark. Can be added as a notebook step to flag sensitive columns and write results to a metadata table. Requires ~3–5 days engineering effort to build the scanning pipeline. No portal UI — results live in a Delta table or Markdown report.
- **Manual labelling** — Free. Given MKC's relatively small schema (B2B agricultural data, no consumer PII), manual review of column names is feasible once at schema design time.

!!! tip "MKC Verdict"
    Manual labelling at schema design time is sufficient. MKC data does not include consumer PII (no CPF/CNPJ volumes, no credit cards). Purview auto-classification is not cost-justified.

---

### Capability 4 — Sensitivity Labels (MIP)

**Fabric Native:** Fabric can *apply* MIP labels to items (files, semantic models, lakehouses), but label *creation and policy management* require either the M365 Compliance Portal or Purview. Without a published label policy, labels have no enforcement effect.

**What Purview adds:** Purview Data Map enables automated label propagation to columns discovered during scan — labels applied to a source column flow downstream automatically.

**Free / cheaper alternatives:**

- **Microsoft 365 Compliance Portal — Free (included in M365 E3/E5).** Labels are created, scoped, and published here. Power BI and OneLake respect these labels with no Purview Data Map required. The only limitation vs. Purview: labels must be applied manually per item (no auto-propagation from scan). For MKC's scale (12 workspaces, ~40 reports), manual assignment is feasible.

!!! tip "MKC Verdict"
    Use M365 Compliance Portal for sensitivity labels — $0 additional cost. Purview Data Map is only needed if automated column-level label propagation becomes a compliance requirement.

---

### Capability 5 — Formal Data Ownership & Stewardship Workflow

**Fabric Native:** Workspace-level roles (Admin, Member, Contributor, Viewer) only. No asset-level ownership — no way to assign a "Data Owner" to a specific table or column, or to track who approved a classification change.

**What Purview adds:** Per-asset Data Owner and Data Steward assignment, access request workflows, and an audit trail of classification approvals.

**Free / cheaper alternatives:**

- **OpenMetadata** — ~$50/month. Full ownership model: Owner, Expert, Reviewer per asset. Includes a data access request flow. Suitable replacement for Purview's stewardship features.
- **Documented ownership in MkDocs** — Free. A simple ownership table in the governance docs covers the need at MKC's current maturity. Not enforceable, but sufficient before a Data Steward role exists.

!!! tip "MKC Verdict"
    Document ownership in MkDocs for now. Formal stewardship workflow is a Phase 3 need, contingent on hiring a Data Steward.

---

### Summary

| Capability | Fabric Native | Purview | Free Alternative | Cheaper Alternative | MKC Verdict |
|---|---|---|---|---|---|
| Lineage within Fabric | Auto (free) | Full chain incl. on-prem | Manual docs / OpenLineage+Marquez (~$30/mo) | OpenMetadata (~$50/mo) | Fabric Native now; OpenLineage if on-prem lineage demanded |
| Cross-workspace catalog | No | Yes | MkDocs (current, free) | OpenMetadata (~$50/mo) | MkDocs now; OpenMetadata at scale |
| Auto PII detection | No | Yes (Data Map scan) | Presidio OSS (engineering effort) | None turnkey | Manual labelling; Presidio if volume grows |
| Sensitivity Labels (MIP) | Apply only | Auto-propagate via scan | **M365 Compliance Portal (free)** | — | M365 Portal covers MKC needs at $0 |
| Ownership & stewardship | Workspace roles only | Per-asset + audit trail | MkDocs ownership table (free) | OpenMetadata (~$50/mo) | MkDocs now; OpenMetadata in Phase 2 |
