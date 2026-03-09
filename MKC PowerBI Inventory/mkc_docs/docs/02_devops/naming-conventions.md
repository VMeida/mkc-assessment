# Naming Conventions

This page is the single source of truth for all naming patterns used across MKC's Fabric platform. Consistent names are the foundation of cross-workspace search, automated lineage, and CI/CD variable substitution.

---

## Fabric Artifact Names

### Workspaces

```
MKC-{Layer}-{Environment}
```

| Token | Values |
|---|---|
| `{Layer}` | `Bronze`, `Silver`, `Gold`, `SemanticModels`, `BI-{Domain}` |
| `{Environment}` | `Dev`, `Prod` |

**Examples:**

```
MKC-Bronze-Prod
MKC-Silver-Dev
MKC-Gold-Prod
MKC-SemanticModels-Prod
MKC-BI-Sales-Prod
MKC-BI-Financial-Prod
MKC-BI-Operations-Prod
```

---

### Lakehouses

Lakehouses live inside a workspace. The name mirrors the layer only (no environment suffix — the workspace already carries it):

```
{Layer}.Lakehouse
```

**Examples:**

```
Bronze.Lakehouse
Silver.Lakehouse
Gold.Lakehouse
```

!!! info "Why no env suffix on the Lakehouse name?"
    The environment is encoded in the workspace (`MKC-Bronze-Dev` vs `MKC-Bronze-Prod`). Repeating it in the Lakehouse name creates redundancy and complicates notebook path templates.

---

### Notebooks

```
nb-{layer}-{action}-{subject}
```

All lowercase, hyphen-separated. The `{layer}` token makes the notebook's position in the medallion immediately clear.

| Token | Values |
|---|---|
| `{layer}` | `bronze`, `silver`, `gold`, `utils` |
| `{action}` | `ingest`, `transform`, `aggregate`, `validate`, `repair` |
| `{subject}` | Source table or entity name in `snake_case` |

**Examples:**

```
nb-bronze-ingest-sop10100
nb-bronze-ingest-rm00101
nb-silver-transform-grain-sale-transaction
nb-silver-validate-fact-inventory
nb-gold-aggregate-fact-grain-sales
nb-utils-schema-drift-check
```

---

### Pipelines

```
pl-{layer}-{subject}
```

Pipelines orchestrate one or more notebooks for a subject area. Keep the name at the pipeline level — do not repeat individual notebook names.

**Examples:**

```
pl-bronze-gp-daily-ingest
pl-silver-sales-transform
pl-gold-refresh-all
pl-bronze-sharepoint-ingest
pl-bronze-agvantage-api
```

---

### Dataflow Gen2

Dataflows handle small-payload ingestion (API/SharePoint → Bronze). Name them after their source:

```
dfw-{source}-{subject}
```

**Examples:**

```
dfw-sharepoint-crop-plan
dfw-dynamics-crm-opportunity
dfw-agvantage-field-applications
dfw-agworld-producer-master
```

---

### Semantic Models

Semantic models are named after their business domain. No environment suffix (managed by workspace):

```
{Domain}.SemanticModel
```

**Examples:**

```
Sales.SemanticModel
Financial.SemanticModel
Operations.SemanticModel
```

---

### Reports

Reports live in BI workspaces. Name them after the business subject with Title Case:

```
{Subject Area} {Report Type}
```

Where `{Report Type}` is one of: `Dashboard`, `Scorecard`, `Report`, `Analysis`.

**Examples:**

```
Grain Sales Dashboard
Agronomy Scorecard
AP Aging Report
Inventory On Hand Report
Payroll Summary Dashboard
GL Cost Center Analysis
```

---

### DAX Measures

Measures use **Title Case with spaces**, wrapped in square brackets in DAX:

```
[{Aggregation} {Subject}]
```

**Examples:**

```
[Total Grain Revenue]
[Grain Margin %]
[Inventory On Hand]
[AP Overdue Amount]
[AR 60+ Days]
[YTD Feed Sales]
```

!!! warning "No underscores in measure names"
    Measure names appear in report tooltips and field lists. Use human-readable Title Case, not `snake_case` or `SCREAMING_SNAKE`.

---

## Column Naming Contract

Column names are the contract that travels across all medallion layers. The rules below define what happens to a column name at each layer transition. Enforcing these rules at Silver is the mechanism that standardises columns across all environments and workspaces.

### The Three-Layer Contract

```
Source (GP / AgVantage / SharePoint)
    ↓  Bronze: mirror source names exactly
Bronze.Lakehouse
    ↓  Silver: rename to snake_case canonical form
Silver.Lakehouse
    ↓  Gold: add surrogate keys; names carry through unchanged
Gold.Lakehouse / Gold.Warehouse
    ↓  DirectLake: column names inherited unchanged
Semantic Model
    ↓  DAX: measures follow [Title Case] convention
```

---

### Bronze — Mirror Source Names

Bronze tables replicate the source exactly. **Do not rename columns.** Renaming at Bronze breaks reprocessability and makes it impossible to trace a Bronze value back to the source system.

| Rule | Example |
|---|---|
| Copy column names verbatim from source | `ITEMNMBR`, `CUSTNMBR`, `TRXDATE` |
| Add audit columns with `_` prefix | `_ingested_at TIMESTAMP`, `_source_system STRING` |
| Table names: `{source_db}_{source_table}` in `lowercase_snake` | `mkcgp_sop10100`, `mkcgp_rm00101` |

**Bronze audit columns (added at every ingest, never from source):**

| Column | Type | Description |
|---|---|---|
| `_ingested_at` | `TIMESTAMP` | When the row was written to Bronze |
| `_source_system` | `STRING` | Source identifier (`mkcgp`, `agvantage`, `sharepoint`) |
| `_source_table` | `STRING` | Fully qualified source table name |
| `_pipeline_run_id` | `STRING` | Fabric Pipeline run ID for traceability |

---

### Silver — Canonical snake_case Rename

Silver is where source-native names are translated to canonical MKC names. **Every column rename happens here and only here.** Downstream layers inherit the Silver name without further renaming.

#### Rename rules

| Rule | Source Name | Silver Name |
|---|---|---|
| All lowercase, underscore-separated | `ITEMNMBR` | `item_number` |
| Spell out abbreviations | `TRXDATE` | `transaction_date` |
| Use consistent suffixes (see table below) | `CUSTNMBR` | `customer_id` |
| Disambiguate with entity prefix when joining | `NAME` (from customer) | `customer_name` |
| Add `_source_company` discriminator on unions | — | `_source_company STRING` (`mkcgp`, `mwfgp`) |

#### Standard column suffixes

| Suffix | Meaning | Example |
|---|---|---|
| `_id` | Natural / business key from source | `customer_id`, `vendor_id`, `item_code` |
| `_key` | Surrogate integer key (added at Gold) | `customer_key`, `date_key` |
| `_date` | Calendar date (`DATE` type) | `transaction_date`, `due_date` |
| `_at` | Timestamp (`TIMESTAMP` type) | `created_at`, `updated_at` |
| `_amount` | Monetary value | `invoice_amount`, `open_amount` |
| `_qty` or `_quantity` | Unit count | `quantity_bushels`, `order_quantity` |
| `_name` | Human-readable label | `customer_name`, `location_name` |
| `_type` | Category/enum | `transaction_type`, `movement_type` |
| `_flag` | Boolean indicator | `is_active_flag`, `is_intercompany_flag` |
| `_pct` | Percentage (0–100 scale) | `margin_pct`, `discount_pct` |

#### Silver table names

Silver tables use **PascalCase** entity names that reflect the business concept, not the source table:

| Bronze source | Silver entity |
|---|---|
| `mkcgp_sop10100` | `GrainSaleTransaction` |
| `mkcgp_iv30300` | `InventoryMovement` |
| `mkcgp_rm00101` | `CustomerMaster` |
| `mkcgp_sy01400` | `VendorMaster` |
| `mkcgp_gl10000` | `GLTransaction` |
| `agvantage_field_applications` | `FieldApplication` |

---

### Gold — Surrogate Keys + PascalCase Tables

Gold inherits Silver's `snake_case` column names unchanged. The only additions are:

- **Surrogate keys** (`{entity}_key INTEGER`) generated with `ROW_NUMBER()` or a sequence
- **Derived/aggregated columns** following the same `snake_case` rules as Silver
- **Table names** use `Fact{Subject}` / `Dim{Entity}` PascalCase

#### Surrogate key pattern

```python
# Gold dimension load — add surrogate key
from pyspark.sql import functions as F
from pyspark.sql.window import Window

dim_df = silver_df.withColumn(
    "customer_key",
    F.row_number().over(Window.orderBy("customer_id"))
)
```

#### Fact table column order convention

Fact tables should follow this column order for consistency:

1. Surrogate keys (`date_key`, `location_key`, …)
2. Natural/degenerate keys (`transaction_id`, `order_number`)
3. Measures / numeric columns (`total_bushels`, `amount_usd`)
4. Audit columns (`_loaded_at`)

---

### Semantic Model — Inherit + Rename for Readability

DirectLake semantic models inherit Gold column names. Rename only when the technical name would confuse business users in report field lists:

| Gold column | Semantic Model column | Rename justified? |
|---|---|---|
| `quantity_bushels` | `Quantity (Bushels)` | Yes — unit clarifies meaning |
| `amount_usd` | `Amount (USD)` | Yes — currency clarifies meaning |
| `date_key` | *(hidden — use `full_date`)* | Yes — surrogate key hidden |
| `customer_id` | `Customer ID` | Optional — usually kept as-is |
| `transaction_type` | `Transaction Type` | Title Case rename in model |

**Rule of thumb:** hide surrogate `_key` columns; rename units/currencies for clarity; leave natural IDs and descriptive columns as-is.

---

### Cross-Layer Column Traceability Example

The table below traces a single business value — grain sale price — from the GP source to a DAX measure:

| Layer | Object | Column Name | Notes |
|---|---|---|---|
| Source (GP) | `SOP10100` | `UNITPRCE` | Source abbreviated name |
| Bronze | `mkcgp_sop10100` | `UNITPRCE` | Mirrored verbatim |
| Silver | `GrainSaleTransaction` | `price_per_unit` | Renamed at Silver transform |
| Gold | `FactGrainSales` | `price_per_unit` | Inherited unchanged |
| Semantic Model | `FactGrainSales` | `Price per Unit` | Title Case for field list |
| DAX Measure | — | `[Avg Grain Price]` | Aggregation over `price_per_unit` |

---

## Schema Registry

### What It Is

`schema_registry.yml` is the machine-readable, version-controlled source of truth for every Bronze→Silver column rename. It lives in the repository root alongside the notebooks and is reviewed in every PR that touches source table mappings.

```
MKC PowerBI Inventory/
├── schema_registry.yml   ← single source of truth for column renames
├── validate_schema.py    ← offline + online validator
└── ...
```

### Why It Exists

The three-layer contract above is *aspirational* unless it is enforced. Without a registry:

- A developer can rename `UNITPRCE` to `unit_price` in Dev and `price_unit` in Prod — the report breaks silently.
- No reviewer can tell at a glance whether a new Silver column follows the suffix rules.
- Drift between environments is invisible until a semantic model refresh fails.

The registry makes drift structurally impossible: both Dev and Prod deploy from the same branch, so the `schema_registry.yml` they read is identical.

### Registry Structure

Each entry maps a Bronze source table to its Silver entity and lists every column rename:

```yaml
tables:
  mkcgp_sop10100:
    source_db: mkcgp
    source_table: SOP10100
    silver_entity: GrainSaleTransaction
    columns:
      SOPNUMBE: { silver: transaction_number, type: STRING,        description: "Sales order number" }
      CUSTNMBR: { silver: customer_id,        type: STRING,        description: "Customer ID (FK DimCustomer)" }
      UNITPRCE: { silver: price_per_unit,     type: DECIMAL(18,4), description: "Unit price in USD" }
      TRXDATE:  { silver: transaction_date,   type: DATE,          description: "Transaction date" }
```

Audit columns (`_ingested_at`, `_source_system`, `_source_table`, `_pipeline_run_id`) are **not listed** — they are added automatically by the Bronze ingest template.

### Onboarding a New Source Table

1. Add an entry to `schema_registry.yml` with all source→silver column mappings.
2. Run the validator locally to confirm no naming violations:
   ```bash
   python validate_schema.py --table mkcgp_new_table
   ```
3. Write the Silver notebook using **only** the registered Silver column names.
4. Open a PR — CI runs `validate_schema.py` automatically and fails if any rule is broken.

### Running the Validator

```bash
# Validate all tables (offline — no credentials needed)
python validate_schema.py

# Validate a single table
python validate_schema.py --table mkcgp_sop10100

# Online mode: compare registry against actual Delta schemas in OneLake
python validate_schema.py --live --env dev
python validate_schema.py --live --env prod --workspace MKC-Silver-Prod
```

### What CI Checks

The offline validator (run on every PR) enforces:

| Rule | Example violation |
|---|---|
| Silver names must be `snake_case` | `CustomerName` instead of `customer_name` |
| Silver names must end with a recognised suffix | `price_unit` (no valid suffix) |
| No duplicate Silver name within the same table | Two source columns mapped to `transaction_date` |
| Every column entry must have a `type` field | Missing `type:` in YAML |

See the [CI/CD page](cicd.md) for the pipeline step that runs this check.

---

## Notebook Parameter Cells

Parameters injected by CI/CD use `SCREAMING_SNAKE_CASE`:

```python
# parameters  ← Fabric "Parameter Cell" tag required
ENV        = "dev"          # overridden by CI/CD to "prod"
WORKSPACE  = f"MKC-Bronze-{ENV.capitalize()}"
LAYER      = "bronze"
SOURCE_DB  = "mkcgp"
SOURCE_TABLE = "sop10100"
```

Local/derived variables inside the notebook use `snake_case`:

```python
bronze_path = f"abfss://{WORKSPACE}@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Tables/{SOURCE_DB}_{SOURCE_TABLE}"
watermark_col = "rowversion"
```

---

## OneLake Path Convention

OneLake paths follow the workspace naming pattern so a single `ENV` parameter covers all layers:

```
abfss://MKC-{Layer}-{ENV}@onelake.dfs.fabric.microsoft.com/{Layer}.Lakehouse/Tables/{table_name}
```

**Examples:**

```
abfss://MKC-Bronze-Prod@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Tables/mkcgp_sop10100
abfss://MKC-Silver-Dev@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables/GrainSaleTransaction
abfss://MKC-Gold-Prod@onelake.dfs.fabric.microsoft.com/Gold.Lakehouse/Tables/FactGrainSales
```

---

## Identity & Access Names

See [Entra ID & RBAC](../06_governance/entra-rbac.md) for the full Entra group and service principal naming conventions. Summary:

| Pattern | Example |
|---|---|
| Workspace member groups | `sg-fabric-{domain}-members` |
| Workspace viewer groups | `sg-fabric-{domain}-viewers` |
| RLS filter groups | `sg-pbi-{domain}-{filter}` |
| CI/CD service principals | `sp-fabric-cicd` |
| Purview scanner SP | `sp-fabric-purview` |

---

## Quick Reference

| Artifact | Pattern | Case | Example |
|---|---|---|---|
| Workspace | `MKC-{Layer}-{Env}` | PascalCase | `MKC-Bronze-Prod` |
| Lakehouse | `{Layer}.Lakehouse` | PascalCase | `Bronze.Lakehouse` |
| Notebook | `nb-{layer}-{action}-{subject}` | kebab-case | `nb-silver-transform-grain-sale-transaction` |
| Pipeline | `pl-{layer}-{subject}` | kebab-case | `pl-bronze-gp-daily-ingest` |
| Dataflow Gen2 | `dfw-{source}-{subject}` | kebab-case | `dfw-agvantage-field-applications` |
| Semantic Model | `{Domain}.SemanticModel` | PascalCase | `Sales.SemanticModel` |
| Report | `{Subject} {Type}` | Title Case | `Grain Sales Dashboard` |
| DAX Measure | `[{Aggregation} {Subject}]` | Title Case | `[Total Grain Revenue]` |
| Bronze table | `{source_db}_{source_table}` | snake_case | `mkcgp_sop10100` |
| Silver table | `{BusinessEntity}` | PascalCase | `GrainSaleTransaction` |
| Gold Fact table | `Fact{Subject}` | PascalCase | `FactGrainSales` |
| Gold Dim table | `Dim{Entity}` | PascalCase | `DimCustomer` |
| Column (Silver/Gold) | `{entity}_{suffix}` | snake_case | `customer_id`, `transaction_date` |
| Notebook parameter | `SCREAMING_SNAKE_CASE` | UPPER | `SOURCE_TABLE`, `ENV` |
| Notebook variable | `snake_case` | lower | `bronze_path`, `watermark_col` |
