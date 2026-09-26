# Case Study 5 of 6: Enterprise Data and AI Platform

**Scenario:** Harborline Mutual Insurance Group (fictional, composite) is a ~$4.2B-premium US property-and-casualty carrier with three post-acquisition data estates, a 12-year-old Teradata warehouse whose notice date is 31 December 2026, SAS-based actuarial work, and 95 million unsearchable claim documents. Four pressures force the issue:
- a shadow-AI incident, in which claim notes were pasted into a public chatbot
- the NAIC AI bulletin and state AI rules for insurers
- the Teradata contract deadline
- an 18-day reserving close caused by fragmented data

**Angle:** Data architecture, AI/RAG, and FinOps. The central question is **hyperscaler-native data and AI stack versus a cross-cloud data platform (Databricks or Snowflake) running on top of one**, while keeping data in open formats so this is the last proprietary warehouse migration.

Part of the [Cloud Architecture](../README.md) portfolio.

## Scope Note

This case study runs **three** implementation tracks: Azure, AWS, and GCP. Within each track, the cloud's native data and AI stack is evaluated against **Databricks and Snowflake running on that cloud**. That is the decision most enterprises actually face for data and AI, and treating the cross-cloud platforms as a lens *inside* each track avoids pretending that they are clouds of their own. There is no private-cloud track. On-prem and sovereign options are reserved for Case Study 6.

Contrasts with earlier case studies:
- **Governance is sequenced first,** as security was in Case Study 4. Here, the governance and AI control plane is ranked driver #1 even though the assistant and the Teradata exit carry the dollars.
- **FinOps is a design requirement, not a closing chapter.** Consumption-priced warehouses and token-priced inference are both easy to overrun, so unit costs (per query, per claim) are NFRs from Step 3.

## Status

| Step | Status |
| --- | --- |
| 1. Business problem | Done — [`docs/problem-statement.md`](docs/problem-statement.md) |
| Current-state architecture | Done — [`docs/current-state.md`](docs/current-state.md); diagram not yet drawn |
| 2–3. Capabilities, requirements, and NFRs | Done — [`docs/requirements.md`](docs/requirements.md) |
| 4. Architecture options and styles | Done — [`docs/architecture-options-and-styles.md`](docs/architecture-options-and-styles.md), [ADR-001](adr/ADR-001-lakehouse-on-open-tables.md) to [ADR-005](adr/ADR-005-teradata-migration-approach.md), [target-style diagram (Mermaid)](diagrams/target-architecture-style.md): 6-R disposition (Guidewire retained via CDC, ECM retained and indexed, Teradata replatformed, Informatica/SSRS retired, SAS retired gradually); a lakehouse on open tables with a medallion layout; one governance plane for data and AI assets (it doubles as the NAIC model inventory); permission-aware retrieval (ACL metadata on every chunk, pre-filtered search, a final authorization check, a red-team suite); an AI gateway through which every model call passes (ZDR or in-tenancy models only, immutable audit, metering); Teradata migration by rationalizing, translating, re-layering, and dual-running per domain |
| 5. Vendor-neutral logical design | Done — [`docs/logical-design.md`](docs/logical-design.md), [ADR-006](adr/ADR-006-retrieval-scope-and-chunking.md), [ADR-007](adr/ADR-007-evaluation-and-release-gating.md), [ADR-008](adr/ADR-008-finops-allocation-and-unit-cost.md), [logical diagrams (Mermaid)](diagrams/logical-architecture.md): 22 logical components (ingestion, lakehouse, governance, AI layer, consumption, FinOps); a unified insurance data model (party/policy/claim with crosswalks, append-only reserve and payment facts for as-of loss triangles); six end-to-end flows, including the assistant request sequence. Tiered retrieval index (hot/reference/warm, on-demand promotion) with structure-aware chunks and citation anchors; a Claims-owned golden set with release gates (≥95% faithfulness, zero leaks, a 5% canary); FinOps with mandatory tags, per-workload compute pools, and gateway budgets decomposing the $0.05/query ceiling |
| 6. Azure implementation (native vs. Databricks/Snowflake) | Done — [`docs/azure-implementation.md`](docs/azure-implementation.md), [ADR-009](adr/ADR-009-azure-data-platform.md) to [ADR-014](adr/ADR-014-azure-network-identity-finops.md), [Azure diagram (Mermaid)](diagrams/azure-implementation-architecture.md): each layer compared across native Azure, Databricks, and Snowflake. Chosen stack: **Azure Databricks + Unity Catalog** at the core, with Azure AI Search (GA security-filter pattern), Foundry Data Zone US models (Azure OpenAI + Claude hosted on Azure, with a ZDR approval gate), API Management as the AI gateway, immutable Blob audit, Lakebridge for Teradata, ExpressRoute + Data Box. Fabric and Snowflake were rejected with reasons (Fabric's migration tooling doesn't name Teradata; Snowflake is the runner-up, with the strongest documented Teradata/BTEQ translation). The governance gap: the AI Search index sits outside Unity Catalog |
| 7. AWS implementation (native vs. Databricks/Snowflake) | Done — [`docs/aws-implementation.md`](docs/aws-implementation.md), [ADR-015](adr/ADR-015-aws-data-platform.md) to [ADR-020](adr/ADR-020-aws-network-identity-finops.md), [AWS diagram (Mermaid)](diagrams/aws-implementation-architecture.md): chosen stack is **AWS-native**. Components: S3 Tables (native Iceberg); Lake Formation column/cell security across Athena, Redshift, EMR, and Glue; Redshift Serverless (derived gold marts only); SageMaker Unified Studio; DMS Oracle CDC; SCT Teradata → Redshift including BTEQ → RSQL; OpenSearch with **native document-level security** plus an app claim filter; Bedrock US geo profiles (models requiring 30-day review retention excluded); a Harborline-built gateway with Guardrails and per-use-case application inference profiles; Object Lock audit. Databricks on AWS is the runner-up. Gaps: three governance planes aligned by identity, a custom gateway, and Redshift-shaped translated logic |
| 8. GCP implementation (native vs. Databricks/Snowflake) | Not started |
| 9. Decision matrix | Not started |
| 10. Recommended platform / target architecture | Not started |
| 11. Migration roadmap and ADRs | Not started |
| 12. Cost, FinOps, and risk analysis | Not started |

## Repository Structure

```
case-study-05-enterprise-data-ai/
│
├── README.md
├── docs/
│   ├── problem-statement.md   # organization, 4 forcing functions, 5 ranked drivers, the invariant (done)
│   ├── current-state.md       # sources, Informatica, Teradata/SAS, ECM, governance, $6.8M/yr cost baseline (done)
│   ├── requirements.md        # 8 capabilities, 12 NFRs, requirement/constraint/assumption/risk, priority weights (done)
│   ├── architecture-options-and-styles.md   # (Step 4) 6-R, 4 decisions, target style (done)
│   ├── logical-design.md                    # (Step 5) 22 components, insurance data model, 6 flows (done)
│   ├── azure-implementation.md              # (Step 6) 3-way comparison, Azure-track stack, deviations (done)
│   └── aws-implementation.md                # (Step 7) 3-way comparison, AWS-native stack, deviations (done)
├── adr/
│   ├── ADR-001-lakehouse-on-open-tables.md          # medallion lakehouse, Iceberg/Delta, second engine required (done)
│   ├── ADR-002-unified-governance-plane.md          # one catalog/policy plane for data + AI assets (done)
│   ├── ADR-003-permission-aware-retrieval.md        # ACL metadata, pre-filtered search, final authZ check (done)
│   ├── ADR-004-ai-gateway-and-model-access.md       # gateway, ZDR/in-tenancy admission, audit, metering (done)
│   ├── ADR-005-teradata-migration-approach.md       # rationalize, translate, re-layer, dual-run by domain (done)
│   ├── ADR-006-retrieval-scope-and-chunking.md      # hot/reference/warm tiers, structure-aware chunks, blue/green index (done)
│   ├── ADR-007-evaluation-and-release-gating.md     # golden set, metrics, gates, canary, risk tiers (done)
│   ├── ADR-008-finops-allocation-and-unit-cost.md   # tags, metering points, unit costs, $0.05/query budget (done)
│   ├── ADR-009-azure-data-platform.md               # Azure Databricks (vs Fabric, Snowflake on Azure) (done)
│   ├── ADR-010-azure-governance-plane.md            # Unity Catalog authoritative; Purview for M365 (done)
│   ├── ADR-011-azure-retrieval.md                   # Azure AI Search, security-filter pattern, 3 tiers (done)
│   ├── ADR-012-azure-models-and-ai-gateway.md       # Foundry Data Zone US + APIM gateway, ZDR gate (done)
│   ├── ADR-013-azure-ingestion-and-teradata-migration.md  # Oracle CDC tool, Doc Intelligence, Lakebridge (done)
│   ├── ADR-014-azure-network-identity-finops.md     # ExpressRoute + Data Box, Entra, tag enforcement (done)
│   ├── ADR-015-aws-data-platform.md                 # AWS-native Iceberg lakehouse (vs Databricks, Snowflake on AWS) (done)
│   ├── ADR-016-aws-governance-plane.md              # Lake Formation + linked AI inventory (done)
│   ├── ADR-017-aws-retrieval.md                     # OpenSearch with native DLS + app claim filter (done)
│   ├── ADR-018-aws-models-and-ai-gateway.md         # Bedrock US profiles, review-tier excluded, custom gateway (done)
│   ├── ADR-019-aws-ingestion-and-teradata-migration.md  # DMS, Textract, SCT incl. BTEQ→RSQL (done)
│   └── ADR-020-aws-network-identity-finops.md       # Direct Connect + Snowball, Identity Center⇄Entra, CUR (done)
├── diagrams/
│   ├── target-architecture-style.md                 # (Step 4) Mermaid reference (done)
│   ├── logical-architecture.md                      # (Step 5) Mermaid component model + assistant sequence (done)
│   ├── azure-implementation-architecture.md         # (Step 6) Mermaid Azure track (done)
│   └── aws-implementation-architecture.md           # (Step 7) Mermaid AWS track (done)
└── finance/
```
