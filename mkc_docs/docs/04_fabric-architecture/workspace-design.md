# Workspace Design

## Fabric Capacity Model

Microsoft Fabric uses a **capacity unit (CU)** model. An F-SKU reserves a fixed pool of CUs that all workspaces in the capacity share. There are no per-user compute charges for Fabric workloads — only the flat capacity fee.

| F-SKU | CUs | Max Memory | Recommended Use | PAYG/mo |
|-------|-----|-----------|-----------------|---------|
| F8 | 8 | 16 GB | Dev / Test | ~$630 |
| F32 | 32 | 64 GB | Production (MKC recommended) | ~$4,194 |
| F64 | 64 | 128 GB | Large orgs or Copilot (F64+) | ~$8,388 |

> MKC recommended: **F32 (Prod) + F8 (Dev/Test)**. See [FinOps → SKU Reference](../07_finops/sku-reference.md) for full table.

## Workspace Topology

MKC organises workspaces by **layer** and **environment**:

```
MKC Fabric Tenant
│
├── Platform workspaces (Data Engineering)
│   ├── MKC-Bronze-Prod
│   ├── MKC-Silver-Prod
│   ├── MKC-Gold-Prod
│   └── MKC-SemanticModels-Prod
│
├── BI workspaces (per business domain)
│   ├── MKC-BI-Sales-Prod
│   ├── MKC-BI-OMS-Prod
│   ├── MKC-BI-Operations-Prod
│   ├── MKC-BI-Executive-Prod
│   ├── MKC-BI-DataPortal-Prod
│   ├── MKC-BI-FinancialReporting-Prod
│   ├── MKC-BI-FinancialProcessing-Prod
│   ├── MKC-BI-Administration-Prod
│   ├── MKC-BI-ProducerAg-Prod
│   ├── MKC-BI-HumanResources-Prod
│   ├── MKC-BI-DigitalTransformation-Prod
│   └── MKC-BI-Public-Prod
│
├── Data Science workspace
│   └── MKC-DataScience-Prod
│
└── Dev / Test workspaces (mirror of above, on F8)
    ├── MKC-Bronze-Dev / MKC-Bronze-Test
    └── ...
```

## Workspace RBAC

Each workspace has four standard roles. MKC maps Entra groups to roles:

| Role | Permissions | MKC Entra Group |
|------|-------------|----------------|
| **Admin** | Full control including Git | `sg-fabric-platform-admins` |
| **Member** | Publish content, manage items | `sg-fabric-{domain}-members` |
| **Contributor** | Create and edit items | `sg-fabric-{domain}-contributors` |
| **Viewer** | Read-only access to reports | `sg-fabric-{domain}-viewers` |

BI workspace viewers require **no Power BI Pro license** when on an F-SKU capacity.

## Fabric Capacity Assignment

All workspaces run within a single **F32** capacity pool. The capacity administrator can set per-workspace CU limits to prevent one workload starving others:

| Workspace Group | CU Allocation Guideline |
|----------------|------------------------|
| Platform (Bronze/Silver/Gold pipelines) | 12 CUs (burst up to 24) |
| Semantic Models | 8 CUs |
| BI Workspaces | 6 CUs (shared) |
| Data Science | 6 CUs |
| Dev capacity (F8) | Separate capacity, paused off-hours |

## DirectLake Semantic Model Configuration

Semantic models in DirectLake mode must point to Gold Lakehouse Delta tables:

1. In Fabric workspace, create a new **Semantic Model** item
2. Connect it to **MKC-Gold-Prod** Lakehouse
3. Select Delta tables: `FactGrainSales`, `DimDate`, `DimLocation`, etc.
4. Set mode to **DirectLake** (not Import, not DirectQuery)
5. Configure RLS/OLS roles (see [RLS & OLS](../06_governance/rls-ols.md))

!!! info "DirectLake Requirements"
    - Gold Delta tables must be in **Delta Lake V1** format (not V2 with deletion vectors, until Fabric fully supports it)
    - No unsupported DAX functions that require column-level fallback to DirectQuery
    - Run the Fabric **DirectLake analyser** tool to validate compatibility before deployment

---

## References

| Resource | Description |
|----------|-------------|
| [Fabric licenses and capacity](https://learn.microsoft.com/en-us/fabric/enterprise/licenses) | F-SKU tiers, capacity units, and feature availability by SKU |
| [Fabric workspace roles](https://learn.microsoft.com/en-us/fabric/get-started/roles-workspaces) | Admin, Member, Contributor, and Viewer permissions in Fabric workspaces |
| [Fabric capacity management](https://learn.microsoft.com/en-us/fabric/admin/capacity-settings) | Configuring, pausing, and monitoring F-SKU capacities in the Admin portal |
| [DirectLake analyser tool](https://learn.microsoft.com/en-us/fabric/get-started/direct-lake-overview#use-the-analyzer) | Validating Gold Delta table compatibility with DirectLake semantic models |
| [Microsoft Entra group management](https://learn.microsoft.com/en-us/entra/fundamentals/groups-view-azure-portal) | Creating and managing security groups for workspace RBAC assignment |
