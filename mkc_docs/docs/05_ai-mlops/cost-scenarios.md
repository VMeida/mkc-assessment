# AI Cost Scenarios

## The Fundamental Cost Split

MKC's AI platform has **two completely separate cost components** that are often confused:

!!! info "Two Independent Cost Lines"
    **Microsoft Fabric F-SKU** = **fixed** monthly platform cost covering ALL data workloads (pipelines, lakehouses, notebooks, Power BI, semantic models). This cost exists regardless of AI usage.

    **Azure OpenAI** = **variable** per-token cost, billed separately based on actual LLM usage. This is additive to the Fabric cost.

## Azure OpenAI Pricing (East US, March 2026)

### GPT-4 Family

| Model | Input $/1M tokens | Output $/1M tokens | Best For |
|-------|------------------|-------------------|---------|
| **GPT-4o** | $2.50 | $10.00 | Complex multi-table NL→DAX, reasoning — **MKC primary** |
| **GPT-4o-mini** | $0.15 | $0.60 | Simple lookups, classification, high-volume queries |
| GPT-4 Turbo | $10.00 | $30.00 | Legacy; superseded by GPT-4o — avoid for new work |
| GPT-4 (0613) | $30.00 | $60.00 | Legacy; deprecating — migrate to GPT-4o |

### Reasoning Models (o-series)

| Model | Input $/1M tokens | Output $/1M tokens | Best For |
|-------|------------------|-------------------|---------|
| o1 | $15.00 | $60.00 | Multi-step reasoning, compliance logic, complex audit queries |
| o3-mini | $1.10 | $4.40 | Cost-efficient reasoning for structured data validation |

### GPT-5 (Preview — Estimated)

!!! warning "GPT-5 Pricing — Indicative Only"
    GPT-5 entered Azure OpenAI preview in early 2026. Prices below are estimates — confirm at the [Azure OpenAI pricing page](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) before using in budget models.

| Model | Input $/1M tokens | Output $/1M tokens | Best For |
|-------|------------------|-------------------|---------|
| GPT-5 | ~$15.00* | ~$60.00* | Autonomous agents, deep research, multi-document synthesis |
| GPT-5-mini | ~$1.50* | ~$6.00* | Balanced cost/quality at scale once GA |

### Embedding Models

| Model | Price $/1M tokens | Best For |
|-------|------------------|---------|
| text-embedding-3-large | $0.13 | Semantic search, RAG pipeline |
| text-embedding-3-small | $0.02 | High-volume embedding |

## Token Consumption Per Data Agent Query

Each Data Agent query consumes tokens across four components:

| Component | Tokens (GPT-4o) | Description |
|-----------|----------------|-------------|
| System prompt (schema + instructions) | ~2,000 input | Semantic model schema, few-shot DAX examples, RLS context |
| User question | ~50 input | Average NL question |
| Few-shot DAX examples | ~1,000 input | 3–5 grounding examples per model |
| Generated DAX/SQL response | ~300 output | The generated query |
| **Total per query** | **~3,350 tokens** | **~$0.011/query (GPT-4o)** |
| | | **~$0.0007/query (GPT-4o-mini)** |

!!! tip "Optimisation Lever"
    The system prompt (schema context) is the largest cost driver. Caching the compiled system prompt using Azure OpenAI **Prompt Caching** (50% discount on repeated prompt prefixes) can reduce per-query cost by 30–40%.

## Three Deployment Scenarios

=== "Pilot (25 users)"

    | Item | Value |
    |------|-------|
    | Active users | 25 |
    | Queries/user/day | 5 |
    | Queries/month | 3,750 |
    | **Fabric F32 (Prod)** | **$4,194** |
    | **Fabric F8 (Dev, paused)** | **~$200** |
    | AOAI — GPT-4o tokens | ~$41 |
    | AOAI — GPT-4o-mini tokens | ~$3 |
    | Azure APIM | ~$3 |
    | **Total (GPT-4o path)** | **~$4,438/month** |
    | **Total (GPT-4o-mini path)** | **~$4,400/month** |
    | Token cost as % of total | 0.9% / 0.07% |

    > Token cost is negligible at pilot scale — the F-SKU dominates 99%+ of spend.

=== "Production (150 users)"

    | Item | Value |
    |------|-------|
    | Active users | 150 |
    | Queries/user/day | 10 |
    | Queries/month | 45,000 |
    | **Fabric F32 (Prod)** | **$4,194** |
    | **Fabric F8 (Dev, paused)** | **~$200** |
    | AOAI — GPT-4o tokens | ~$495 |
    | AOAI — GPT-4o-mini tokens | ~$32 |
    | Azure APIM | ~$15 |
    | **Total (GPT-4o path)** | **~$4,904/month** |
    | **Total (GPT-4o-mini path)** | **~$4,441/month** |
    | Token cost as % of total | 10.1% / 0.72% |

    > At production scale GPT-4o adds ~12% to total cost. GPT-4o-mini keeps AI costs under 1%.

=== "Scale (500 users)"

    | Item | Value |
    |------|-------|
    | Active users | 500 |
    | Queries/user/day | 15 |
    | Queries/month | 225,000 |
    | **Fabric F64 (Prod)** | **$8,388** |
    | **Fabric F8 (Dev, paused)** | **~$200** |
    | AOAI — GPT-4o tokens | ~$2,475 |
    | AOAI — GPT-4o-mini tokens | ~$158 |
    | Azure APIM | ~$50 |
    | **Total (GPT-4o path)** | **~$11,113/month** |
    | **Total (GPT-4o-mini path)** | **~$8,796/month** |
    | Token cost as % of total | 22.3% / 1.8% |

    > At scale, GPT-4o token cost becomes significant. Hybrid routing (below) is recommended.

## Cost Optimisation — Intelligent Routing

Route queries by complexity using a lightweight classifier:

| Traffic Mix | Cost/Query | Monthly Cost (225K queries) |
|------------|-----------|---------------------------|
| 100% GPT-4o | $0.0110 | $2,475 |
| 100% GPT-4o-mini | $0.0007 | $158 |
| **60% mini + 40% GPT-4o** (hybrid) | **$0.0046** | **$1,040** |
| 100% o1 (reasoning) | $0.0705 | $15,863 |
| 100% o3-mini (reasoning) | $0.0052 | $1,170 |
| 100% GPT-5* (estimated) | ~$0.0705 | ~$15,863 |
| 100% GPT-5-mini* (estimated) | ~$0.0071 | ~$1,598 |

Hybrid routing (GPT-4o-mini + GPT-4o) saves **58% vs. all-GPT-4o** with minimal quality impact on simple queries. o-series and GPT-5 models are only cost-justified for specialised tasks (compliance reasoning, autonomous agents) — not for standard NL→DAX at MKC's current query volumes.

```python
# Hybrid routing — GPT-4o-mini classifies, then routes
SIMPLE_THRESHOLD = "SIMPLE"

def classify_and_route(question: str) -> str:
    # Step 1: Cheap classification (~100 tokens = $0.00002)
    complexity = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user",
                   "content": f"Simple or Complex? Reply one word only.\n{question}"}],
        max_tokens=5
    ).choices[0].message.content.strip().upper()

    # Step 2: Route accordingly
    model = "gpt-4o-mini" if complexity == SIMPLE_THRESHOLD else "gpt-4o"
    return generate_dax(question, model=model)
```

## Provisioned Throughput Units (PTU)

At high query volumes, **Azure OpenAI PTU** reservations become cheaper than pay-as-you-go:

| Volume | PAYG Cost | PTU Estimate | Savings |
|--------|----------|-------------|---------|
| 45,000 queries/month (GPT-4o) | ~$495 | ~$450 | ~9% |
| 225,000 queries/month (GPT-4o) | ~$2,475 | ~$2,000 | ~19% |
| 225,000 queries/month (GPT-4o-mini) | ~$158 | Not justified | — |

**PTU break-even:** ~130,000 GPT-4o queries/month. Below that, PAYG is cheaper.

## Cost Summary Table

| | Pilot | Production | Scale |
|---|---|---|---|
| **Users** | 25 | 150 | 500 |
| **Queries/month** | 3,750 | 45,000 | 225,000 |
| **Fabric SKU** | F32+F8 | F32+F8 | F64+F8 |
| **Fabric cost** | $4,394 | $4,394 | $8,588 |
| **AOAI (GPT-4o)** | $41 | $495 | $2,475 |
| **AOAI (GPT-4o-mini)** | $3 | $32 | $158 |
| **APIM** | $3 | $15 | $50 |
| **Total (GPT-4o)** | **~$4,438** | **~$4,904** | **~$11,113** |
| **Total (mini / hybrid)** | **~$4,400** | **~$4,441** | **~$8,796** |
| Token % of total (GPT-4o) | 0.9% | 10.1% | 22.3% |
| Token % of total (mini) | 0.07% | 0.72% | 1.8% |

!!! success "Key Insight"
    At MKC's expected production scale (≤150 active users), **Fabric capacity dominates 99%+ of spend**. Azure OpenAI token costs are marginal. The decision on which F-SKU to purchase has far more financial impact than model selection. GPT-4o-mini delivers excellent NL→DAX quality for simple queries at 1/16th the cost.
