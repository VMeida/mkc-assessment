"""
architecture_diagram.py
=======================
MKC Microsoft Fabric Medallion Architecture Diagram
Generates: mkc_fabric_architecture.png + mkc_fabric_architecture.svg

Prerequisites (run once):
    sudo apt install -y graphviz
    .venv/bin/pip install "graphviz==0.20.3" diagrams

Usage:
    .venv/bin/python architecture_diagram.py
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.analytics import (
    AnalysisServices,        # semantic models (replaces PowerBiEmbedded there)
    DataFactories,
    DataLakeAnalytics,
    PowerBiEmbedded,         # kept for BI workspace / report nodes
    StreamAnalyticsJobs,
)
from diagrams.azure.storage import (
    BlobStorage,
    DataLakeStorage,
    StorageAccounts,
)
from diagrams.azure.database import (
    SQLServers,
    SQLManagedInstances,
    SQLDatawarehouse,
)
from diagrams.azure.integration import (
    DataFactories as IntDataFactories,
    APIManagementServices,
    SoftwareAsAService,
)
from diagrams.azure.compute import FunctionApps
from diagrams.azure.aimachinelearning import (
    MachineLearning,
    AzureOpenai,
    BotServices,             # Data Agents
)
from diagrams.azure.network import (
    OnPremisesDataGateways,  # replaces VirtualMachine for gateway
    PrivateEndpoint,         # private endpoint for Azure OpenAI
)
from diagrams.azure.managementgovernance import Monitor, LogAnalyticsWorkspaces
from diagrams.azure.security import KeyVaults
from diagrams.azure.identity import AzureActiveDirectory


# ---------------------------------------------------------------------------
# Global graph / node / edge attributes
# ---------------------------------------------------------------------------

GRAPH_ATTR = {
    "rankdir":   "LR",
    "splines":   "ortho",
    "nodesep":   "0.20",
    "ranksep":   "1.5",
    "fontname":  "Helvetica",
    "fontsize":  "20",
    "labelloc":  "t",
    "bgcolor":   "#1a1a2e",
    "fontcolor": "#ffffff",
    "pad":       "0.5",
}

NODE_ATTR = {
    "fontname":  "Helvetica",
    "fontsize":  "9",
    "fontcolor": "#ffffff",
}

EDGE_ATTR = {
    "fontcolor": "#cccccc",
    "fontsize":  "8",
    "fontname":  "Helvetica",
}

# Per-cluster background + border palette (dark theme)
C_SOURCE   = {"bgcolor": "#0d1f3c", "fontcolor": "#4E79A7", "pencolor": "#4E79A7",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}
C_INGEST   = {"bgcolor": "#1a2e1a", "fontcolor": "#59A14F", "pencolor": "#59A14F",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}
C_FABRIC   = {"bgcolor": "#1f1a2e", "fontcolor": "#B07AA1", "pencolor": "#B07AA1",
              "style": "filled", "fontsize": "11", "fontname": "Helvetica Bold"}
C_ONELAKE  = {"bgcolor": "#26203c", "fontcolor": "#dda0dd", "pencolor": "#dda0dd",
              "style": "dashed", "fontsize": "10", "fontname": "Helvetica Bold"}
C_BRONZE   = {"bgcolor": "#2e1f00", "fontcolor": "#F28E2B", "pencolor": "#F28E2B",
              "style": "filled", "fontsize": "10", "fontname": "Helvetica"}
C_SILVER   = {"bgcolor": "#252525", "fontcolor": "#cccccc", "pencolor": "#cccccc",
              "style": "filled", "fontsize": "10", "fontname": "Helvetica"}
C_GOLD     = {"bgcolor": "#2e2800", "fontcolor": "#FFD700", "pencolor": "#FFD700",
              "style": "filled", "fontsize": "10", "fontname": "Helvetica"}
# Semantic models: indigo/violet — clearly distinct from BI workspace red
C_SEMANTIC = {"bgcolor": "#1a0d2e", "fontcolor": "#B07AA1", "pencolor": "#B07AA1",
              "style": "filled", "fontsize": "10", "fontname": "Helvetica Bold"}
C_BI       = {"bgcolor": "#2e1a1a", "fontcolor": "#E15759", "pencolor": "#E15759",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}
C_BI_SUB   = {"bgcolor": "#3d1f1f", "fontcolor": "#ff8080", "pencolor": "#ff8080",
              "style": "dashed", "fontsize": "10", "fontname": "Helvetica"}
C_DS       = {"bgcolor": "#1a2e2e", "fontcolor": "#76B7B2", "pencolor": "#76B7B2",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}
# AI Platform: deep emerald
C_AI       = {"bgcolor": "#0d2e1a", "fontcolor": "#50C878", "pencolor": "#50C878",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}
C_GOV      = {"bgcolor": "#2a2a1a", "fontcolor": "#F28E2B", "pencolor": "#F28E2B",
              "style": "dashed", "fontsize": "11", "fontname": "Helvetica Bold"}


# ---------------------------------------------------------------------------
# Build diagram
# ---------------------------------------------------------------------------

def build_diagram(filename: str = "mkc_fabric_architecture") -> None:
    with Diagram(
        "MKC  ·  Microsoft Fabric Medallion Architecture",
        filename=filename,
        outformat=["png", "svg"],
        show=False,
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR",
    ):

        # =================================================================
        # 1 — SOURCE SYSTEMS
        # =================================================================
        with Cluster("Source Systems", graph_attr=C_SOURCE):

            with Cluster("On-Premises  ·  mkc-sqlcall (primary)",
                         graph_attr=C_SOURCE):
                with Cluster("GP / Grain / Vendor", graph_attr=C_SOURCE):
                    sql_mkcgp  = SQLServers("MKCGP\n(GP Transactions)")
                    sql_mwfgp  = SQLServers("MWFGP\n(MWF GP)")
                    sql_agtx   = SQLServers("Agtrax_BI\n(Grain / Feed)")
                    sql_agvend = SQLServers("AgVend\n(Vendor Portal)")
                with Cluster("Operations / HR", graph_attr=C_SOURCE):
                    sql_it     = SQLServers("ITAPPS\n(IT Apps)")
                    sql_haven  = SQLServers("HAVEN\n(HR / Payroll)")
                    sql_dynwh  = SQLServers("DynamicsGP\nWarehouse")

            with Cluster("On-Premises  ·  CARDTROLSVR-01",
                         graph_attr=C_SOURCE):
                sql_card = SQLServers("CARDTROLSVR-01\n\\SQLEXPRESS")

            with Cluster("Azure SQL Managed Instance  (optional lift)",
                         graph_attr=C_SOURCE):
                sql_mi = SQLManagedInstances("SQL MI\n(cloud option)")

            with Cluster("External SaaS & APIs", graph_attr=C_SOURCE):
                agvantage  = SoftwareAsAService("AgVantage\n(Grain SaaS)")
                agworld    = SoftwareAsAService("AgWorld\n(Agronomy SaaS)")
                dyn_crm    = APIManagementServices("Dynamics CRM\n(REST / Dataverse)")
                sharepoint = StorageAccounts("SharePoint\nLists")

        # =================================================================
        # 2 — INGESTION LAYER
        # =================================================================
        with Cluster("Ingestion Layer", graph_attr=C_INGEST):
            # OnPremisesDataGateways: dedicated icon (was VirtualMachine)
            gateway   = OnPremisesDataGateways(
                "On-Premises\nData Gateway\n(Standard Mode)"
            )
            pipelines = DataFactories("Fabric\nData Pipelines\n(Full + CDC)")
            dfw_gen2  = IntDataFactories(
                "Dataflow Gen2\n(Power Query)\n37 shared flows"
            )
            evtstream = StreamAnalyticsJobs(
                "Eventstream\n(Real-time)\nGrain prices / IoT"
            )

        # =================================================================
        # 3 — MICROSOFT FABRIC  /  ONELAKE
        # =================================================================
        with Cluster("Microsoft Fabric Capacity  (F32 prod · F8 dev)",
                     graph_attr=C_FABRIC):

            with Cluster("OneLake  ·  Delta Parquet  ·  Open Format (ADLS Gen2)",
                         graph_attr=C_ONELAKE):

                # Bronze
                with Cluster("Bronze Lakehouse  [raw · append-only]",
                             graph_attr=C_BRONZE):
                    bronze = BlobStorage(
                        "Raw Delta Tables\n"
                        "Partitioned by source/yr/mo\n"
                        "Retention 7 years"
                    )

                # Silver
                with Cluster("Silver Lakehouse  [clean · conformed]",
                             graph_attr=C_SILVER):
                    silver = DataLakeStorage(
                        "Validated Delta Tables\n"
                        "Typed · Deduped · Null-handled\n"
                        "Shared: DimDate · DimLocation · DimItem"
                    )

                # Gold
                with Cluster("Gold Lakehouse  [business aggregates]",
                             graph_attr=C_GOLD):
                    gold = DataLakeStorage(
                        "Aggregated Delta Tables\n"
                        "KPIs: Grain · Feed · Sales · HR\n"
                        "Open via ADLS Gen2 REST API"
                    )
                    gold_wh = SQLDatawarehouse(
                        "Fabric Warehouse\n"
                        "External tables → Gold Delta\n"
                        "T-SQL endpoint (no data copy)"
                    )

            # ----------------------------------------------------------------
            # Semantic Model Layer — sibling of OneLake, NOT nested inside it
            # Uses AnalysisServices icon (distinct from PowerBiEmbedded dashboards)
            # RLS / OLS governance enforced via Entra ID roles
            # ----------------------------------------------------------------
            with Cluster(
                "Semantic Models  ·  RLS · OLS Governed  ·  DirectLake",
                graph_attr=C_SEMANTIC,
            ):
                sem_sales = AnalysisServices(
                    "Sales Semantic Model\n"
                    "FactGrainSales · FactFeedSales\n"
                    "FactAgronomy\n"
                    "RLS: Region · Division\n"
                    "OLS: CostMargin (Finance only)"
                )
                sem_fin = AnalysisServices(
                    "Financial Semantic Model\n"
                    "FactGLTransaction · FactAPTransaction\n"
                    "FactPayroll\n"
                    "RLS: CostCenter · Company\n"
                    "OLS: SalaryAmt (HR only)"
                )
                sem_ops = AnalysisServices(
                    "Operations Semantic Model\n"
                    "FactInventory · FactOrder\n"
                    "FactARTransaction\n"
                    "RLS: Location · Division\n"
                    "OLS: CreditLimit (Finance only)"
                )

            # Notebook transformation engines (inside Fabric, outside OneLake)
            nb_b2s = MachineLearning(
                "Notebooks: Bronze→Silver\n"
                "PySpark · MERGE INTO\n"
                "Schema enforce · DQ checks"
            )
            nb_s2g = MachineLearning(
                "Notebooks: Silver→Gold\n"
                "Spark SQL · Cross-DB joins\n"
                "Business rules · KPI calc"
            )

        # =================================================================
        # 4 — BI SELF-SERVICE WORKSPACES  (22 total)
        #     Each sub-cluster includes a Fabric Data Agent (BotServices)
        #     scoped to that workspace group's semantic models
        # =================================================================
        # Reports sourced from DFW Lineage sheet only (12 workspaces, 40 reports)
        with Cluster("BI Self-Service  (DFW Lineage — 12 Workspaces · 40 Reports)",
                     graph_attr=C_BI):

            with Cluster("Operational", graph_attr=C_BI_SUB):
                ws_sales  = PowerBiEmbedded(
                    "Sales  (8 reports)\n"
                    "Account Assignments\n"
                    "Fertilizer Prepay · LCR Reporting\n"
                    "Energy · Agronomy · Fuel · Feed Scorecards\n"
                    "Item Price Master"
                )
                ws_oms    = PowerBiEmbedded(
                    "OMS  (1 report)\n"
                    "OrderEntry"
                )
                ws_ops    = PowerBiEmbedded(
                    "Operations  (2 reports)\n"
                    "Operational KPIs · Locations"
                )
                agent_ops = BotServices(
                    "Data Agent\n(Operational)\nNL → Sales · OMS · Ops"
                )

            with Cluster("Analytics — Executive / Portal", graph_attr=C_BI_SUB):
                ws_exec    = PowerBiEmbedded(
                    "Executive  (2 reports)\n"
                    "Financials · Executive Sales"
                )
                ws_dp      = PowerBiEmbedded(
                    "Data Portal  (4 reports)\n"
                    "Sales Detail Analysis\n"
                    "Customer Master Summary\n"
                    "GL Reconciliation\n"
                    "Applications Revenue"
                )
                agent_exec = BotServices(
                    "Data Agent\n(Analytics)\nNL → Exec · Portal · Fin"
                )

            with Cluster("Analytics — Financial", graph_attr=C_BI_SUB):
                ws_fin_r  = PowerBiEmbedded(
                    "Financial Reporting  (3 reports)\n"
                    "Voucher Report\n"
                    "MKC Branch Financials\n"
                    "Vehicle Report"
                )
                ws_fin_p  = PowerBiEmbedded(
                    "Financial Processing  (3 reports)\n"
                    "1099 Amount to Payments\n"
                    "Vendor Payments · Credit Holds"
                )
                agent_fin = BotServices(
                    "Data Agent\n(Financial)\nNL → GL · AP · Payroll"
                )

            with Cluster("Domain", graph_attr=C_BI_SUB):
                ws_admin     = PowerBiEmbedded(
                    "Administration  (7 reports)\n"
                    "Internal Transfers · Margin Analysis\n"
                    "Energy Dept Orders · Claims Report\n"
                    "Procurement Long & Short\n"
                    "Billing Dashboard · CICM PPM"
                )
                ws_pag       = PowerBiEmbedded(
                    "Producer Ag  (6 reports)\n"
                    "Long and Short\n"
                    "Physical v Book Bushels\n"
                    "Grain Receipts · Open Contracts\n"
                    "Shipment Overview · Dispatch"
                )
                ws_hr        = PowerBiEmbedded(
                    "Human Resources  (2 reports)\n"
                    "Overtime Report · Millwright Hours"
                )
                ws_dt        = PowerBiEmbedded(
                    "Digital Transformation  (1 report)\n"
                    "PPM - Project Portfolio Management"
                )
                ws_pub       = PowerBiEmbedded(
                    "Public  (1 report)\n"
                    "CICM - PPM\n"
                    "Project Portfolio Management"
                )
                agent_domain = BotServices(
                    "Data Agent\n(Domain)\nNL → Admin · Ag · HR · DT"
                )

        # =================================================================
        # 5 — DATA SCIENCE & ML
        # =================================================================
        with Cluster("Data Science & ML", graph_attr=C_DS):
            ml_nb    = MachineLearning(
                "ML Notebooks\n(Fabric Spark)\nFeature engineering"
            )
            ml_exp   = MachineLearning(
                "ML Experiments\n(MLflow tracking)\nModel registry"
            )
            feat_st  = DataLakeStorage(
                "Feature Store\n(Gold Delta)\nAgronomic · CRM features"
            )
            ml_serve = FunctionApps(
                "Model Serving\n(Azure Functions)\nYield · Churn · Anomaly"
            )
            copilot  = AzureOpenai(
                "Fabric Copilot\n(F64+ only)\nNL → DAX / SQL"
            )

        # =================================================================
        # 6 — AI PLATFORM  ·  ENTERPRISE LLM
        #     Azure OpenAI Service secured behind Private Endpoint + APIM
        #     Consumed by: Data Agents, Fabric Copilot, ML Notebooks
        # =================================================================
        with Cluster("AI Platform  ·  Enterprise LLM", graph_attr=C_AI):
            azure_oai = AzureOpenai(
                "Azure OpenAI Service\n"
                "GPT-4o · text-embedding-3-large\n"
                "Private Endpoint · Managed Identity\n"
                "SOC2 · HIPAA · ISO27001\n"
                "Data stays in tenant"
            )
            oai_pe = PrivateEndpoint(
                "Private Endpoint\n"
                "VNet-secured\n"
                "No public internet"
            )
            apim_ai = APIManagementServices(
                "LLM Gateway  (Azure APIM)\n"
                "Rate limiting · Token metering\n"
                "Managed Identity auth\n"
                "Audit log → Log Analytics"
            )

        # =================================================================
        # 7 — GOVERNANCE & SECURITY
        # =================================================================
        with Cluster("Governance & Security", graph_attr=C_GOV):
            purview = DataLakeAnalytics(
                "Microsoft Purview\nData Catalog\nLineage · Sensitivity"
            )
            monitor = Monitor(
                "Azure Monitor\nCapacity Metrics\nPipeline Alerts"
            )
            log_a   = LogAnalyticsWorkspaces("Log Analytics\nAudit Logs")
            kv      = KeyVaults(
                "Key Vault\nConnection Secrets\nSPN Credentials"
            )
            entra   = AzureActiveDirectory(
                "Microsoft Entra ID\nWorkspace RBAC\nRLS · OLS identity"
            )

        # =================================================================
        # EDGES
        # =================================================================

        # -- Source → Gateway (on-prem SQL)
        sql_edge = Edge(color="#4E79A7", label="JDBC / Gateway")
        [sql_mkcgp, sql_mwfgp, sql_agtx,
         sql_it, sql_haven, sql_agvend,
         sql_dynwh, sql_card] >> sql_edge >> gateway

        # -- SQL MI → Pipelines (direct VNet, no gateway)
        sql_mi >> Edge(color="#4E79A7", label="Direct VNet") >> pipelines

        # -- Gateway → Pipelines
        gateway >> Edge(color="#59A14F", label="Encrypted tunnel") >> pipelines

        # -- SaaS / API → Dataflow Gen2
        api_edge = Edge(color="#FF9DA7", style="dashed", label="REST / OData")
        [agvantage, agworld, dyn_crm] >> api_edge >> dfw_gen2
        sharepoint >> Edge(
            color="#B07AA1", style="dashed", label="SP.Lists"
        ) >> dfw_gen2

        # -- Ingestion → Bronze
        pipelines >> Edge(
            color="#F28E2B", label="Full / CDC\nDelta write"
        ) >> bronze
        dfw_gen2  >> Edge(color="#F28E2B", label="Append raw") >> bronze
        evtstream >> Edge(
            color="#F28E2B", label="Streaming append"
        ) >> bronze

        # -- Bronze → Silver → Gold (via Notebooks)
        bronze >> Edge(color="#B07AA1", label="Spark read") >> nb_b2s
        nb_b2s >> Edge(color="#B07AA1", label="MERGE INTO") >> silver

        silver >> Edge(color="#76B7B2", label="Spark read") >> nb_s2g
        nb_s2g >> Edge(color="#76B7B2", label="Aggregate write") >> gold

        # -- Gold → Warehouse (external table, no data copy)
        gold >> Edge(
            color="#FFD700", label="External table\n(no data copy)"
        ) >> gold_wh

        # -- Warehouse → Semantic Models (T-SQL views → DirectLake)
        wh_edge = Edge(color="#B07AA1", label="T-SQL views")
        gold_wh >> wh_edge >> sem_sales
        gold_wh >> wh_edge >> sem_fin
        gold_wh >> wh_edge >> sem_ops

        # -- Semantic Models → BI Workspaces (DirectLake)
        dl_edge = Edge(color="#E15759", label="DirectLake")
        sem_sales >> dl_edge >> ws_sales
        sem_sales >> dl_edge >> ws_oms
        sem_sales >> dl_edge >> ws_exec
        sem_sales >> dl_edge >> ws_dp
        sem_sales >> dl_edge >> ws_pag
        sem_fin   >> dl_edge >> ws_fin_r
        sem_fin   >> dl_edge >> ws_fin_p
        sem_fin   >> dl_edge >> ws_admin
        sem_fin   >> dl_edge >> ws_hr
        sem_ops   >> dl_edge >> ws_ops
        sem_ops   >> dl_edge >> ws_dt
        sem_fin   >> dl_edge >> ws_pub   # Public: CICM PPM → Financial model

        # -- Semantic Models → Data Agents (agents query semantic models)
        ag_q = Edge(color="#B07AA1", style="dashed", label="NL→DAX")
        sem_sales >> ag_q >> agent_ops
        sem_sales >> ag_q >> agent_exec
        sem_fin   >> ag_q >> agent_fin
        sem_fin   >> ag_q >> agent_exec
        sem_fin   >> ag_q >> agent_domain
        sem_ops   >> ag_q >> agent_exec
        sem_ops   >> ag_q >> agent_domain

        # -- Data Agents → AI Platform (LLM inference via APIM gateway)
        llm_edge = Edge(color="#50C878", style="dashed", label="LLM inference")
        [agent_ops, agent_exec, agent_fin, agent_domain] >> llm_edge >> apim_ai

        # -- AI Platform internal path: APIM → PrivateEndpoint → Azure OpenAI
        apim_ai >> Edge(color="#50C878") >> oai_pe
        oai_pe  >> Edge(color="#50C878") >> azure_oai

        # -- Fabric Copilot → AI Platform (same LLM gateway)
        copilot >> Edge(
            color="#50C878", style="dashed",
            label="NL → DAX / SQL\n(F64+ only)"
        ) >> apim_ai

        # -- Gold → Feature Store → ML pipeline
        gold    >> Edge(color="#76B7B2", label="Feature read") >> feat_st
        feat_st >> Edge(color="#76B7B2") >> ml_nb
        ml_nb   >> Edge(color="#76B7B2") >> ml_exp
        ml_exp  >> Edge(
            color="#76B7B2", label="Champion model"
        ) >> ml_serve
        # ML enrichment writes back to Gold
        ml_nb   >> Edge(
            color="#76B7B2", style="dashed", label="Enrichment write"
        ) >> gold

        # -- ML Notebooks → AI Platform (LLM-enhanced features)
        ml_nb >> Edge(
            color="#50C878", style="dashed", label="LLM features"
        ) >> apim_ai

        # -- Governance: RLS/OLS on Semantic Models (Entra ID → sem_*)
        rl_edge = Edge(
            color="#F28E2B", style="dotted", label="RLS · OLS roles"
        )
        entra >> rl_edge >> sem_sales
        entra >> rl_edge >> sem_fin
        entra >> rl_edge >> sem_ops
        # T-SQL RBAC on Warehouse
        entra >> Edge(
            color="#F28E2B", style="dotted", label="RBAC"
        ) >> gold_wh

        # -- Governance: monitoring, catalog, secrets (cross-cutting)
        gov_dot = Edge(color="#F28E2B", style="dotted")
        [pipelines, dfw_gen2, nb_b2s, nb_s2g] >> gov_dot >> monitor
        monitor >> gov_dot >> log_a
        # APIM audit log → Log Analytics
        apim_ai >> Edge(
            color="#50C878", style="dotted", label="audit log"
        ) >> log_a
        [bronze, silver, gold] >> Edge(
            color="#F28E2B", style="dotted", label="catalog / lineage"
        ) >> purview
        kv >> Edge(
            color="#F28E2B", style="dotted", label="secrets"
        ) >> pipelines


# ---------------------------------------------------------------------------
# Legend diagram — all icons used in the main diagram, grouped by category
# Generates: mkc_fabric_legend.png + mkc_fabric_legend.svg
# ---------------------------------------------------------------------------

LEGEND_GRAPH = {
    "rankdir":   "LR",
    "nodesep":   "0.30",
    "ranksep":   "0.90",
    "fontname":  "Helvetica",
    "fontsize":  "18",
    "labelloc":  "t",
    "bgcolor":   "#1a1a2e",
    "fontcolor": "#ffffff",
    "pad":       "0.6",
}

LEGEND_NODE = {
    "fontname":  "Helvetica",
    "fontsize":  "9",
    "fontcolor": "#ffffff",
}


def build_legend(filename: str = "mkc_fabric_legend") -> None:
    """Generate a standalone icon legend for the architecture diagram."""
    with Diagram(
        "MKC Fabric Architecture  —  Icon Legend",
        filename=filename,
        outformat=["png", "svg"],
        show=False,
        graph_attr=LEGEND_GRAPH,
        node_attr=LEGEND_NODE,
        direction="LR",
    ):
        # ------------------------------------------------------------------
        # 1 — DATA SOURCES
        # ------------------------------------------------------------------
        with Cluster("Data Sources", graph_attr=C_SOURCE):
            SQLServers("On-Premises SQL Server\n(mkc-sqlcall · CARDTROLSVR-01)")
            SQLManagedInstances("Azure SQL\nManaged Instance\n(optional lift)")
            SoftwareAsAService("External SaaS\n(AgVantage · AgWorld)")
            # NOTE: same icon used for Dynamics CRM REST in main diagram
            APIManagementServices("REST / CRM API\n(Dynamics CRM · Dataverse)")
            StorageAccounts("SharePoint Lists\n(SP.Lists connector)")

        # ------------------------------------------------------------------
        # 2 — INGESTION
        # ------------------------------------------------------------------
        with Cluster("Ingestion Layer", graph_attr=C_INGEST):
            OnPremisesDataGateways(
                "On-Premises Data Gateway\n(Standard Mode · outbound tunnel)"
            )
            DataFactories(
                "Fabric Data Pipelines\n(ADF engine · Full + CDC ingestion)"
            )
            IntDataFactories(
                "Dataflow Gen2\n(Power Query engine · 37 shared flows)"
            )
            StreamAnalyticsJobs(
                "Eventstream\n(Real-time streaming · grain prices / IoT)"
            )

        # ------------------------------------------------------------------
        # 3 — ONELAKE STORAGE  (Delta Parquet — open format)
        # ------------------------------------------------------------------
        with Cluster("OneLake Storage  ·  Delta Parquet  ·  Open Format",
                     graph_attr=C_ONELAKE):
            BlobStorage(
                "Bronze Lakehouse\n(Raw Delta · append-only · 7-yr retention)"
            )
            DataLakeStorage(
                "Silver / Gold Lakehouse\n(Validated / aggregated Delta)\n"
                "also used for: Feature Store"
            )
            SQLDatawarehouse(
                "Fabric Warehouse\n(T-SQL endpoint · External Tables)\n"
                "no data copy from Gold"
            )

        # ------------------------------------------------------------------
        # 4 — SEMANTIC MODELS & BI  (★ two distinct icons)
        # ------------------------------------------------------------------
        with Cluster(
            "Semantic Models & BI  (two distinct icons)",
            graph_attr=C_SEMANTIC,
        ):
            AnalysisServices(
                "Semantic Model\n(AnalysisServices icon)\n"
                "DirectLake · RLS · OLS governed\n"
                "Sales / Financial / Operations schemas"
            )
            PowerBiEmbedded(
                "Power BI Report / Dashboard\n(PowerBiEmbedded icon)\n"
                "22 workspaces · 170 reports\n"
                "Distinct from Semantic Model above"
            )
            BotServices(
                "Fabric Data Agent\n(BotServices icon)\n"
                "NL → DAX/SQL per workspace group\n"
                "Governed by same RBAC as semantic model"
            )

        # ------------------------------------------------------------------
        # 5 — DATA SCIENCE & ML
        # ------------------------------------------------------------------
        with Cluster("Data Science & ML", graph_attr=C_DS):
            MachineLearning(
                "Fabric Notebooks\n(PySpark · MERGE INTO · Spark SQL)\n"
                "also used for: ML Experiments (MLflow)"
            )
            FunctionApps(
                "Model Serving\n(Azure Functions)\n"
                "Yield prediction · Churn · Anomaly"
            )
            AzureOpenai(
                "Fabric Copilot  (F64+ only)\n(AzureOpenai icon)\n"
                "NL → DAX / SQL  ·  same icon\nas Azure OpenAI Service below"
            )

        # ------------------------------------------------------------------
        # 6 — AI PLATFORM  ·  ENTERPRISE LLM
        # ------------------------------------------------------------------
        with Cluster("AI Platform  ·  Enterprise LLM", graph_attr=C_AI):
            AzureOpenai(
                "Azure OpenAI Service\n(AzureOpenai icon — same as Copilot)\n"
                "GPT-4o · text-embedding-3-large\n"
                "SOC2 · HIPAA · Managed Identity\n"
                "Data stays in tenant"
            )
            PrivateEndpoint(
                "Private Endpoint\n(PrivateEndpoint icon)\n"
                "VNet-secured · no public internet\n"
                "All traffic on Microsoft backbone"
            )
            APIManagementServices(
                "LLM Gateway  (Azure APIM)\n(APIManagementServices icon)\n"
                "Rate limiting · token metering\n"
                "Audit log → Log Analytics\n"
                "also used for: Dynamics CRM source"
            )

        # ------------------------------------------------------------------
        # 7 — GOVERNANCE & SECURITY
        # ------------------------------------------------------------------
        with Cluster("Governance & Security", graph_attr=C_GOV):
            DataLakeAnalytics(
                "Microsoft Purview\n(DataLakeAnalytics icon)\n"
                "Data catalog · lineage · sensitivity labels"
            )
            Monitor(
                "Azure Monitor\n(Monitor icon)\n"
                "Fabric capacity metrics · pipeline alerts"
            )
            LogAnalyticsWorkspaces(
                "Log Analytics Workspace\n(LogAnalyticsWorkspaces icon)\n"
                "Audit logs · APIM token usage"
            )
            KeyVaults(
                "Azure Key Vault\n(KeyVaults icon)\n"
                "Connection strings · SPN credentials"
            )
            AzureActiveDirectory(
                "Microsoft Entra ID\n(AzureActiveDirectory icon)\n"
                "Workspace RBAC · RLS roles · OLS roles"
            )

        # ------------------------------------------------------------------
        # Edge style legend (horizontal strip at bottom via separate cluster)
        # ------------------------------------------------------------------
        with Cluster("Edge / Arrow Styles", graph_attr={
            "bgcolor": "#12122a", "fontcolor": "#cccccc",
            "pencolor": "#555577", "style": "dashed",
            "fontsize": "10", "fontname": "Helvetica Bold",
        }):
            e_src = SQLServers(" ")
            e_ingest = DataFactories(" ")
            e_bronze = BlobStorage(" ")
            e_silver = DataLakeStorage("  ")
            e_gold = SQLDatawarehouse("  ")
            e_sem = AnalysisServices("  ")
            e_bi = PowerBiEmbedded("  ")
            e_ai = AzureOpenai("  ")
            e_gov = Monitor("  ")

            e_src >> Edge(
                color="#4E79A7", label="JDBC via Gateway\n(on-prem SQL → ingestion)"
            ) >> e_ingest
            e_ingest >> Edge(
                color="#F28E2B", label="Delta write\n(ingestion → Bronze)"
            ) >> e_bronze
            e_bronze >> Edge(
                color="#B07AA1", label="Spark read / MERGE INTO\n(Bronze → Silver → Gold)"
            ) >> e_silver
            e_silver >> Edge(
                color="#FFD700", label="External table\n(Gold → Warehouse)"
            ) >> e_gold
            e_gold >> Edge(
                color="#B07AA1", label="T-SQL views / DirectLake\n(Warehouse → Semantic Models)"
            ) >> e_sem
            e_sem >> Edge(
                color="#E15759", label="DirectLake\n(Semantic Model → BI)"
            ) >> e_bi
            e_sem >> Edge(
                color="#B07AA1", style="dashed",
                label="NL→DAX query\n(Semantic Model → Data Agent → AI Platform)"
            ) >> e_ai
            e_gov >> Edge(
                color="#F28E2B", style="dotted",
                label="Governance (dotted)\n(monitor / catalog / secrets / RLS·OLS)"
            ) >> e_silver
            e_ai >> Edge(
                color="#50C878", style="dashed",
                label="LLM inference (emerald dashed)\n(Agents / Copilot → AI Platform)"
            ) >> e_bi


if __name__ == "__main__":
    build_diagram()
    print("[OK] Architecture diagram → mkc_fabric_architecture.png + .svg")
    build_legend()
    print("[OK] Legend diagram       → mkc_fabric_legend.png + .svg")
