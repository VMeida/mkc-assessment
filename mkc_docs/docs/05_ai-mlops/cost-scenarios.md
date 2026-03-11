# AI Cost Scenarios

## The Three Cost Buckets

MKC's AI platform has **three independent cost components** that appear on separate bills:

!!! info "Three Independent Cost Lines"
    **Microsoft Fabric F-SKU** — Fixed monthly platform cost covering all data workloads (pipelines, lakehouses, notebooks, Power BI, Semantic Models, and Data Agent execution). This cost exists regardless of AI usage volume.

    **Foundry Agent Service** — Variable cost per agent orchestration step, billed to the Azure subscription (not Fabric). Covers the reasoning loop, tool dispatch, and model invocations managed by Foundry.

    **External Reasoning Model tokens** — Variable per-token cost for the LLM that generates narrative insights (Claude, GPT-4o, etc.), billed via Azure AI Foundry or Azure OpenAI — separate from both Fabric and Foundry orchestration.

---

## LLM Process Component Breakdown

Each user query travels through six steps. The table below identifies which billing bucket owns each step.

```
User → App / Teams → [APIM opt.] → Foundry Agent → Data Agent → Fabric Semantic Model
                                                                              ↓
                                              User ← Foundry Agent ← External LLM (sanitised summary)
```

| Step | Component | Service | Billing Model | Charged to Fabric F-SKU? |
|------|-----------|---------|---------------|--------------------------|
| 1 | User query arrives at app / Teams / Copilot | App hosting (App Service / Teams) | Flat / included | No — App Service or M365 billing |
| 2 | **APIM edge gateway** *(optional — Position 1)* | Azure APIM | ~$3.50 per 1M calls + $0.09/GB data | No — Azure subscription |
| 3 | **Foundry Agent orchestration** — plan, tool selection, trace | Azure AI Foundry Agent Service | Per orchestration step / token (see below) | No — Azure subscription |
| 4 | **Data Agent — NL→DAX translation** | Fabric Data Agent (Fabric AI item) | Fabric CU-seconds consumed | **Yes — Fabric F-SKU** |
| 5 | **Semantic Model — DAX execution** | Fabric Power BI / Analysis Services engine | Fabric CU-seconds consumed | **Yes — Fabric F-SKU** |
| 6 | **APIM internal governance** *(optional — Position 2)* | Azure APIM | ~$3.50 per 1M calls | No — Azure subscription |
| 7 | **External reasoning model** — narrative insight generation | Azure AI Foundry / Azure OpenAI | Per input + output token | No — Azure AI Foundry / AOAI billing |
| 8 | Foundry returns answer to user | Foundry Agent Service (outbound) | Included in orchestration cost | No |

!!! success "Key Insight: DAX Generation Is Now Inside Fabric"
    In the Foundry Agent Service architecture, **NL→DAX translation is a Fabric operation** (Step 4) — it runs inside the Data Agent item and is absorbed by the F-SKU. External LLM tokens (Step 7) are used only for narrative reasoning on a compact, sanitised summary, not for schema-aware query generation. This means external token costs are significantly lower than in a direct APIM → Azure OpenAI architecture.

---

## What Each Billing Bucket Covers

=== "Fabric F-SKU (Fixed)"

    Everything that runs inside the Fabric capacity boundary.

    | Fabric Workload | CU Consumption Driver | Notes |
    |-----------------|-----------------------|-------|
    | **Data Agent NL→DAX translation** | CU-seconds per query | Uses Fabric's built-in model layer; no external token charge |
    | **Semantic Model DAX execution** | CU-seconds proportional to query complexity | Same engine as Power BI — shared capacity with other BI workloads |
    | **Dataflow / pipeline refreshes** | CU-seconds during execution window | Not AI-specific; same as standard Fabric workloads |
    | **OneLake storage** | GB stored / month | Bronze + Silver + Gold layers |
    | **ML Notebooks** (feature engineering) | Spark CU-seconds during execution | Only during active notebook runs |
    | **Power BI report rendering** | CU-seconds per report load | Shared with Data Agent capacity |

    !!! warning "Data Agent and Power BI Compete for the Same CU Pool"
        Fabric capacity is shared. A spike in Data Agent query volume (e.g. 500 simultaneous agent queries) will consume CUs that would otherwise serve Power BI report renders. Size the F-SKU with headroom for peak AI load — see the scenario tables below.

=== "Foundry Agent Service (Variable)"

    Billed to the Azure subscription as an Azure AI Foundry cost, separate from Fabric.

    | Foundry Component | Billing Unit | Estimated Cost | Notes |
    |-------------------|-------------|----------------|-------|
    | **Agent orchestration** (plan + tool dispatch) | Per orchestration step / execution | ~$0.001–$0.005 per agent run | Preview pricing as of Q1 2026 — confirm at [Azure AI Foundry pricing](https://azure.microsoft.com/pricing/details/ai-foundry/) |
    | **Foundry managed storage** (thread / trace storage) | GB / month | Minimal — traces are small | Thread history for multi-turn conversations |
    | **Foundry evaluation** (optional) | Per evaluation run | Variable | Used for model quality A/B testing |

    !!! warning "Foundry Agent Service Pricing — Verify Before Budgeting"
        Foundry Agent Service (Azure AI Agent Service) pricing was in preview as of March 2026. The estimates above are indicative. Confirm current pricing at the Azure AI Foundry pricing page before building production cost models.

=== "External Reasoning Model Tokens (Variable)"

    Billed via Azure AI Foundry or Azure OpenAI, separate from Fabric and Foundry orchestration.

    | Model | Input $/1M tokens | Output $/1M tokens | Tokens per reasoning call* | $/reasoning call |
    |-------|------------------|-------------------|---------------------------|-----------------|
    | **Claude 3.5 Sonnet** | $3.00 | $15.00 | ~1,000 | ~$0.008 |
    | **Claude 3.5 Haiku** | $0.80 | $4.00 | ~1,000 | ~$0.002 |
    | **GPT-4o** | $2.50 | $10.00 | ~1,000 | ~$0.006 |
    | **GPT-4o-mini** | $0.15 | $0.60 | ~1,000 | ~$0.0003 |
    | **Mistral Large 2** | $2.00 | $6.00 | ~1,000 | ~$0.005 |
    | **Mistral Small 3** | $0.10 | $0.30 | ~1,000 | ~$0.0001 |

    *Token estimate for reasoning calls in the Foundry architecture — see breakdown below.

---

## Token Consumption — Foundry Agent Architecture

In the Foundry Agent architecture, external LLM tokens are used **only for reasoning on a sanitised summary** — not for NL→DAX generation (which happens inside Fabric). This significantly reduces external token spend.

### Per-Query Token Breakdown

| Component | Tokens | Where It Runs | Billed To |
|-----------|--------|--------------|-----------|
| Foundry Agent system policy prompt | ~300 input | Foundry / External LLM | External LLM billing |
| Sanitised data summary from Data Agent | ~400 input | Foundry / External LLM | External LLM billing |
| User question (rephrased for reasoning) | ~50 input | Foundry / External LLM | External LLM billing |
| Narrative reasoning response | ~300 output | External LLM | External LLM billing |
| **Total external tokens per query** | **~1,050** | | **~$0.006 (GPT-4o)** |
| | | | **~$0.0003 (GPT-4o-mini)** |
| NL→DAX translation (inside Data Agent) | ~3,000 tokens (internal) | Fabric Data Agent | **Fabric F-SKU** |

!!! success "45% Fewer External Tokens vs. Direct APIM → AOAI Architecture"
    The previous architecture sent the full Semantic Model schema (~2,000 tokens) plus few-shot DAX examples (~1,000 tokens) to the external LLM on every query — ~3,350 tokens total. In the Foundry architecture, DAX generation stays inside Fabric and the external LLM only sees a compact summary (~1,050 tokens). This is a **69% reduction in external token spend** per query.

---

## Three Deployment Scenarios

=== "Pilot (25 users)"

    **Usage assumptions:** 25 users · 5 queries/user/day · 3,750 queries/month

    ### What's Charged to Fabric F-SKU

    | Fabric Component | Monthly Cost | Notes |
    |-----------------|-------------|-------|
    | Fabric F32 (Production) | $4,194 | Includes Data Agent execution, DAX queries, Power BI, pipelines |
    | Fabric F8 (Dev/Test, paused overnight) | ~$200 | Paused ~14 hrs/day to reduce cost |
    | **Fabric total** | **$4,394** | Fixed regardless of query volume |

    ### What's Billed Outside Fabric

    | External Component | Monthly Cost (GPT-4o) | Monthly Cost (GPT-4o-mini) | Notes |
    |-------------------|----------------------|--------------------------|-------|
    | Foundry Agent Service (3,750 runs) | ~$4–$19 | ~$4–$19 | ~$0.001–$0.005/run (preview pricing) |
    | External LLM — reasoning tokens (3,750 calls × 1,050 tok) | ~$23 | ~$1 | GPT-4o or GPT-4o-mini as reasoning backend |
    | Azure APIM *(optional — Position 1 or 2)* | ~$3 | ~$3 | Negligible at pilot scale |
    | **Outside Fabric total** | **~$30–$45** | **~$8–$23** | |

    ### Total Monthly Cost

    | | GPT-4o reasoning | GPT-4o-mini reasoning |
    |-|-----------------|----------------------|
    | Fabric F-SKU | $4,394 | $4,394 |
    | Outside Fabric (Foundry + LLM + APIM) | ~$42 | ~$20 |
    | **Total** | **~$4,436** | **~$4,414** |
    | External AI cost as % of total | ~0.9% | ~0.4% |

    > At pilot scale, external AI costs remain under 1% of total spend regardless of model choice.

=== "Production (150 users)"

    **Usage assumptions:** 150 users · 10 queries/user/day · 45,000 queries/month

    ### What's Charged to Fabric F-SKU

    | Fabric Component | Monthly Cost | Notes |
    |-----------------|-------------|-------|
    | Fabric F32 (Production) | $4,194 | Shared across Data Agents + Power BI + pipelines |
    | Fabric F8 (Dev/Test, paused overnight) | ~$200 | |
    | **Fabric total** | **$4,394** | Fixed — same as Pilot (F32 has headroom for this volume) |

    ### What's Billed Outside Fabric

    | External Component | Monthly Cost (GPT-4o) | Monthly Cost (GPT-4o-mini) | Monthly Cost (Claude 3.5 Sonnet) |
    |-------------------|----------------------|--------------------------|----------------------------------|
    | Foundry Agent Service (45,000 runs) | ~$45–$225 | ~$45–$225 | ~$45–$225 |
    | External LLM — reasoning tokens (45,000 × 1,050 tok) | ~$283 | ~$14 | ~$378 |
    | Azure APIM *(optional)* | ~$15 | ~$15 | ~$15 |
    | **Outside Fabric total** | **~$343–$523** | **~$74–$254** | **~$438–$618** |

    ### Total Monthly Cost

    | | GPT-4o reasoning | GPT-4o-mini reasoning | Claude 3.5 Sonnet |
    |-|-----------------|----------------------|------------------|
    | Fabric F-SKU | $4,394 | $4,394 | $4,394 |
    | Outside Fabric | ~$433 | ~$164 | ~$528 |
    | **Total** | **~$4,827** | **~$4,558** | **~$4,922** |
    | External AI cost as % of total | ~9% | ~3.6% | ~10.7% |

    !!! tip "Production Model Selection"
        At 45,000 queries/month, the cost difference between GPT-4o (~$433 external) and Claude 3.5 Sonnet (~$528 external) is ~$95/month — less than 2% of total spend. Model selection at this scale should be driven by reasoning quality, not cost.

=== "Scale (500 users)"

    **Usage assumptions:** 500 users · 15 queries/user/day · 225,000 queries/month

    ### What's Charged to Fabric F-SKU

    | Fabric Component | Monthly Cost | Notes |
    |-----------------|-------------|-------|
    | Fabric F64 (Production) | $8,388 | Upgraded from F32 — needed for Data Agent + BI load at 500 users |
    | Fabric F8 (Dev/Test, paused overnight) | ~$200 | |
    | **Fabric total** | **$8,588** | F64 upgrade adds ~$4,194 vs. Production scenario |

    ### What's Billed Outside Fabric

    | External Component | Monthly Cost (GPT-4o) | Monthly Cost (GPT-4o-mini) | Monthly Cost (Hybrid 60/40) |
    |-------------------|----------------------|--------------------------|----------------------------|
    | Foundry Agent Service (225,000 runs) | ~$225–$1,125 | ~$225–$1,125 | ~$225–$1,125 |
    | External LLM — reasoning tokens (225,000 × 1,050 tok) | ~$1,417 | ~$71 | ~$583 |
    | Azure APIM *(optional)* | ~$50 | ~$50 | ~$50 |
    | **Outside Fabric total** | **~$1,692–$2,592** | **~$346–$1,246** | **~$858–$1,758** |

    ### Total Monthly Cost

    | | GPT-4o reasoning | GPT-4o-mini reasoning | Hybrid (60% mini + 40% GPT-4o) |
    |-|-----------------|----------------------|-------------------------------|
    | Fabric F-SKU | $8,588 | $8,588 | $8,588 |
    | Outside Fabric | ~$2,142 | ~$796 | ~$1,308 |
    | **Total** | **~$10,730** | **~$9,384** | **~$9,896** |
    | External AI cost as % of total | ~20% | ~8.5% | ~13.2% |

    !!! tip "Scale Optimisation"
        At 500 users, Foundry Agent Service orchestration cost becomes material (potentially $225–$1,125/month depending on GA pricing). Monitor orchestration costs separately from token costs. Hybrid routing (60% GPT-4o-mini + 40% GPT-4o) saves ~$834/month vs. all-GPT-4o on reasoning tokens alone.

---

## Cost Optimisation — Intelligent Routing

Route reasoning calls by query complexity using a lightweight Foundry classifier tool:

| Traffic Mix | External $/reasoning call | External $/month (225K queries) |
|------------|--------------------------|--------------------------------|
| 100% GPT-4o | ~$0.0063 | ~$1,417 |
| 100% GPT-4o-mini | ~$0.0003 | ~$71 |
| **60% mini + 40% GPT-4o** (hybrid) | **~$0.0027** | **~$583** |
| 100% Claude 3.5 Sonnet | ~$0.0084 | ~$1,890 |
| 100% Claude 3.5 Haiku | ~$0.0022 | ~$495 |
| 100% Mistral Small 3 | ~$0.0001 | ~$22 |

Hybrid routing (60/40 split) saves **59% vs. all-GPT-4o** on reasoning tokens. Note that Foundry Agent Service orchestration cost (per run) is the same regardless of which reasoning model is selected — the saving is purely on token billing.

---

## Provisioned Throughput Units (PTU)

At high reasoning call volumes, **Azure OpenAI PTU** reservations become cheaper than pay-as-you-go. Note PTU applies to the reasoning token cost only — Foundry orchestration and Fabric F-SKU are unaffected.

| Volume | PAYG Reasoning Cost | PTU Estimate | Savings |
|--------|--------------------|-----------| --------|
| 45,000 queries/month (GPT-4o) | ~$283 | ~$255 | ~10% |
| 225,000 queries/month (GPT-4o) | ~$1,417 | ~$1,150 | ~19% |
| 225,000 queries/month (GPT-4o-mini) | ~$71 | Not justified | — |

**PTU break-even:** ~250,000 GPT-4o reasoning calls/month. Below that, PAYG is cheaper.

---

## Full Cost Summary

| | Pilot (25 users) | Production (150 users) | Scale (500 users) |
|--|---|---|---|
| **Queries/month** | 3,750 | 45,000 | 225,000 |
| **Fabric SKU** | F32 + F8 | F32 + F8 | F64 + F8 |
| | | | |
| **Fabric F-SKU** | $4,394 | $4,394 | $8,588 |
| **Foundry Agent Service** | ~$4–$19 | ~$45–$225 | ~$225–$1,125 |
| **Reasoning tokens (GPT-4o)** | ~$23 | ~$283 | ~$1,417 |
| **Reasoning tokens (GPT-4o-mini)** | ~$1 | ~$14 | ~$71 |
| **Reasoning tokens (Claude Sonnet)** | ~$31 | ~$378 | ~$1,890 |
| **APIM** *(optional)* | ~$3 | ~$15 | ~$50 |
| | | | |
| **Total (GPT-4o reasoning)** | **~$4,436** | **~$4,827** | **~$10,730** |
| **Total (GPT-4o-mini reasoning)** | **~$4,414** | **~$4,558** | **~$9,384** |
| **Total (Claude Sonnet reasoning)** | **~$4,447** | **~$4,922** | **~$10,953** |
| **Total (Hybrid 60/40)** | **~$4,419** | **~$4,657** | **~$9,896** |
| | | | |
| External AI % of total (GPT-4o) | ~0.9% | ~9.0% | ~20% |
| External AI % of total (GPT-4o-mini) | ~0.4% | ~3.6% | ~8.5% |

!!! success "Key Insight"
    At MKC's expected production scale (≤150 users), **Fabric F-SKU dominates 91%+ of spend** regardless of reasoning model choice. The absolute difference between the most expensive reasoning model (Claude 3.5 Sonnet) and the cheapest (GPT-4o-mini) is ~$269/month at production scale — less than 6% of total cost. **F-SKU tier selection has far greater financial impact than model selection.**

!!! info "Foundry Agent Service Pricing Uncertainty"
    Foundry Agent Service was in preview as of March 2026. Orchestration cost estimates above use a range of $0.001–$0.005 per agent run. At the low end, this is negligible; at the high end, it becomes the second largest external cost at scale. Monitor actual Foundry billing from day one and set Azure cost alerts on the `AI Foundry` resource group.

---

## References

| Resource | Description |
|----------|-------------|
| [Azure AI Foundry pricing](https://azure.microsoft.com/pricing/details/ai-foundry/) | Foundry Agent Service orchestration pricing — confirm before production budgeting |
| [Azure OpenAI pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) | GPT-4o / GPT-4o-mini token pricing (East US region) |
| [Microsoft Fabric pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/) | F-SKU monthly capacity costs and CU consumption model |
| [Azure APIM pricing](https://azure.microsoft.com/pricing/details/api-management/) | Per-call and data transfer costs for optional APIM positions |
| [Anthropic pricing (via Azure AI Foundry)](https://azure.microsoft.com/pricing/details/ai-foundry/) | Claude 3.5 Sonnet / Haiku token pricing via Foundry |
| [Foundry Agent Service Architecture](llm-architecture.md) | Full architecture — component roles, APIM positions, sanitisation pattern |
| [External Reasoning Models](alternative-llm-providers.md) | Model selection guide, data controls, and DPA checklist |
| [Fabric Data Agents](data-agents.md) | Data Agent role in the pipeline — what runs inside Fabric capacity |
