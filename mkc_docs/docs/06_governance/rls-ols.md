# Row-Level Security & Object-Level Security

Semantic models are Fabric workspace items (`.pbidataset`) governed independently of the raw Delta files. Microsoft Entra ID groups provide the identity source for both RLS and OLS roles.

## RLS & OLS Summary by Semantic Model

| Semantic Model | RLS Rule | OLS (hidden columns/tables) | Entra Group Convention |
|----------------|---------|----------------------------|----------------------|
| **Sales** | Filter rows by `Region` + `Division` based on `USERPRINCIPALNAME()` → role mapping | `CostMargin` column hidden; visible to `sg-pbi-finance-*` only | `sg-pbi-sales-{region}` |
| **Financial** | Filter rows by `CostCenter` + `Company` | `SalaryAmt`, `HourlyRate` hidden; visible to `sg-pbi-hr-*` only | `sg-pbi-finance-{costcenter}` |
| **Operations** | Filter rows by `Location` + `Division` | `CreditLimit` hidden; visible to `sg-pbi-finance-*` only | `sg-pbi-ops-{location}` |

## RLS Implementation

RLS filters are defined in the semantic model's **role editor** (Fabric UI or Tabular Editor). Each role has a DAX table filter expression:

```dax
-- Sales semantic model: Region role
-- Applied to DimLocation table

[Region] = LOOKUPVALUE(
    DimEmployee[Region],
    DimEmployee[Email], USERPRINCIPALNAME()
)
```

This expression:
1. Takes the current user's email via `USERPRINCIPALNAME()`
2. Looks up their assigned `Region` in the `DimEmployee` table
3. Filters `DimLocation` to only show rows where `Region` matches

Because `DimLocation` is related to all fact tables, this single filter propagates through the entire star schema — the user sees only their region's data in every report.

### RLS Role Definitions

=== "Sales Model"
    ```dax
    -- Table: DimLocation
    -- Role filter expression (applied to Region column):
    [Region] = LOOKUPVALUE(
        DimEmployee[Region],
        DimEmployee[Email], USERPRINCIPALNAME()
    )

    -- Additionally, filter by Division for division managers:
    [Division] = LOOKUPVALUE(
        DimEmployee[Division],
        DimEmployee[Email], USERPRINCIPALNAME()
    )
    ```

=== "Financial Model"
    ```dax
    -- Table: DimCostCenter
    -- Role filter expression:
    [CostCenter] = LOOKUPVALUE(
        DimEmployee[CostCenter],
        DimEmployee[Email], USERPRINCIPALNAME()
    )
    ||
    -- Company-level filter for CFO role:
    USERPRINCIPALNAME() IN
        VALUES('sg-pbi-finance-all'[Email])
    ```

=== "Operations Model"
    ```dax
    -- Table: DimLocation
    -- Role filter expression:
    [Location] = LOOKUPVALUE(
        DimEmployee[Location],
        DimEmployee[Email], USERPRINCIPALNAME()
    )
    ```

### Testing RLS

Test RLS roles in Power BI Desktop or Tabular Editor before publishing:

```
Power BI Desktop → Modeling → View As Roles → Select role → Verify filtered data
```

Or programmatically via REST API:
```http
POST /datasets/{id}/GenerateToken
Body: { "identities": [{ "username": "test.user@mkcgrain.com", "roles": ["Region_NorthKansas"], "datasets": ["{id}"] }] }
```

## OLS Implementation

Object-Level Security hides **columns or entire tables** from users who don't have the required role. OLS is configured in the semantic model's role editor (Tabular Editor or Fabric UI).

### OLS Definitions

| Model | Column/Table | Hidden From | Visible To |
|-------|-------------|-------------|-----------|
| Sales | `FactGrainSales[CostMargin]` | Default / Sales roles | `sg-pbi-finance-*` |
| Financial | `FactPayroll[SalaryAmt]` | Default / Finance roles | `sg-pbi-hr-*` |
| Financial | `DimEmployee[HourlyRate]` | Default / Finance roles | `sg-pbi-hr-*` |
| Operations | `DimCustomer[CreditLimit]` | Default / Ops roles | `sg-pbi-finance-*` |

### Setting OLS in Tabular Editor

```csharp
// Tabular Editor C# script to set OLS
var role = Model.Roles["Sales-Default"];
var column = Model.Tables["FactGrainSales"].Columns["CostMargin"];
role.ColumnPermissions[column] = MetadataPermission.None;
// MetadataPermission.None = column is hidden and throws error if queried
// MetadataPermission.Read = visible (default)
```

## Data Agents and RLS/OLS

Because Data Agent queries execute under the **user's own Entra identity**, RLS and OLS rules apply automatically:

- A sales rep asking "What is our margin?" will get an error if `CostMargin` is OLS-hidden from their role
- A regional manager asking "Show grain sales by location" will only see locations in their region (RLS)
- No special Data Agent configuration is needed — the semantic model enforces it transparently
