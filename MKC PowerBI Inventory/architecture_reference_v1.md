# MKC Microsoft Fabric Architecture — Reference Guide

> This document is a companion to `mkc_fabric_architecture.png / .svg`.
> It explains every component visible in the diagram, the design decisions behind each layer, and the security model for data governance.

---

## 1. Architecture Overview

MKC's data platform is built on a **Bronze → Silver → Gold → Semantic Model** medallion architecture hosted entirely on **Microsoft Fabric** with **OneLake** (ADLS Gen2) as the single storage layer. On-premises SQL Servers (mkc-sqlcall, CARDTROLSVR-01) connect via an On-Premises Data Gateway. External SaaS systems (AgVantage, AgWorld, Dynamics CRM, SharePoint) connect via Dataflow Gen2 REST connectors. All data is stored as **Delta Parquet** (open format) to prevent vendor lock-in. A governed **AI Platform** (Azure OpenAI behind a Private Endpoint and APIM gateway) powers Data Agents in each BI workspace and Fabric Copilot in the Data Science layer.

---

## 2. Medallion Layer Strategy

| Layer | Fabric Component | Storage Format | Purpose | Key Design Decision |
|-------|-----------------|---------------|---------|-------------------|
| **Bronze** | Lakehouse | Delta Parquet, append-only | Raw replica of all sources, 7-year retention | Never modify Bronze; always re-processable from source |
| **Silver** | Lakehouse | Delta Parquet, MERGE INTO | Cleaned, deduped, typed, schema-enforced | Union MKCGP + MWFGP tables here, not at source |
| **Gold** | Lakehouse + Fabric Warehouse | Delta Parquet + External Tables | Business aggregates, KPIs, open access | External tables = zero-copy; Gold Delta readable via ADLS Gen2 REST by any engine |
| **Semantic Models** | Fabric Workspace Items (`.pbidataset`) | Stored in OneLake workspace folder | Star schema with RLS/OLS for BI | DirectLake mode: reads Delta directly from Gold — no import copy, sub-second refresh |
| **BI Reports** | Power BI Workspaces | In-memory / DirectLake | Self-service dashboards for 22 workspaces | 170 reports; consumers need no Pro license inside F-SKU capacity |
| **Data Agents** | Fabric AI items | In-memory NL session | Natural-language querying per workspace | Governed by the same Entra RBAC as their parent semantic model |

---

## 3. Component → `diagrams` Library Icon Mapping

> Icon choices use the closest available Azure `diagrams` library class. Fabric has no dedicated icons; Azure equivalents are used with descriptive labels.

| Architecture Component | `diagrams` Class | Module | Rationale |
|------------------------|-----------------|--------|-----------|
| On-prem SQL Server | `SQLServers` | `azure.database` | Direct icon match |
| Azure SQL MI | `SQLManagedInstances` | `azure.database` | Direct icon match |
| **On-Premises Data Gateway** | **`OnPremisesDataGateways`** | **`azure.network`** | Dedicated gateway icon; replaces generic VM |
| Fabric Pipelines | `DataFactories` | `azure.analytics` | ADF is the underlying engine for Fabric Pipelines |
| Dataflow Gen2 (Power Query) | `DataFactories` *(labelled)* | `azure.integration` | Same Power Query engine; labelled to differentiate |
| Eventstream (real-time) | `StreamAnalyticsJobs` | `azure.analytics` | Stream processing analogy |
| Bronze Lakehouse | `BlobStorage` | `azure.storage` | Raw / blob-like append-only storage |
| Silver / Gold Lakehouses | `DataLakeStorage` | `azure.storage` | Structured Delta lake tier |
| Fabric Warehouse | `SQLDatawarehouse` | `azure.database` | T-SQL endpoint analogy |
| **Semantic Model** | **`AnalysisServices`** | **`azure.analytics`** | Semantic models evolved from SSAS Tabular; this icon correctly differentiates them from Power BI report nodes |
| Power BI Workspace (reports) | `PowerBiEmbedded` | `azure.analytics` | Report / dashboard visual |
| **Data Agent** | **`BotServices`** | **`azure.aimachinelearning`** | AI agent / conversational bot analogy |
| ML Notebooks / Experiments | `MachineLearning` | `azure.aimachinelearning` | ML workload |
| Feature Store | `DataLakeStorage` *(labelled)* | `azure.storage` | Delta-stored feature vectors |
| Model Serving | `FunctionApps` | `azure.compute` | Serverless REST endpoint for inference |
| Fabric Copilot | `AzureOpenai` | `azure.aimachinelearning` | Copilot is powered by Azure OpenAI |
| **Azure OpenAI Service** | **`AzureOpenai`** | **`azure.aimachinelearning`** | Enterprise-grade hosted GPT models |
| **Private Endpoint** | **`PrivateEndpoint`** | **`azure.network`** | VNet-secured access to Azure OpenAI |
| LLM Gateway (APIM) | `APIManagementServices` | `azure.integration` | Rate-limiting, token metering, audit log |
| Microsoft Purview | `DataLakeAnalytics` *(labelled)* | `azure.analytics` | Data catalog, lineage, sensitivity labels |
| Azure Monitor | `Monitor` | `azure.managementgovernance` | Fabric capacity metrics, pipeline alerts |
| Log Analytics | `LogAnalyticsWorkspaces` | `azure.managementgovernance` | Audit log storage and query |
| Key Vault | `KeyVaults` | `azure.security` | Connection strings, SPN credentials |
| Microsoft Entra ID | `AzureActiveDirectory` | `azure.identity` | Workspace RBAC, RLS/OLS identity provider |
| AgVantage / AgWorld SaaS | `SoftwareAsAService` | `azure.integration` | External SaaS REST connector |
| Dynamics CRM | `APIManagementServices` | `azure.integration` | REST / Dataverse OData v4 API |
| SharePoint Lists | `StorageAccounts` | `azure.storage` | SP.Lists as structured list storage |

---

## 4. Star Schema Tables

### 4.1 Shared Dimensions (Silver → Gold, reused across all semantic models)

| Dimension | Source DB | Source Table / API | Description |
|-----------|----------|--------------------|-------------|
| `DimDate` | Calculated | — | Standard date/calendar with fiscal periods |
| `DimLocation` | MKCGP | `LocationsMaster` | Site / elevator / location hierarchy |
| `DimItem` | MKCGP | `IV00101` | Item / product / commodity master |
| `DimCustomer` | MKCGP | `RM00101` | Customer account master |
| `DimVendor` | MKCGP | `SY01400` | Vendor / supplier master |
| `DimEmployee` | HAVEN | HR tables | Employee master, department, role |
| `DimField` | AgWorld | Field API | Agricultural field geometry + attributes |
| `DimProducer` | AgVantage / AgWorld | Producer API | Grower / producer master |

### 4.2 Fact Tables

| Fact Table | Source DB(s) | Semantic Model | Grain | Description |
|------------|-------------|----------------|-------|-------------|
| `FactGrainSales` | Agtrax_BI + MKCGP | Sales | Transaction line | Grain purchase / sale transactions |
| `FactFeedSales` | MKCGP | Sales | Transaction line | Feed and agricultural supply sales |
| `FactAgronomy` | AgVantage + AgWorld | Sales | Field application | Field services, crop application records |
| `FactGLTransaction` | MKCGP GL | Financial | Journal line | General ledger entries |
| `FactAPTransaction` | MKCGP AP | Financial | Invoice line | Accounts payable invoices and payments |
| `FactPayroll` | HAVEN | Financial | Pay run line | Payroll disbursements by employee |
| `FactInventory` | MKCGP (`IV30300`) | Operations | Movement | Inventory receipts, adjustments, transfers |
| `FactOrder` | AgVend | Operations | Order line | Vendor / purchase orders |
| `FactARTransaction` | MKCGP AR | Operations | Invoice line | Accounts receivable invoices and receipts |

---

## 5. BI Workspace Organization (22 Workspaces)

| Group | Workspaces | Reports | Primary Semantic Model | Data Agent |
|-------|-----------|---------|----------------------|-----------|
| Operational | Sales (36), OMS (11), Operations (9) | 56 | Sales | Data Agent (Operational) |
| Analytics — Executive / Portal | Executive (14), Data Portal (15) | 29 | Sales + Financial + Operations | Data Agent (Analytics) |
| Analytics — Financial | Financial Reporting (6), Financial Processing (6) | 12 | Financial | Data Agent (Financial) |
| Domain | Administration (24), Producer Ag (19), HR (4), Digital Transformation (6) | 53 | Financial + Operations | Data Agent (Domain) |
| External / SaaS | edX (5), KnowBe4 (4), Intune (2) | 11 | Standalone | — |

---

## 6. Data Agent Scope

Fabric Data Agents are natural-language query interfaces scoped to specific semantic models within their workspace. Each agent translates user questions into DAX or SQL queries via Azure OpenAI, executes them against the semantic model, and returns formatted answers.

| Agent | BI Sub-cluster | Semantic Models Queried | Example NL Questions |
|-------|---------------|------------------------|----------------------|
| Data Agent (Operational) | Operational | Sales | *"What were grain sales in Q3 by location?"* |
| Data Agent (Analytics) | Analytics — Executive / Portal | Sales + Financial + Operations | *"Show margin trend vs budget by division this fiscal year"* |
| Data Agent (Financial) | Analytics — Financial | Financial | *"Which AP invoices are overdue by cost center?"* |
| Data Agent (Domain) | Domain | Financial + Operations | *"What fields are enrolled per producer this planting season?"* |

**Data Agent query flow:**
```
User NL question
    → Data Agent (Fabric AI item, workspace-scoped)
    → Azure APIM (rate limit, auth, token metering)
    → Azure OpenAI Private Endpoint
    → Azure OpenAI Service (GPT-4o: NL → DAX/SQL)
    ← DAX/SQL query returned to agent
    → Semantic Model / Fabric Warehouse (query execution)
    ← Result set returned to user
```

---

## 7. Semantic Model Security: RLS & OLS

Semantic models are Fabric workspace items (`.pbidataset`), stored in OneLake but governed independently of the raw Delta files. Microsoft Entra ID groups provide the identity source for both RLS and OLS roles.

| Semantic Model | RLS Rule | OLS (hidden columns/tables) | Entra Group Convention |
|----------------|---------|----------------------------|----------------------|
| **Sales** | Filter rows by `Region` + `Division` based on `USERPRINCIPALNAME()` → role mapping | `CostMargin` column hidden; visible to `sg-pbi-finance-*` only | `sg-pbi-sales-{region}` |
| **Financial** | Filter rows by `CostCenter` + `Company` | `SalaryAmt`, `HourlyRate` hidden; visible to `sg-pbi-hr-*` only | `sg-pbi-finance-{costcenter}` |
| **Operations** | Filter rows by `Location` + `Division` | `CreditLimit` hidden; visible to `sg-pbi-finance-*` only | `sg-pbi-ops-{location}` |

**RLS implementation pattern (DAX):**
```dax
-- Example: Sales semantic model, Region role
[Region] = LOOKUPVALUE(
    DimEmployee[Region],
    DimEmployee[Email], USERPRINCIPALNAME()
)
```

**OLS implementation:** Object-Level Security is set in the semantic model's role editor (Tabular Editor or Fabric UI) — columns or entire tables are set to `None` permission for roles that should not see them.

---

## 8. Enterprise LLM Strategy

Azure OpenAI Service is selected as the enterprise LLM for all AI features (Data Agents, Fabric Copilot, ML feature engineering).

| Criterion | Azure OpenAI Service | Decision |
|-----------|---------------------|----------|
| **Data residency** | In-tenant; same Azure region as Fabric | MKC data never leaves the tenant boundary |
| **Authentication** | Managed Identity (no API keys in code) | Zero-secret auth; no key rotation risk |
| **Network security** | Private Endpoint + VNet integration | All traffic on Microsoft backbone; no public internet |
| **Compliance** | SOC2 Type II, HIPAA, ISO27001, GDPR | Meets agricultural co-op data handling requirements |
| **No model training on data** | Confirmed via Data Protection Addendum | Microsoft does not use customer prompts to train models |
| **Governance** | Azure APIM as LLM Gateway | Per-workspace token quotas, full audit log, chargeback by workspace |
| **Model availability** | GPT-4o, GPT-4.1, text-embedding-3-large | State-of-the-art models with Microsoft SLA |
| **Alternatives considered** | Azure AI Foundry model hub, on-prem Ollama, public OpenAI API | Azure OpenAI wins on compliance + native Fabric/Entra integration |

**AI Platform security layers:**
```
Data Agent / Copilot / ML Notebook
    ↓ HTTPS (Managed Identity token)
Azure API Management (LLM Gateway)
    · Rate limit: 50K tokens/min per workspace
    · Authentication: Managed Identity validation
    · Audit log → Log Analytics workspace
    ↓ Internal VNet
Private Endpoint (no public IP)
    ↓ Microsoft backbone
Azure OpenAI Service
    · No public internet access
    · Content filters enabled
    · Customer data not used for training
```

---

## 9. Vendor Lock-in Avoidance Strategy

| Risk Area | Lock-in Scenario | Mitigation |
|-----------|-----------------|-----------|
| **Storage** | Fabric-proprietary format makes data inaccessible without Fabric license | All data stored as **Delta Parquet** on ADLS Gen2 (OneLake). Readable by Databricks, DuckDB, Apache Spark, Trino, Azure Synapse — no Fabric license needed |
| **Warehousing** | T-SQL queries only work inside Fabric Warehouse | Gold Lakehouse data exposed as Fabric Warehouse **external tables** (no data copy). The underlying Delta files remain independently accessible |
| **BI** | Power BI is the only consumer of semantic models | Gold Warehouse T-SQL views can be queried by Tableau, Looker, Excel, or any JDBC/ODBC client |
| **Ingestion** | Fabric Pipelines use proprietary connectors | Standard connector ecosystem (JDBC, REST, OData). Equivalent pipelines exist in Azure Data Factory, dbt, Airbyte, Apache Airflow |
| **LLM** | Azure OpenAI API is the only LLM endpoint | Azure OpenAI API is OpenAI-compatible (`/v1/chat/completions`). Switch to other GPT-compatible endpoints (Azure AI Foundry, open-source via Ollama) with one config change |
| **Feature store** | ML features in a proprietary store | Features stored as Delta tables in OneLake (Gold layer). Portable to any Delta-compatible ML platform |
| **Semantic models** | `.pbidataset` items are Fabric-native | DirectLake reads standard Delta Parquet files. If Fabric is replaced, the underlying Gold Delta data is fully available to any analytical engine |

---

## 10. Transformation Engine Decisions

| Step | Tool Chosen | Alternative | Why This Tool |
|------|------------|-------------|--------------|
| **Bronze → Silver** | Fabric Notebooks (PySpark `MERGE INTO`) | Dataflow Gen2 | Dataflow Gen2 lacks `MERGE INTO` (upsert). Hits ~1 GB memory limit on large transactional tables. Notebooks scale via Spark clusters with no memory ceiling |
| **Silver → Gold** | Fabric Notebooks (Spark SQL) | Dataflow Gen2 | Cross-source joins (MKCGP GP tables + AgVantage API data) exceed Dataflow Gen2 single-source scope. Spark SQL supports multi-source joins natively |
| **API / SP → Bronze** | Dataflow Gen2 (Power Query) | Notebooks | Small payloads (<100 MB). MKC already has 37 existing Power Query dataflows. Native scheduling, no cluster spin-up latency |
| **Gold → Semantic Model** | DirectLake (zero-ETL) | Import mode | DirectLake reads Delta files directly from OneLake. No data import copy, sub-second model refresh, no storage duplication |

---

## 11. Ingestion Strategy by Source Type

| Source | Tool | Auth Method | Frequency | Notes |
|--------|------|------------|-----------|-------|
| mkc-sqlcall (primary on-prem) | Fabric Pipeline + On-Premises Data Gateway | SQL Auth via Key Vault secret | Hourly CDC / nightly full | `rowversion` or `DEX_ROW_ID` as watermark |
| CARDTROLSVR-01\\SQLEXPRESS | Fabric Pipeline + Data Gateway | SQL Auth | Nightly full | Low volume; full load acceptable |
| Azure SQL MI (optional) | Fabric Pipeline (direct, no gateway) | Managed Identity | Hourly CDC | If on-prem SQL is migrated to cloud |
| AgVantage (Grain SaaS) | Dataflow Gen2 (REST) | OAuth2 client credentials | Daily | Price feeds, contract data |
| AgWorld (Agronomy SaaS) | Dataflow Gen2 (REST) | OAuth2 | Daily | Field records, application logs |
| Dynamics CRM | Dataflow Gen2 (Dataverse connector) | Service Principal | Daily | OData v4; entity-level incremental |
| SharePoint Lists | Dataflow Gen2 (SP.Lists connector) | Service Principal | Daily | HR admin lists; low volume |
| Grain prices / IoT (real-time) | Eventstream | Event Hub / MQTT | Real-time streaming | Streamed directly to Bronze Delta |

---

## 12. Diagram Color Legend

| Color | Cluster / Edge | Represents |
|-------|---------------|-----------|
| Blue `#4E79A7` | Source Systems | On-premises SQL and SaaS sources |
| Green `#59A14F` | Ingestion Layer | Gateway, Pipelines, Dataflow Gen2, Eventstream |
| Purple `#B07AA1` | Fabric Capacity / OneLake | The Fabric platform boundary |
| Orange `#F28E2B` | Bronze layer / Governance edges | Raw data; monitoring and governance |
| Grey `#cccccc` | Silver layer | Cleaned/conformed data |
| Gold `#FFD700` | Gold layer | Business aggregate data |
| Indigo `#B07AA1` (darker bg) | Semantic Models | Governed star schema models (RLS/OLS) |
| Red `#E15759` | BI Workspaces | Power BI dashboards and reports |
| Teal `#76B7B2` | Data Science & ML | ML notebooks, feature store, model serving |
| Emerald `#50C878` | AI Platform | Azure OpenAI, APIM, Private Endpoint |
| Yellow-brown `#F28E2B` | Governance & Security | Purview, Monitor, Key Vault, Entra ID |
