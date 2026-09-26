# Step 10: Recommended Platform and Target Architecture

## Confirmed Platform

**Google Cloud, GCP-native stack**, per [ADR-027](../adr/ADR-027-cloud-platform-selection.md). It scored 3.90/5.00 (78.0%) against Azure (Databricks core) at 3.68 and AWS-native at 3.55 in [Step 9](decision-matrix.md). The selection is **conditional on gate G0**, which must pass **before the Teradata notice date of 31 December 2026**. If G0's Iceberg-parity and model-terms checks both fail, ADR-027 reverses to the Azure track.

This step:
- states the target architecture at a glance
- builds G0 into it
- traces each forcing function and the invariant to the mechanism that closes it
- carries forward what is still open

It does not re-argue the choice of platform.

## Target Architecture at a Glance

**Ingestion (US regions: us-east4, with us-central1 for DR; inside a VPC Service Controls perimeter)**
- **Datastream** captures Guidewire's Oracle changes within ≤ 15 minutes (NFR-7). Nightly Coastal files and vendor feeds land in Cloud Storage and load to BigQuery.
- The **document pipeline** takes the ECM change feed through **Document AI** (OCR and layout), then Harborline's structure-aware chunker (citation anchors and ACL attributes), then **Vertex AI embeddings** ([ADR-025](../adr/ADR-025-gcp-ingestion-and-teradata-migration.md), [ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md)).

**Lakehouse** ([ADR-021](../adr/ADR-021-gcp-data-platform.md))
- Bronze, silver, and gold are **BigQuery tables for Apache Iceberg**. Silver holds the unified party, policy, and claim model, with append-only reserve and payment facts.
- Native BigQuery storage is used only for derived gold performance marts.
- **Dataform** runs the tested SQL transformations that replace Informatica.
- **BigQuery Studio / Colab Enterprise** replaces SAS over time.
- Tableau connects through BI Engine.

**Governance** ([ADR-022](../adr/ADR-022-gcp-governance-plane.md))
- **BigQuery policy tags** (Restricted / Confidential / Internal), **row-level access policies**, and masking are cataloged in **Dataplex Universal Catalog**, with lineage. **Sensitive Data Protection** proposes the tags.
- The **AI inventory** is the Vertex AI Model Registry plus a use-case register.
- **VPC Service Controls** surround everything.
- Identity is **Workforce Identity Federation with Entra ID**.

**AI layer** ([ADR-023](../adr/ADR-023-gcp-retrieval.md), [ADR-024](../adr/ADR-024-gcp-models-and-ai-gateway.md))
- **Retrieval:** the claims assistant (Cloud Run) calls the retrieval service.
  - **Hot and reference tiers:** Vertex AI Vector Search (hybrid), with entitlement **restricts**.
  - **Warm tier:** BigQuery `SEARCH` under row-level security.
  - The **final authorization check** runs against ClaimCenter and ECM.
- **Models:** reached only through **Apigee** (LLM token budgets per use case, **Model Armor**, the G4 check). The admitted models are **Gemini** (with in-memory caching disabled) and **Claude via the US multi-region endpoint**.
- **Audit:** every interaction goes to **Cloud Storage with Bucket Lock** (7 years plus object holds).
- **Evaluation:** Vertex AI Gen AI evaluation plus Harborline's harness gate every change ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md)).

**FinOps** ([ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md), [ADR-026](../adr/ADR-026-gcp-network-identity-finops.md))
- The billing export lands in BigQuery.
- **BigQuery reservations are assigned per workload project** (ELT, BI, actuarial, data science, migration dual-run).
- Apigee reports token analytics per use case.
- Unit-cost dashboards track cost per query, per claim, and against the $6.8M baseline.

See [`diagrams/gcp-implementation-architecture.md`](../diagrams/gcp-implementation-architecture.md) for the reference diagram that the hand-drawn target diagram will be drawn from.

## Gate G0, Designed In

| G0 check (ADR-027) | Where it lives in the architecture | If it fails |
|---|---|---|
| 1. **Iceberg parity:** Datastream CDC merges ≤ 15 min on Iceberg-managed tables; the reserving (gold triangle) workload meets its targets; a second engine reads the tables | Proof of concept on the claims domain in a sandbox project before any production commitment | Silver moves to native BigQuery storage, with scheduled Iceberg exports of gold. Portability is re-scored |
| 2. **Model terms:** Gemini's abuse-monitoring exception is granted, and legal confirms Claude's partner terms on Vertex AI | A contract workstream running in parallel. **Apigee refuses** any model whose terms are not confirmed in G4 | If one model fails, run on the other. **If both 1 and 2 fail, reverse to the Azure track** |
| 3. **Translation proof of concept:** at least 200 BTEQ scripts and 150 procedures or macros through the BigQuery translator | The results size the manual rewrite and feed the Teradata **bridge-extension decision** ([Step 11](migration-roadmap.md)) | Revise the timeline. Translation quality alone does not reverse the platform choice |

## Tracing Each Forcing Function to the Mechanism That Closes It

1. **Shadow AI with customer data (driver 1, then 2).**
   - **Mechanism:** a sanctioned assistant **inside a VPC Service Controls perimeter**, reachable only through Apigee to admitted US models under confirmed no-training and no-retention terms. Every interaction is logged immutably.
   - **Result:** adjusters get the capability they were using personal phones for. It is faster, because it's grounded in *their* claim file with citations, and it is governed. Blocking public tools only lasts once there's a better sanctioned option.
2. **NAIC AI bulletin and state AI rules (driver 1).**
   - **Mechanism:** the **use-case register and Model Registry** (the inventory), the **evaluation harness** with its release gates, risk tiering and red-team testing ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md)), **human-in-the-loop by design** (NFR-5), and the **7-year immutable audit trail**.
   - **Result:** when a regulator asks "show us how this AI system is governed", the answer is a record, not a policy memo.
3. **The Teradata contract dates (driver 3).**
   - **Mechanism:** a first-party GA translator for **SQL, BTEQ, and TPT**; Datastream CDC; domain-by-domain dual-run with automated reconciliation ([ADR-005](../adr/ADR-005-teradata-migration-approach.md)); and G0's translation proof of concept, so the notice decision is made on evidence.
   - **Result:** Harborline exits on its own timeline, at worst with the one-year bridge, and never another multi-year renewal.
4. **Three post-acquisition estates and an 18-day reserving close (driver 4).**
   - **Mechanism:** the unified silver model (survivorship golden records, crosswalks that keep every source key, append-only reserve and payment facts). Gold loss triangles are produced continuously, with as-of snapshots for the close.
   - **Result:** NFR-8's close of ≤ 8 days becomes achievable, because reconciliation moves from quarter end to every day.
5. **The invariant (no autonomous adverse decisions; no training on Harborline data).**
   - **Mechanism:**
     - The assistant is advisory only, and drafts need a human to send them.
     - G4 risk tiering blocks any Tier 1 use case without bias testing and compliance approval.
     - Apigee admits only models with confirmed no-training terms.
     - Stateful model APIs and caching are disabled.
     - VPC Service Controls prevent data leaving the perimeter.

## NFR Coverage Summary

| NFR | Met by |
|---|---|
| NFR-1 Latency (p95 ≤ 6 s) | Vector Search (hot) + reranking + Vertex models; the latency budget from Step 5 |
| NFR-2 Groundedness (≥ 95%) | Citations with anchors; the evaluation harness gates every change |
| NFR-3 Retrieval authorization | Restricts (hot), BigQuery row-level security (warm), the final authorization check, and a red-team gate with zero leaks |
| NFR-4 Model data use | Apigee admission via G4; Gemini caching off plus the abuse-monitoring exception; Claude US multi-region with confirmed terms; US-only via org policy |
| NFR-5 Human-in-the-loop | Advisory-only assistant; G4 risk tiers |
| NFR-6 AI audit, 7 years | Bucket Lock plus object holds, with a BigQuery copy |
| NFR-7 CDC ≤ 15 min | Datastream |
| NFR-8 Reserving close ≤ 8 days | Unified silver model plus continuously produced triangles |
| NFR-9 Availability / RPO / RTO | Regional managed services, BigQuery time travel, DR region (us-central1) |
| NFR-10 Scale | Serverless BigQuery; Vector Search sized to the hot tier (ADR-006) |
| NFR-11 FinOps | Billing export to BigQuery, reservations per workload, Apigee token budgets, unit-cost dashboards. Tested in [Step 12](cost-and-risk-analysis.md) |
| NFR-12 Openness | Iceberg-managed system of record, subject to G0 check 1 |

## What This Step Carries Forward, Not Resolves

- **[Step 11](migration-roadmap.md):**
  - timing against the Teradata notice (31 December 2026) and term end (30 June 2027), and whether to sign the one-year bridge
  - the domain migration order
  - **decoupling the claims assistant from the Teradata exit** (the assistant needs ECM indexing, ClaimCenter CDC, and governance, not the warehouse)
  - the SAS retirement sequence
  - retiring the 2024 Snowflake account
  - Coastal ingestion
  - standing up the golden set and the FinOps role
- **[Step 12](cost-and-risk-analysis.md):**
  - run-rate against the $6.8M baseline (excluding AI)
  - assistant cost per query against the $0.05 ceiling
  - dual-run and bridge costs
  - the consolidated risk register
