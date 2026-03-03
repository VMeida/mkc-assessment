# CI/CD Pipelines

## Pipeline Architecture

Two GitHub Actions workflows handle the full CI/CD lifecycle:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Pull Request to `dev` or `main` | Lint notebooks, run DQ checks, validate pipeline YAML |
| `promote.yml` | Push to `main` (after PR merge) | Deploy workspace items to Test via Fabric REST API; gate before Prod |

## `ci.yml` — Continuous Integration

```yaml
name: MKC Fabric CI

on:
  pull_request:
    branches: [dev, main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install nbqa ruff
      - name: Lint notebooks
        run: nbqa ruff workspaces/dev/notebooks/ --select E,W,F

  data-quality:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install great_expectations sqlalchemy pyodbc
      - name: Run DQ smoke tests
        run: python scripts/dq_check.py --env dev
        env:
          SQL_CONNECTION_STRING: ${{ secrets.DEV_SQL_CONNECTION_STRING }}

  validate-pipelines:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate pipeline JSON/YAML definitions
        run: python scripts/validate_definitions.py workspaces/dev/pipelines/
```

## `promote.yml` — Workspace Promotion

```yaml
name: MKC Fabric Promote

on:
  push:
    branches: [main]

jobs:
  deploy-to-test:
    runs-on: ubuntu-latest
    environment: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install requests msal
      - name: Deploy to Test Workspace
        run: python scripts/deploy.py --workspace MKC-Test --branch main
        env:
          FABRIC_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FABRIC_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
          FABRIC_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}

  deploy-to-prod:
    runs-on: ubuntu-latest
    needs: deploy-to-test
    environment: production   # requires manual approval in GitHub Environments
    steps:
      - name: Deploy to Prod Workspace
        run: python scripts/deploy.py --workspace MKC-Prod --branch release/v${{ github.ref_name }}
        env:
          FABRIC_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FABRIC_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
          FABRIC_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
```

## Fabric REST API Deployment Script

The `deploy.py` script uses the **Fabric REST API** to update workspace items from the Git repository:

```python
import requests, msal, os, json

TENANT_ID = os.environ["FABRIC_TENANT_ID"]
CLIENT_ID = os.environ["FABRIC_CLIENT_ID"]
CLIENT_SECRET = os.environ["FABRIC_CLIENT_SECRET"]
FABRIC_API = "https://api.fabric.microsoft.com/v1"

def get_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    result = app.acquire_token_for_client(scopes=["https://api.fabric.microsoft.com/.default"])
    return result["access_token"]

def update_workspace_from_git(workspace_id: str, token: str):
    """Trigger a Git update (pull from branch) on a Fabric workspace."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(
        f"{FABRIC_API}/workspaces/{workspace_id}/git/updateFromGit",
        headers=headers,
        json={"conflictResolution": {"conflictResolutionType": "PreferWorkspace"}}
    )
    r.raise_for_status()
    print(f"Workspace {workspace_id} updated from Git — status {r.status_code}")
```

## Secrets Management

All secrets are stored in **GitHub Environments** (never in repository files) and injected as environment variables at runtime:

| Secret | Purpose |
|--------|---------|
| `FABRIC_CLIENT_ID` | Service Principal app ID |
| `FABRIC_CLIENT_SECRET` | Service Principal secret (rotated quarterly) |
| `FABRIC_TENANT_ID` | Azure tenant ID |
| `DEV_SQL_CONNECTION_STRING` | Read-only connection for DQ smoke tests |

!!! warning "No Direct Prod Deployments"
    The `deploy-to-prod` job requires a manual approval step via **GitHub Environments** protection rules. No code reaches Prod without an explicit human sign-off.
