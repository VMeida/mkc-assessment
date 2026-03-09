# AI, Data Science & MLOps

This section covers MKC's AI platform strategy, Data Agent deployment, and machine learning operations.

| Page | Description |
|------|-------------|
| [Enterprise LLM Architecture](llm-architecture.md) | Azure OpenAI Service design — Private Endpoint, APIM gateway, security model, deployment options |
| [Azure OpenAI Integration](azure-openai-integration.md) | Full model catalogue (GPT-4, GPT-4o, GPT-5), M365 Copilot vs. Azure OpenAI, Teams deployment patterns, Microsoft Graph integration diagrams |
| [Fabric Data Agents](data-agents.md) | Natural-language querying per workspace group — scope, query flow, security |
| [MLOps Pipeline](mlops-pipeline.md) | ML Notebooks, MLflow experiment tracking, model registry, model serving |
| [Feature Store](feature-store.md) | Gold-layer Delta feature tables for ML training and inference |
| [Cost Scenarios](cost-scenarios.md) | Fabric F-SKU capacity costs vs. Azure OpenAI per-token costs — three scenarios |

## AI Platform Summary

```mermaid
flowchart LR
    subgraph Users["MKC Users"]
        U1[Business<br/>users]
        U2[Data<br/>scientists]
    end
    subgraph Agents["Fabric Data Agents"]
        A1[Operational]
        A2[Analytics]
        A3[Financial]
        A4[Domain]
    end
    subgraph Gateway["AI Platform"]
        APIM[Azure APIM<br/>LLM Gateway]
        PE[Private<br/>Endpoint]
        AOAI[Azure OpenAI<br/>GPT-4o]
    end
    subgraph Models["Semantic Models"]
        SM[Sales · Financial<br/>Operations]
    end
    U1 -->|NL question| Agents
    U2 -->|LLM features| APIM
    Agents --> APIM
    APIM --> PE --> AOAI
    AOAI -->|DAX/SQL| SM
    SM -->|results| U1
```
