# Source Inventory

Auto-generated from **Source Mapping** sheet of `MKC PowerBI Inventory (1).xlsx`.

!!! info "Coverage"
    **190 source connections** across **12 workspaces**

## Source Type Breakdown

| Source Type | Connections | % of Total |
|-------------|-------------|-----------|
| Dataflow | 104 | 54.7% |
| mkc-sqlcall | 52 | 27.4% |
| SharePointList | 20 | 10.5% |
| DataFlow | 8 | 4.2% |
| API | 3 | 1.6% |
| dataflow | 2 | 1.1% |
| tmadbserver.database.windows.net | 1 | 0.5% |

## SQL Server & Database Inventory

| Server | Databases |
|--------|-----------|
| `#REF!` | Agtrax_BI |
| `Sharepoint` | AgVend |

## Connections by Workspace

### 

**179 connections**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| 1099 Amount to Payments | mkc-sqlcall |  | haven | PM00204 |
| 1099 Amount to Payments | mkc-sqlcall |  | haven | PM30200 |
| 1099 Amount to Payments | mkc-sqlcall |  | haven | PM00200 |
| 1099 Amount to Payments | mkc-sqlcall |  | mkcgp | PM00204 |
| 1099 Amount to Payments | mkc-sqlcall |  | mkcgp | PM30200 |
| 1099 Amount to Payments | mkc-sqlcall |  | mkcgp | PM00200 |
| 1099 Amount to Payments | mkc-sqlcall |  | mwfgp | PM00204 |
| 1099 Amount to Payments | mkc-sqlcall |  | mwfgp | PM30200 |
| 1099 Amount to Payments | mkc-sqlcall |  | mwfgp | PM00200 |
| Applications Revenue | Dataflow |  | ITApps | DateDim |
| Applications Revenue | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Applications Revenue | Dataflow |  | MKCGP+MWFGP+HAVEN | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis,vFarmKanSalesDetailAnalysis |
| Applications Revenue | Dataflow |  | ITAPPS | LocationsMaster |
| Billing Dashboard | Dataflow |  | AgWorld | vActivitySummary,vMWFActivitySummary |
| Billing Dashboard | Dataflow |  | ITAPPS | LocationsMaster |
| Billing Dashboard | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Billing Dashboard | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > SOP10100 |
| Billing Dashboard | Dataflow |  | Agtrax_BI | DateDim |
| Billing Dashboard | Dataflow |  | dynamics | SY01400 |
| Billing Dashboard | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IRASShipInvHDRWORK |
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |
| CICM - PPM - Project Portfolio Management | Dataflow |  | Agtrax_BI | DateDim |
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |
| CICM - PPM - Project Portfolio Management | Dataflow |  | dynamics | SLB21100 |
| CICM - PPM - Project Portfolio Management | Dataflow |  | dynamics | SY01400 |
| Claim Reports | SharePointList |  |  |  |
| Claims Report | SharePointList |  |  |  |
| Credit Holds | mkc-sqlcall |  | mkcgp | RM20101 |
| Credit Holds | mkc-sqlcall |  | mkcgp | RM00101 |
| Credit Holds | mkc-sqlcall |  | mkcgp | RM40201 |
| Credit Holds | mkc-sqlcall |  | mkcgp | vmkcCreditMgmtBalHold |
| Credit Holds | mkc-sqlcall |  | mwfgp | RM20101 |
| Credit Holds | mkc-sqlcall |  | mwfgp | RM00101 |
| Credit Holds | mkc-sqlcall |  | mwfgp | RM40201 |
| Credit Holds | mkc-sqlcall |  | mwfgp | vmwfCreditMgmtBalHold |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > RM00101 |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > RM20201 |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > RM00101 |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > SY01200 |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > RM20101 |
| Customer Master Summary | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM20000 |
| Dispatch | Dataflow |  | Agtrax_BI | DispatchContracts |
| Dispatch | Dataflow |  | Agtrax_BI | IV_BRANCH_MASTER |
| Dispatch | Dataflow |  |  | Sharepoint |
| Dispatch | SharePointList |  |  |  |
| Dispatch | SharePointList |  |  |  |
| Energy Department Orders | mkc-sqlcall |  | mkcgp | IV00101 |
| Energy Department Orders | mkc-sqlcall |  | mkcgp | IV00101 |
| Energy Scorecard | Dataflow |  | AgVend | MKC_CRM_AccountRep |
| Energy Scorecard | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Energy Scorecard | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Executive Sales | Dataflow |  | ITApps | DateDim |
| Executive Sales | Dataflow |  | AgVend | AgVend > MKC_CRM_AccountRep ,MWF_CRM_AccountRep |
| Executive Sales | Dataflow |  | MKCGP | IRPGvMembers |
| Executive Sales | Dataflow |  | MKCGP+MWFGP+HAVEN | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis,vFarmKanSalesDetailAnalysis |
| Feed Scorecard | Dataflow |  | AgVend | AgVend > MKC_CRM_AccountRep ,MWF_CRM_AccountRep |
| Feed Scorecard | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Feed Scorecard | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Fertilizer Prepay | mkc-sqlcall |  | agtrax_bi | DateDim |
| Fertilizer Prepay | mkc-sqlcall |  | mkcgp | RM00101 |
| Fertilizer Prepay | mkc-sqlcall |  | mkcgp | IV00101 |
| Fertilizer Prepay | mkc-sqlcall |  | mkcgp | IV00102 |
| Fertilizer Prepay | mkc-sqlcall |  | mkcgp | IRASPrepayLINEOPEN |
| Fertilizer Prepay | mkc-sqlcall |  | mkcgp | vmkcSalesDetailAnalysis |
| Fertilizer Prepay | mkc-sqlcall |  | mwfgp | RM00101 |
| Fertilizer Prepay | mkc-sqlcall |  | mwfgp | IV00101 |
| Fertilizer Prepay | mkc-sqlcall |  | mwfgp | IV00102 |
| Fertilizer Prepay | mkc-sqlcall |  | mwfgp | IRASPrepayLINEOPEN |
| Fertilizer Prepay | mkc-sqlcall |  | mwfgp | vmwfSalesDetailAnalysis |
| Financials | Dataflow |  | MKCGP | IRPGvMemberStockSummaryRpt |
| Financials | Dataflow |  | MKCGP | IRPGvMemberStockSummaryRpt |
| Financials | Dataflow |  | MKCGP | IRPGvMembers |
| Financials | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM00200 |
| Financials | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM00201 |
| Financials | Dataflow |  | MKCGP+MWFGP | HAVEN > RM00101 |
| Financials | Dataflow |  | MKCGP+MWFGP+HAVEN | MKCGP+MWFGP+HAVEN> RM00103 |
| Financials | Dataflow |  | ITApps | DateDim |
| Financials | Dataflow |  | MKCGP | AccountSummary |
| Fuel Dashboard | Dataflow |  | eeeHomeOffice | vw_MKC_ExportSource" |
| Fuel Dashboard | Dataflow |  | MKCGP | IRCSBranchMSTR |
| Fuel Dashboard | Dataflow |  | MKCGP | vmkcSalesDetailAnalysis |
| Fuel Dashboard | Dataflow |  | DynamicsGPWarehouse | DtnAllPrices |
| Fuel Dashboard | Dataflow |  | MKCGP | IRASXRefItemLINE |
| GL Reconciliation | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > AccountSummary |
| Grain Receipts | Dataflow |  | Agtrax_BI | DM_GrainReceiptSummary |
| Grain Receipts | Dataflow |  | ITAPPS | LocationsMaster |
| Grain Receipts | Dataflow |  | Agtrax_BI | DMvGrainBalances |
| Internal Transfers | Dataflow |  | ITAPPS | LocationsMaster |
| Internal Transfers | Dataflow |  | MKCGP | IV00101 |
| Internal Transfers | Dataflow |  | dynamics | SY01400 |
| Internal Transfers | dataflow |  | MKCGP | IRASBranchTranHDRHIST |
| Internal Transfers | dataflow |  | MKCGP | IRASBranchTranLINEHIST |
| Internal Transfers | Dataflow |  | MKCGP | IRCSReasonCodeMSTR |
| Item Price Master | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Item Price Master | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00108 |
| Item Price Master | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > SY03900 |
| LCR Reporting | Dataflow |  | CST3PWR9 | U6FRMXH |
| LCR Reporting | Dataflow |  | ITAPPS | LocationsMaster |
| LCR Reporting | Dataflow |  | CST3PWR9 | U6SEEDSTS |
| LCR Reporting | Dataflow |  | CST3PWR14 | U8CONST |
| LCR Reporting | Dataflow |  | CST3PWR10 | U4CSTMR |
| LCR Reporting | Dataflow |  | CST3PWR11 | U4ITMMR |
| LCR Reporting | Dataflow |  | CST3PWR12 | U4SLSMN |
| LCR Reporting | Dataflow |  | CST3PWR9 | USSEEDDISC |
| LCR Reporting | Dataflow |  | CST3PWR13 | USSEEDXREF |
| LCR Reporting | Dataflow |  | CST3PWR9 | U6FRMXD |
| LCR Reporting | Dataflow |  | Agtrax_BI | DateDim |
| Locations | Dataflow |  | ITAPPS | LocationsMaster |
| Long and Short | Dataflow |  | Agtrax_BI | IV_BRANCH_MASTER |
| Long and Short | Dataflow |  | Agtrax_BI | CA_POSITION_BALANCE |
| Long and Short | Dataflow |  | 0 | https://midkscoop-my.sharepoint.com/personal/pashare_producerag_com/Documents/ProducerAg%20Files/Asset%20Utilization/Long%20and%20Short.xlsm |
| MKC Branch Financials VP 7.10.23 | API |  |  |  |
| MKC Branch Financials VP 7.10.23 | mkc-sqlcall |  | agtrax_bi | MKCGP.dbo.ABCPODLU |
| MKC Branch Financials VP 7.10.23 | mkc-sqlcall |  | itapps | [ITApps].[dbo].[St_branch] |
| MKC Branch Financials VP 7.10.23 | mkc-sqlcall |  | mkcgp | MKCGP.dbo.slbAccountSummary |
| MKC Branch Financials VP 7.10.23 | mkc-sqlcall |  | mwfgp | MKCGP.dbo.vmkcBudgetSummary |
| Margin Analysis | mkc-sqlcall |  | haven | SOP30200 |
| Margin Analysis | mkc-sqlcall |  | haven | SOP30300 |
| Margin Analysis | mkc-sqlcall |  | haven | IV00101 |
| Margin Analysis | mkc-sqlcall |  | haven | IV40400 |
| Margin Analysis | mkc-sqlcall |  | mkcgp | IRCSBranchMSTR |
| Margin Analysis | mkc-sqlcall |  | mkcgp | IV00101 |
| Margin Analysis | mkc-sqlcall |  | mkcgp | vmkcSalesDetailAnalysis |
| Margin Analysis | mkc-sqlcall |  | mwfgp | IRCSBranchMSTR |
| Margin Analysis | mkc-sqlcall |  | mwfgp | IV00101 |
| Margin Analysis | mkc-sqlcall |  | mwfgp | vmwfSalesDetailAnalysis |
| Millwright Hours | SharePointList |  |  |  |
| Millwright Hours | SharePointList |  |  |  |
| Open Contracts | Dataflow |  | Agtrax_BI | DM_OpenContracts |
| Open Contracts | Dataflow |  | ITApps | DateDim |
| Open Contracts | Dataflow |  | Agtrax_BI | AR_CUSTOMER_MASTER_TMA |
| Open Contracts | mkc-sqlcall |  | agtrax_bi | Agtrax_BI..DM_OpenContractsNet |
| Open Contracts | mkc-sqlcall |  | mkcgp | AgTrax_BI..DM_OpenContracts |
| Operational KPIs | Dataflow |  | Agtrax_BI | CA_SI_TICKET_INFO |
| Operational KPIs | Dataflow |  | Agtrax_BI | CA_TICKET_OUTBOUND ,CA_TICKET_INBOUND |
| Operational KPIs | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Operational KPIs | Dataflow |  | ITAPPS | LocationsMaster |
| Operational KPIs | Dataflow |  | Agtrax_BI | DMvGrainVolume |
| Operational KPIs | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Operational KPIs | Dataflow |  | Agtrax_BI | DateDim |
| OrderEntry | tmadbserver.database.windows.net |  |  |  |
| Overtime Report | Dataflow |  | Agtrax_BI | DMvGrainVolume |
| Overtime Report | Dataflow |  | MKCGP | vmkcSalesDetailAnalysis |
| Overtime Report | Dataflow |  | MWFGP | vmwfSalesDetailAnalysis |
| Overtime Report | Dataflow |  | ITAPPS | LocationsMaster |
| Overtime Report | SharePointList |  |  |  |
| PPM - Project Portfolio Management | Dataflow |  | dynamics | SY01400 |
| PPM - Project Portfolio Management | Dataflow |  | dynamics | SLB21100 |
| PPM - Project Portfolio Management | SharePointList |  |  |  |
| PPM - Project Portfolio Management | SharePointList |  |  |  |
| PPM - Project Portfolio Management | SharePointList |  |  |  |
| PPM - Project Portfolio Management | SharePointList |  |  |  |
| PPM - Project Portfolio Management | SharePointList |  |  |  |
| Physical v Book Bushels | mkc-sqlcall |  | agtrax_bi | CA_POSITION_BALANCE |
| Physical v Book Bushels | mkc-sqlcall |  | agtrax_bi | IV_BRANCH_MASTER |
| Physical v Book Bushels | mkc-sqlcall |  | agtrax_bi | CA_COMMODITY_MASTER |
| Physical v Book Bushels | SharePointList |  |  |  |
| Procurement Long & Short | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00102 |
| Procurement Long & Short | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Procurement Long & Short | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |
| Procurement Long & Short | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > SY03900 |
| Procurement Long & Short | SharePointList |  |  |  |
| Procurement Long & Short | Dataflow |  | Agtrax_BI | DateDim |
| Sales Detail Analysis | Dataflow |  | MKCGP+MWFGP+HAVEN | MKCGP+MWFGP+HAVEN> RM00103 |
| Sales Detail Analysis | Dataflow |  | AgVend | AgVend > MKC_CRM_AccountRep ,MWF_CRM_AccountRep |
| Sales Detail Analysis | Dataflow |  | HAVEN | vFarmKanSalesDetailAnalysis |
| Sales Detail Analysis | Dataflow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |
| Sales Detail Analysis | Dataflow |  | MKCGP+MWFGP | HAVEN > RM00101 |
| Shipment Overview | mkc-sqlcall |  | agtrax_bi | DMvGrainVolume |
| Vehicle Report | API |  |  |  |
| Vehicle Report | mkc-sqlcall |  | agtrax_bi | DateDim |
| Vendor Payments | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM00100 |
| Vendor Payments | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM30200 |
| Vendor Payments | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM30300 |
| Vendor Payments | Dataflow |  | MKCGP+MWFGP | MKCGP+MWFGP > PM00200 |
| Voucher Report | API |  |  |  |
| Voucher Report | Dataflow |  | Agtrax_BI | DateDim |

### Administration

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Agronomy Scorecard | DataFlow |  | MKCGP+MWFGP | MKCGP+MWFGP > IV00101 |

### Data Portal

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Agronomy Scorecard | DataFlow | #REF! | Agtrax_BI | DateDim |

### Digital Transformation

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |

### Executive

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| CICM - PPM - Project Portfolio Management | SharePointList |  |  |  |

### Financial Processing

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| CICM - PPM - Project Portfolio Management | mkc-sqlcall |  | Date Dimension | Agtrax BI DateDim |

### Financial Reporting

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| CICM - PPM - Project Portfolio Management | DataFlow |  | dynamics | SY01400 |

### Human Resources

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| CICM - PPM - Project Portfolio Management | DataFlow |  | dynamics | SLB21100 |

### Operations

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Agronomy Scorecard | DataFlow | Sharepoint | AgVend | AgVend > MKC_CRM_AccountRep ,MWF_CRM_AccountRep |

### Producer Ag

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Agronomy Scorecard | DataFlow |  | MKCGP+MWFGP | vmkcSalesDetailAnalysis,vmwfSalesDetailAnalysis |

### Public

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Agronomy Scorecard | DataFlow |  | ITAPPS | LocationsMaster |

### Sales

**1 connection**

| Report | Type | Server | Database | Table |
|--------|------|--------|----------|-------|
| Account Assignments | DataFlow |  | AgVend | AgVend > MKC_CRM_AccountRep ,MWF_CRM_AccountRep |
