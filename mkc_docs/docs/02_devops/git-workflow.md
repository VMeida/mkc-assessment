# Git Workflow

## Fabric Git Integration

Microsoft Fabric natively integrates with **Azure DevOps Git** or **GitHub** repositories. Each Fabric workspace is connected to a specific branch of the repository, enabling workspace items (Notebooks, Dataflow Gen2, Pipelines, Semantic Models) to be version-controlled as YAML/JSON definition files.

```mermaid
flowchart LR
    A[Developer<br/>local clone] -->|git push feature/xyz| B[feature branch]
    B -->|Pull Request| C[dev branch]
    C -->|Fabric Sync| D["Fabric Dev Workspace<br/>(F8)"]
    D -->|PR + DQ tests pass| E[main branch]
    E -->|Manual approval gate| F["Fabric Prod Workspace<br/>(F32)"]
```

## Branch Strategy

| Branch | Synced Workspace | Purpose |
|--------|-----------------|---------|
| `feature/*` | None (PR only) | Developer sandbox for new features |
| `dev` | Dev Workspace (F8) | Integration of in-progress work; UAT with last-90-days snapshot |
| `main` | Prod Workspace (F32) | Production-deployed; requires manual GitHub Environments approval |

## Repository Structure

```
mkc-fabric/
├── workspaces/
│   ├── dev/
│   │   ├── notebooks/
│   │   │   ├── bronze_silver/
│   │   │   └── silver_gold/
│   │   ├── pipelines/
│   │   ├── dataflows/
│   │   └── semantic_models/
│   ├── prod/
│   │   └── (same structure)
├── .github/
│   └── workflows/
│       ├── ci.yml           # lint, DQ check on PR
│       └── promote.yml      # workspace promotion on merge to main
├── scripts/
│   ├── deploy.py            # Fabric REST API workspace deploy
│   └── dq_check.py          # data quality smoke tests
└── README.md
```

## Pull Request Rules

1. **feature → dev only** — all feature branches target `dev` via PR; direct PRs to `main` are not permitted
2. **Minimum 1 reviewer** for any change to `dev` or `main`
3. **CI checks must pass** before merge (lint + DQ smoke test + coverage gate)
4. **No direct commits** to `main`
5. **dev → main requires approval** — the `main` branch is protected by a GitHub Environments approval gate (replaces the former Test stage gate)
6. **Squash merges** preferred — keeps `main` history clean

## Workspace-to-Branch Mapping

Fabric workspaces are configured in the Fabric portal under **Workspace Settings → Git Integration**:

| Workspace | Repository Branch | Auto-sync |
|-----------|------------------|-----------|
| MKC-Dev | `dev` | On push |
| MKC-Prod | `main` | Manual after approval |

!!! tip "Notebook Parameters"
    Use Fabric Notebook parameters (top-cell `parameters` tag) combined with environment variable substitution in CI/CD to point notebooks at Dev vs. Prod OneLake paths without code changes.
