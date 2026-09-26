# Step 6: Azure Implementation (native vs. Databricks vs. Snowflake on Azure)

## Purpose of This Step

This step maps the 22 logical components from [Step 5](logical-design.md) onto Azure. The case study's scope note calls for a second lens inside each track: every layer is compared three ways, then one **Azure-track stack** is chosen:

- **Azure-native** (Microsoft Fabric, Purview, Azure AI Search, Azure AI Foundry, API Management)
- **Azure Databricks**
- **Snowflake on Azure**

Steps 7 and 8 repeat this independently for AWS and GCP.

## Findings from Current Documentation (September 2026)

These findings drive the choices below. Each is cited in the relevant ADR.

1. **Azure AI Search document-level security.**
   - The **security-filter pattern** (the application passes identity attributes as a query filter) is **generally available**.
   - Native Entra ACL/RBAC enforcement at query time, Purview sensitivity-label enforcement, and SharePoint ACLs are all **preview**.
   - The native ACL ingestion supports only **ADLS Gen2, Blob, SharePoint, and OneLake** sources.

   Harborline's ECM is none of these, so on Azure the ADR-003 design is implemented with the GA security-filter pattern and Harborline's own ACL attributes. That is what ADR-003 specified anyway.
2. **Models and data terms on Azure AI Foundry.**
   - Prompts and completions are **not used to train** models.
   - **Data Zone** deployments created in a US resource process prompts "anywhere within the United States".
   - **Zero data retention** (modified abuse monitoring) is available to managed customers **by application**.
   - **Claude models are offered "Hosted on Azure"** with Data Zone Standard (US), where prompts and outputs are processed on Azure infrastructure. **Anthropic acts as an independent data processor** under Anthropic's DPA and commercial terms.
   - So there are **two frontier model families with US-zone processing** available through one Azure control plane, subject to contract steps.
3. **Teradata translation.**
   - The **Fabric Data Warehouse Migration Assistant** lists Synapse dedicated pools, SQL Server, and "other SQL database platforms". **Teradata is not named**, and the direct-connection path is preview.
   - **Databricks Lakebridge** and **Snowflake SnowConvert AI** both target Teradata. SnowConvert's documentation includes Teradata **BTEQ** translation.
4. **Governance GA milestones in 2026.**
   - **OneLake security** (role-based row and column security across Fabric engines) reached GA in about May 2026.
   - **Unity Catalog ABAC row filtering and column masking, governed tags, and automated data classification** reached GA on 13 May 2026.
5. **CDC from Guidewire's Oracle.** **Fabric mirroring for Oracle** uses LogMiner and requires the on-premises data gateway.
6. **Snowflake Cortex on Azure.** Cross-region inference can be bounded to `AZURE_US`. Customer data "remains stored only in the region where your account is located", and nothing is persisted in the processing region.

## Three-Way Comparison by Layer

| Layer (Step 5 components) | Azure-native | Azure Databricks | Snowflake on Azure | Azure-track choice |
|---|---|---|---|---|
| Lakehouse storage and engines (D1–D4) | OneLake (Delta, with Iceberg metadata virtualization), Fabric Lakehouse/Warehouse, capacity-billed | Delta/UniForm on ADLS; SQL warehouses, jobs, notebooks; DBU-billed per workload | Iceberg tables (can live in OneLake or ADLS) or native tables; credit-billed warehouses | **Databricks** ([ADR-009](../adr/ADR-009-azure-data-platform.md)) |
| Governance plane (G1–G4) | OneLake security (GA 2026) + Purview. AI assets split across Foundry and Purview | **Unity Catalog**: ABAC, governed tags, and classification (GA 13 May 2026). Also governs models and vector indexes as catalog objects | Horizon: tags, masking, row access policies. Cortex objects governed in-account | **Unity Catalog** ([ADR-010](../adr/ADR-010-azure-governance-plane.md)) |
| Retrieval index (A2–A3) | **Azure AI Search**: hybrid (BM25 + vector) + semantic ranker, security filters GA | Mosaic AI Vector Search: governed by Unity Catalog, metadata filters | Cortex Search: in-account, with filters | **Azure AI Search** ([ADR-011](../adr/ADR-011-azure-retrieval.md)) |
| Models (A5) | **Foundry**: Azure OpenAI Data Zone US; Claude hosted on Azure, Data Zone US | External models via its gateway (to Foundry), plus hosted open-weight models | Cortex models, with cross-region bounded to `AZURE_US` | **Foundry Data Zone US** ([ADR-012](../adr/ADR-012-azure-models-and-ai-gateway.md)) |
| AI gateway (A4) | **API Management AI gateway**: token-limit policies, LLM logging, semantic cache | Mosaic AI Gateway: usage tracking, inference tables, guardrails | Limited; non-Snowflake apps would still need a gateway | **API Management** ([ADR-012](../adr/ADR-012-azure-models-and-ai-gateway.md)) |
| CDC from Guidewire (I1) | Fabric mirroring for Oracle (LogMiner + gateway) | Third-party log-based CDC into bronze | Third-party CDC or connectors | **Log-based CDC tool → ADLS bronze** ([ADR-013](../adr/ADR-013-azure-ingestion-and-teradata-migration.md)) |
| Teradata translation (ADR-005) | Migration Assistant does not name Teradata | **Lakebridge** | **SnowConvert AI** (includes BTEQ) | **Lakebridge**, with SnowConvert noted as the stronger documented Teradata tool |
| Notebooks (C2, the SAS replacement) | Fabric notebooks | Databricks notebooks + MLflow | Snowflake Notebooks | **Databricks** |
| BI (C1) | Power BI | Tableau/Power BI via SQL warehouse | Tableau via Snowflake | **Tableau retained** (per Step 4) on Databricks SQL |
| FinOps (F1) | Capacity metrics (coarse per workspace) + Cost Management | **System billing tables + tags per job/warehouse** + budgets | Resource monitors + tags | **Databricks system tables + Cost Management + APIM token metrics** ([ADR-014](../adr/ADR-014-azure-network-identity-finops.md)) |

**The pattern that emerges** is a data-and-AI platform (Databricks) at the core, with **Azure-native services where Azure is stronger**:
- Azure AI Search for hybrid and lexical retrieval at 40M-document scale
- Foundry for model access under Data Zone US terms
- API Management as the enterprise AI gateway
- Entra ID as the identity provider

This is a genuine hybrid of the two lenses, not a pure-native or pure-cross-cloud stack.

## Service Mapping (all 22 components)

| # | Component | Azure-track implementation |
|---|---|---|
| I1 | CDC Connector | Log-based Oracle CDC tool (for example, a commercial replication product) → Delta bronze on ADLS, ≤ 15 min |
| I2 | Batch Ingest | Databricks Auto Loader from ADLS landing (Coastal files, vendor feeds) |
| I3 | Document Pipeline | Databricks jobs: ECM change feed → **Azure AI Document Intelligence** (OCR, layout) → structure-aware chunking → **Azure OpenAI embeddings (Data Zone US)** → push to Azure AI Search tiers ([ADR-011](../adr/ADR-011-azure-retrieval.md)) |
| I4 | ACL Sync | Databricks job reading ClaimCenter assignments (via CDC) and ECM permissions → updates the ACL fields in AI Search (merge, no re-embedding) |
| D1–D3 | Bronze / Silver / Gold | Delta tables with **UniForm** (Iceberg-readable) on ADLS Gen2, governed in Unity Catalog |
| D4 | Transformation Orchestrator | Lakeflow Declarative Pipelines / SQL transformations in Git, with data-quality expectations blocking gold |
| D5 | Migration Reconciler | Databricks jobs comparing Teradata extracts with the lakehouse; results in a UC table; sign-off recorded in G4 |
| G1 | Catalog and Policy Engine | **Unity Catalog** (ABAC row filters and column masks driven by governed tags). An entitlement service exposes UC-derived entitlements to A2 |
| G2 | Classification | Unity Catalog data classification (GA) → governed tags. Human confirmation for core entities |
| G3 | Lineage | Unity Catalog lineage (tables, notebooks, jobs, models) |
| G4 | AI Inventory | UC-registered models, prompts (as versioned assets), evaluation runs (MLflow), plus a use-case register table. APIM reads approvals from it |
| A1 | Claims Assistant | App on **Azure App Service** (or Container Apps), launched from ClaimCenter, with Entra SSO |
| A2 | Retrieval Service | Container app: entitlement lookup → AI Search query with the **security filter** → semantic rerank → final authorization check against ClaimCenter/ECM APIs |
| A3 | Retrieval Index | **Azure AI Search**: separate indexes for hot (hybrid + semantic ranker), reference (hybrid, versioned), and warm (lexical only). Blue/green index versions for embedding changes |
| A4 | AI Gateway | **Azure API Management AI gateway**: Entra auth, `llm-token-limit` per use case, emits LLM logs, and runs a policy check against G4 approvals. Redaction runs as a pre-processing step |
| A5 | Model Endpoints | **Foundry Data Zone US deployments**: Azure OpenAI models and Claude hosted on Azure. **Modified abuse monitoring (ZDR) approval is a go-live prerequisite** |
| A6 | AI Audit Store | APIM and application logs → **immutable (WORM) Blob storage**, 7-year time-based retention with legal hold, plus a Delta copy for compliance analytics |
| A7 | Evaluation Harness | Databricks MLflow GenAI evaluation (golden set, scorers using a different model) plus a red-team job; results registered in G4 |
| C1 | SQL and BI | Databricks SQL warehouses (serverless) for Tableau; Power BI optional |
| C2 | Notebooks | Databricks notebooks (Python/SQL), with SAS reading via connectors during the transition |
| C3 | Regulatory exports | Databricks jobs → governed export locations, registered in UC |
| F1 | FinOps Metering | Databricks system billing tables (per job, warehouse, and tag) + APIM token metrics + Azure Cost Management, with mandatory tags enforced by Azure Policy |

## Why Not Pure-Native (Fabric) or Snowflake on This Track

- **Fabric** is the most integrated Microsoft option and the cheapest to operate *if* Microsoft's catalog governed everything. On this track, however:
  - AI assets are governed across Foundry and Purview rather than in one plane (weakening ADR-002).
  - Teradata is not a named source for Fabric's migration tooling.
  - Capacity billing makes per-use-case cost attribution (ADR-008) coarser.

  It stays the right answer for a Microsoft-standardized organization without a Teradata exit. Harborline has both.
- **Snowflake on Azure** has the strongest documented Teradata translation (SnowConvert AI, including BTEQ). It would also absorb the 2024 account cleanly, and Cortex keeps inference bounded to `AZURE_US`. It loses on this track because:
  - the actuarial and data-science workbench replacing SAS is weaker than Databricks'
  - its retrieval and gateway story would still need API Management and AI Search for non-Snowflake applications

  Snowflake is carried forward as a credible alternative, and its Teradata-tooling advantage is scored in Step 9.

## Network, Identity, and Security

- **Regions:** East US 2 (primary) with Central US for DR. All AI resources use US Data Zone deployments (NFR-4).
- **Hartford to Azure:**
  - **ExpressRoute** (redundant circuits) for CDC, ECM document flow, and the dual-run period.
  - **Azure Data Box** for the one-time bulk copy of historical Teradata data (~180 TB compressed), rather than pushing it over the circuit.
- **Private networking:** Databricks VNet injection and Private Link. Private endpoints for AI Search, Foundry, APIM (internal mode), ADLS, and Key Vault. No public endpoints.
- **Identity:** Entra ID with SCIM to Databricks. Managed identities for services. Users' Entra tokens are passed through, so entitlements are always the user's own.
- **The 2024 Snowflake account** is retired on this track: data inventoried, legitimate datasets re-landed in the lakehouse, account closed.

## Observability

Azure Monitor and Log Analytics (APIM, AI Search, App Service), Databricks system tables (jobs, queries, audit), and the evaluation dashboards. Four alerts matter most:
- ACL-sync lag above 15 minutes
- any final-authorization-check denial (a security event)
- faithfulness drift in production sampling
- cost per query above the ADR-008 budget

## Alignment Check against Steps 4–5

All 22 components are mapped. Deviations carried to Step 9:

| Expectation | Azure-track reality | Treatment |
|---|---|---|
| One governance plane reaches retrieval ([ADR-002](../adr/ADR-002-unified-governance-plane.md)) | Unity Catalog governs data, models, and evaluations, but the **AI Search index sits outside it**. ACL attributes come from UC tables, and the index is registered as an external asset | Partial. Scored under governance fit |
| Open format with a named second engine ([ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md)) | Delta + UniForm (Iceberg metadata). Second engines: Fabric (OneLake shortcut) and any Iceberg reader | Met. The read path is to be demonstrated in the pilot |
| ZDR models in the US ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)) | Data Zone US available. ZDR requires an **approved** modified-abuse-monitoring application. Claude's processor is Anthropic | Met, subject to a contract gate before go-live |
| Engine-level Teradata translation fit ([ADR-005](../adr/ADR-005-teradata-migration-approach.md)) | Lakebridge (Databricks). Microsoft's own tooling does not name Teradata | Met via the platform, not via Azure itself |

## Diagram

See [`diagrams/azure-implementation-architecture.md`](../diagrams/azure-implementation-architecture.md) (Mermaid reference source).

## Known Deferred Items

- Databricks SQL warehouse sizing, the AI Search tier and partitions/replicas, APIM tier, and Foundry throughput (PTU vs. pay-as-you-go) are Step 12 cost-model inputs.
- IaC (Terraform) waits for platform selection.
- Choosing the CDC product vendor is procurement.
