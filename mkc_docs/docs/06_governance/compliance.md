# Compliance

## MKC Compliance Requirements

As an agricultural co-operative handling producer, financial, and employee data, MKC must comply with:

| Standard | Scope | Relevance to MKC |
|----------|-------|-----------------|
| **SOC 2 Type II** | Service organisation controls | Microsoft Fabric and Azure OpenAI both hold SOC 2 Type II attestation |
| **HIPAA** | Health information protection | HAVEN HR system may contain employee health benefit data |
| **ISO 27001** | Information security management | Enterprise security baseline for IT infrastructure |
| **GDPR** | EU data protection | Producer data for any EU-linked operations |
| **CCPA** | California consumer privacy | Any California-based customers or producers |

## Platform Compliance Posture

### Microsoft Fabric

| Control | Status |
|---------|--------|
| SOC 2 Type II | Attested — Microsoft publishes reports via Service Trust Portal |
| Data residency | Configurable — MKC capacity deployed in US-Central region; data stays in USA |
| Encryption at rest | AES-256 for all OneLake storage |
| Encryption in transit | TLS 1.2+ for all API connections |
| Audit logging | All workspace actions logged to Microsoft 365 Unified Audit Log |

### Azure OpenAI Service

| Control | Status |
|---------|--------|
| SOC 2 Type II | Attested |
| HIPAA BAA | Available via Microsoft Healthcare agreement |
| ISO 27001 | Certified |
| GDPR | Compliant via EU Data Boundary |
| No training on customer data | Confirmed via Azure OpenAI Data Protection Addendum |
| Private Endpoint | All MKC traffic on Microsoft backbone — no public internet |
| Content filtering | Enabled — harmful content categories blocked at API level |

## Data Classification Policy

| Data Category | Example | Classification | Retention |
|--------------|---------|---------------|-----------|
| Public market data | Published grain prices | Public | 7 years |
| Operational transactional | Grain sale quantities | Internal | 7 years |
| Customer financial | AR balances, credit limits | Confidential | 7 years |
| Employee compensation | Salary, hourly rate | Highly Confidential | 7 years (HR holds) |
| Producer contact | Name, address, farm details | Confidential | 7 years |

## Data Retention & Deletion

| Layer | Retention Period | Deletion Method |
|-------|-----------------|----------------|
| Bronze Lakehouse | 7 years | Delta `VACUUM` with retention policy |
| Silver Lakehouse | 7 years | Delta `VACUUM` |
| Gold Lakehouse | Indefinite (aggregated, no PII) | Manual review |
| Azure OpenAI prompts | 0 days (not stored by Microsoft) | Not retained per DPA |
| APIM audit log | 90 days | Log Analytics workspace retention policy |
| Purview scan metadata | Indefinite (no raw data) | Manual purge |

## GDPR Right to Erasure

For producer data covered by GDPR, deletion is handled at the Silver layer:

1. Identify all Silver tables containing the producer's data via Purview lineage
2. Execute `DELETE FROM Silver.dim_producer WHERE producer_id = '{id}'`
3. Delta's MERGE INTO on next ETL run will propagate deletion to Gold
4. Semantic model cache clears on next refresh
5. Document deletion in audit log

!!! warning "Bronze is Append-Only"
    Because Bronze is an append-only audit trail, GDPR deletion requests cannot be applied to Bronze. Bronze data for a GDPR-subject must be flagged with a `gdpr_delete_flag` column and explicitly excluded from Silver transformation queries. This is the standard approach for Delta Lake GDPR compliance.

---

## References

| Resource | Description |
|----------|-------------|
| [Microsoft Service Trust Portal](https://servicetrust.microsoft.com/) | SOC 2, ISO 27001, HIPAA, and other compliance audit reports for Microsoft services |
| [Microsoft compliance offerings](https://learn.microsoft.com/en-us/compliance/regulatory/offering-home) | Full catalogue of regulatory certifications held by Microsoft cloud services |
| [Azure OpenAI data privacy and security](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy) | Data Protection Addendum — no training on customer prompts, GDPR compliance |
| [Microsoft Fabric security documentation](https://learn.microsoft.com/en-us/fabric/security/security-overview) | Encryption, network isolation, audit logging, and compliance posture for Fabric |
| [GDPR compliance on Azure](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-gdpr) | Azure tools and guidance for meeting GDPR data subject rights requirements |
| [Delta Lake GDPR delete pattern](https://learn.microsoft.com/en-us/azure/databricks/security/privacy/gdpr-delta) | Right-to-erasure implementation using Delta MERGE and flagging in append-only tables |
