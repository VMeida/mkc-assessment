# Plan: Deploy MkDocs to Azure Static Web Apps

## Context

The project has a fully configured MkDocs site (`mkc_docs/`) with the Material theme, Mermaid diagrams, and data-driven content generated from an Excel file. There is currently no CI/CD or deployment infrastructure. The goal is to deploy the static site to Azure, restricted to internal users via Entra ID, with automated publishing on every push via Azure DevOps Pipelines.

**Recommended service: Azure Static Web Apps (SWA)**
- Built-in Entra ID authentication (no code, just config)
- Native Azure DevOps pipeline integration
- Free tier is sufficient for documentation
- Global CDN + custom domain + SSL included
- Designed for static sites like MkDocs output

---

## Files to Create

### 1. `azure-pipelines.yml` (repo root)

CI/CD pipeline triggered on pushes to `main`. Builds the site and deploys to SWA.

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.12'
    displayName: 'Use Python 3.12'

  - script: pip install -r requirements.txt
    displayName: 'Install dependencies'

  - script: python mkc_docs/scripts/extract_excel.py
    displayName: 'Generate data-driven markdown from Excel'

  - script: cd mkc_docs && mkdocs build
    displayName: 'Build MkDocs static site'

  - task: AzureStaticWebApp@0
    displayName: 'Deploy to Azure Static Web Apps'
    inputs:
      app_location: 'mkc_docs/site'
      skip_app_build: true
      azure_static_web_apps_api_token: $(AZURE_STATIC_WEB_APPS_API_TOKEN)
```

**Pipeline variable required:** `AZURE_STATIC_WEB_APPS_API_TOKEN` (secret, set in Azure DevOps pipeline settings).

---

### 2. `mkc_docs/docs/staticwebapp.config.json`

Placed inside the `docs/` source dir so MkDocs copies it to `site/` during build. This file enforces Entra ID authentication on all routes.

```json
{
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/<TENANT_ID>/v2.0",
          "clientIdSettingName": "AAD_CLIENT_ID",
          "clientSecretSettingName": "AAD_CLIENT_SECRET"
        }
      }
    }
  },
  "routes": [
    {
      "route": "/*",
      "allowedRoles": ["authenticated"]
    }
  ],
  "responseOverrides": {
    "401": {
      "statusCode": 302,
      "redirect": "/.auth/login/aad"
    }
  }
}
```

Placeholders `<TENANT_ID>`, `AAD_CLIENT_ID`, and `AAD_CLIENT_SECRET` are filled in during Azure setup (see below).

---

## Azure Setup (One-Time, Manual)

These steps are done once in Azure Portal or via the `az` CLI before the first pipeline run:

### Step 1 — Create the Static Web App resource
```bash
az staticwebapp create \
  --name mkc-docs \
  --resource-group <your-rg> \
  --location "West Europe" \
  --sku Free
```

### Step 2 — Get the deployment token
In Azure Portal → Static Web App → **Manage deployment token**. Copy the token.

Add it as a **secret pipeline variable** in Azure DevOps:
- Pipeline → Edit → Variables → `AZURE_STATIC_WEB_APPS_API_TOKEN` (secret)

### Step 3 — Register an Entra ID App Registration
In Azure Portal → Entra ID → App Registrations → New registration:
- Name: `mkc-docs`
- Redirect URI: `https://<your-swa-hostname>/.auth/login/aad/callback`

Copy the **Tenant ID** and **Client ID**.
Under "Certificates & secrets", create a client secret.

### Step 4 — Configure SWA authentication
In Azure Portal → Static Web App → Configuration → add these Application Settings:
- `AAD_CLIENT_ID` = `<client-id from Step 3>`
- `AAD_CLIENT_SECRET` = `<client-secret from Step 3>`

Then update `staticwebapp.config.json` with your real `<TENANT_ID>`.

---

## Verification

1. Push to `main` → Azure DevOps pipeline runs automatically
2. Pipeline stages: Install deps → generate Excel-driven markdown → `mkdocs build` → deploy
3. Visit the SWA URL (e.g. `https://nice-name-xxxx.azurestaticapps.net`) → should redirect to Microsoft login
4. Log in with an Entra ID tenant account → docs are visible
5. Unauthenticated access returns 302 redirect to login page
