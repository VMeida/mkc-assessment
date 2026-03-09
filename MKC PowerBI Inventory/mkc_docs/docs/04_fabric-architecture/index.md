# Fabric Architecture & Workspace Design

Technical deep-dive into MKC's Microsoft Fabric platform design.

| Page | Description |
|------|-------------|
| [Medallion Layers](medallion.md) | Bronze / Silver / Gold design decisions and transformation engine choices |
| [OneLake & Delta](onelake.md) | ADLS Gen2 storage, Delta Parquet format, vendor independence |
| [Star Schema](star-schema.md) | 8 shared dimensions and 9 fact tables |
| [Workspace Design](workspace-design.md) | Fabric capacity, workspace topology, F-SKU selection |
| [Vendor Independence](vendor-independence.md) | Anti-lock-in strategy across storage, BI, ingestion, and LLM |
