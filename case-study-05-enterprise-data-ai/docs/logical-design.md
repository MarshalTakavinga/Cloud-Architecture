# Step 5: Vendor-Neutral Logical Design

## Purpose of This Step

[Step 4](architecture-options-and-styles.md) fixed the shape of the solution:
- a lakehouse on open tables ([ADR-001](../adr/ADR-001-lakehouse-on-open-tables.md))
- one governance plane ([ADR-002](../adr/ADR-002-unified-governance-plane.md))
- permission-aware retrieval ([ADR-003](../adr/ADR-003-permission-aware-retrieval.md))
- an AI gateway ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md))
- the Teradata migration approach ([ADR-005](../adr/ADR-005-teradata-migration-approach.md))

This step defines the logical components, the conformed data model, the end-to-end flows, and three designs Step 4 deferred:
- what gets indexed and how ([ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md))
- how AI changes are evaluated and released ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md))
- how cost is metered and attributed ([ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md))

No platform, product, or model is named. Steps 6–8 do that for Azure, AWS, and GCP, each weighing its native stack against Databricks and Snowflake.

## Logical Component Model

| # | Component | Responsibility | Interface / contract |
|---|---|---|---|
| **Ingestion** | | | |
| I1 | CDC Connector | Reads Guidewire's Oracle redo logs and lands row changes in bronze within 15 min (NFR-7) | Append-only change records with source commit time and operation type |
| I2 | Batch Ingest | Coastal nightly files, vendor feeds, reference data | Files are schema-validated on landing. Rejected rows are quarantined, never dropped |
| I3 | Document Pipeline | Extracts text from ECM documents (OCR for scanned PDFs), chunks, embeds, and writes to the index ([ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md)) | Consumes an ECM change feed. Emits chunks carrying citation anchors and ACL attributes |
| I4 | ACL Sync | Keeps chunk-level ACL attributes in step with ClaimCenter assignments and ECM permissions (≤ 15 min, [ADR-003](../adr/ADR-003-permission-aware-retrieval.md)) | Updates index metadata only. It never re-embeds |
| **Lakehouse** | | | |
| D1 | Bronze | Raw, immutable landing of every source | Open tables, partitioned by source and load date |
| D2 | Silver | Cleaned and conformed data, including the **unified insurance model** (below) | Open tables. The system of record for analytics |
| D3 | Gold | Marts for reserving (loss triangles), regulatory schedules, BI, and model features | Open tables and views |
| D4 | Transformation Orchestrator | Version-controlled SQL/ELT that takes data from bronze to gold (replacing Informatica), with tests on every model | A DAG of transformations. Data-quality tests block publication to gold |
| D5 | Migration Reconciler | Dual-run comparison of Teradata and the lakehouse per domain ([ADR-005](../adr/ADR-005-teradata-migration-approach.md)): row counts, control totals, key report outputs | Produces a reconciliation report per domain. Sign-off is recorded in G4 |
| **Governance** | | | |
| G1 | Catalog and Policy Engine | Registers every data and AI asset. Evaluates policies (grants, masking, row filters) for every engine and for retrieval | A policy decision API that returns an entitlement set for a user and asset |
| G2 | Classification Service | Scans columns and documents, proposes Restricted/Confidential/Internal tags, and routes core-entity tags for human confirmation | Tags written to G1. New Restricted columns are masked by default |
| G3 | Lineage | Traces source → bronze → silver → gold → report, and source → index → model use case | Captured automatically from D4 and I3. Queryable |
| G4 | AI Inventory | The NAIC bulletin inventory: each use case's owner, purpose, risk tier, data classes, admitted models, prompt and index versions, evaluation results, and approvals | Release records written by A7. Read by A4 at runtime |
| **AI layer** | | | |
| A1 | Claims Assistant | UI embedded in the adjuster and underwriter workflow (launched from ClaimCenter). Q&A with citations, claim-file summaries, correspondence drafts for human send | Authenticated with Entra ID. Every output is advisory (NFR-5) |
| A2 | Retrieval Service | Builds an entitlement filter from G1, runs **pre-filtered hybrid search** (lexical + vector + rerank) in A3, assembles context, and runs the **final authorization check** on citations | Query, user, and claim context in. Ranked, authorized chunks with citation anchors out |
| A3 | Retrieval Index | Chunks, embeddings, lexical index, and ACL and classification attributes, in tiers ([ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md)) | Filtered search API |
| A4 | AI Gateway | Policy, redaction, routing and fallback, metering and budgets, and audit ([ADR-004](../adr/ADR-004-ai-gateway-and-model-access.md)) | A single model API for all applications. Rejects any model or prompt version not approved in G4 |
| A5 | Model Endpoints | Admitted models only: provider-hosted with no-training and ZDR terms in a US region, or in-tenancy open-weight | Reachable only from A4 |
| A6 | AI Audit Store | Immutable record of each interaction, retained 7 years, with legal hold (NFR-6) | Append-only. Queryable by compliance. Hold flags cannot be removed without dual approval |
| A7 | Evaluation Harness | Golden set, faithfulness scoring, red-team leakage probes, latency and cost checks. Gates every release ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md)) | Pass/fail release record written to G4 |
| **Consumption and FinOps** | | | |
| C1 | SQL and BI | Tableau and SQL access over gold, with policies enforced by G1 | Governed connections only. No extracts of Restricted data |
| C2 | Actuarial and data-science notebooks | The SAS replacement. Reserving and pricing work on gold and silver | Same entitlements as SQL |
| C3 | Regulatory and vendor exports | Statistical plans, annual-statement schedules, and ~40 vendor feeds as governed, logged exports | Each export is registered in G1 with its lineage |
| F1 | FinOps Metering | Collects cost and usage from A4 (tokens), A2/A3 (retrieval), the lakehouse (compute by workload), and storage. Allocates to use case and business unit ([ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md)) | Unit-cost dashboards, budgets, and anomaly alerts |

## The Unified Insurance Data Model (silver, driver 4)

| Subject area | Core entities | Conformance rule |
|---|---|---|
| **Party** | Party (insured, claimant, third party, provider, agent), Party Role, Contact | Golden record via survivorship (Guidewire first, then Coastal, then third-party). A **crosswalk** keeps every source key. No source key is ever discarded |
| **Policy** | Policy, Policy Term, Coverage, Risk (vehicle / location / exposure unit), Premium Transaction | One policy key namespace with a source prefix (`GW-`, `CO-`). Prairie Shield keys are already in Guidewire |
| **Claim** | Claim, Exposure, Reserve Transaction, Payment, Recovery, Claim Assignment | Reserve and payment transactions are **append-only facts**, so loss triangles can be rebuilt as of any date |
| **Document** | Document metadata (type, date, claim, classification, ACL attributes) | Metadata only. Content stays in ECM, and text lives in the index |
| **Gold marts** | Loss triangles (accident period × development period, paid and incurred, by line and state), regulatory schedules, BI marts | Built only from silver facts. Never re-derived from bronze |

The reserving close gets faster (NFR-8, 18 → 8 days) because the triangles are **produced continuously from conformed facts**, instead of being reconciled across three estates at quarter end.

## End-to-End Flows

### Flow A — Adjuster asks the assistant a question (the core flow)

1. From a claim in ClaimCenter, the adjuster opens the assistant (A1). The claim ID and the user's Entra ID identity come with the request.
2. The Retrieval Service (A2) asks G1 for the user's **entitlement set** (lines, states, assigned claims, Restricted entitlement).
3. A2 runs **pre-filtered hybrid search** in A3, restricted to the entitlement filter. It is biased toward the current claim and the relevant state guideline corpus. Results are reranked, and the top chunks are assembled with citation anchors.
4. A1 sends the prompt and the context to the **AI Gateway** (A4). The gateway checks that the use case, prompt version, and model are approved in G4, applies the data-class policy (redacting where required), routes to an admitted model (A5), and meters tokens.
5. The model responds. A2 runs the **final authorization check**: every cited document is re-verified against ClaimCenter/ECM. A failed citation is removed along with the content drawn from it, and the event is logged.
6. A1 shows the answer with **clickable citations** to the source documents. Drafted correspondence is shown for editing and human send only.
7. The gateway writes the complete record to the audit store (A6): user, claim, prompt, source IDs, model version, response, and the user's action (accepted, edited, discarded, thumbs up or down). Latency budget: retrieval ≤ 1.0 s, gateway overhead ≤ 0.2 s, model generation ≤ 4.5 s → p95 ≤ 6 s (NFR-1).

### Flow B — A new claim document becomes searchable

A document is added in ECM → the change feed → I3 extracts text (OCR if needed), chunks it by structure, and embeds it into the **hot tier** (open claims) → it is searchable within **15 minutes**, with the ACL attributes of its claim at that moment.

### Flow C — A claim is reassigned

ClaimCenter assignment change → I1 lands it → I4 updates the ACL attributes on that claim's chunks (metadata only, no re-embedding) within **15 minutes**. In the window before sync, the new adjuster may briefly not see the claim's documents, which fails safe. The old adjuster is blocked at the final authorization check (Flow A, step 5), which checks the live assignment.

### Flow D — A model, prompt, or index change is released

A proposed change (new model version, prompt edit, chunking change, embedding model) runs the full **evaluation harness** (A7):
- golden-set faithfulness ≥ 95%
- citation precision
- **zero** red-team leaks
- p95 latency
- cost per query ≤ budget

The result is written to G4. A4 accepts traffic for the new version only after it passes. The change then goes out as a canary (5% of users), with online metrics compared, before full rollout ([ADR-007](../adr/ADR-007-evaluation-and-release-gating.md)).

### Flow E — Quarterly reserving close

CDC keeps claim facts current → gold triangles refresh daily → actuaries run reserving models in notebooks (C2) on as-of-date snapshots (the time travel that open tables provide) → review and sign-off → regulatory schedules export (C3). The reconciliation that took most of the 18 days today is replaced by conformance rules applied continuously in silver.

### Flow F — Teradata domain dual-run

For each domain, translated logic runs on the lakehouse alongside Teradata → the Reconciler (D5) compares row counts, control totals, and the domain's critical reports daily → after N consecutive clean days plus business sign-off, the Teradata objects are frozen, and later dropped.

## Security and Identity (logical)

- **One identity provider (Entra ID)** for all users. Workload identities are used for services, with no shared service accounts reading documents on a user's behalf *without* passing that user's entitlements.
- **Policy is defined once in G1.** It is enforced by SQL and BI engines, notebooks, A2, and A4. Nothing enforces its own separate copy of the rules.
- **Restricted data** (PII, medical, financial account) is masked by default everywhere. It is unmasked only by entitlement, and it reaches models only for use cases whose G4 record allows it.
- **All data, embeddings, logs, and inference stay in US regions** (NFR-4).

## Diagram

See [`diagrams/logical-architecture.md`](../diagrams/logical-architecture.md) for the component model and the Flow A sequence (Mermaid reference sources).

## Key Decisions Made at This Step

- **[ADR-006](../adr/ADR-006-retrieval-scope-and-chunking.md):** what is indexed, in which tier, and how chunks carry citations and ACL attributes.
- **[ADR-007](../adr/ADR-007-evaluation-and-release-gating.md):** how every AI change is evaluated, gated, and canaried. This is the NAIC bulletin's "testing" expectation made operational.
- **[ADR-008](../adr/ADR-008-finops-allocation-and-unit-cost.md):** how cost is metered and attributed, and how the $0.05-per-query ceiling is budgeted.

## What Step 5 Deliberately Leaves Open

No engine, catalog product, vector store, model, or table format is named. Each platform track maps these 22 components to Azure, AWS, and GCP, **and** to Databricks and Snowflake on each cloud. The biggest expected differences are in:
- **G1** (does governance really reach retrieval?)
- **A3** (filtered vector search at this scale)
- **A5** (which models, under which terms, in which US regions)
