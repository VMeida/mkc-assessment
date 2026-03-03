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
