# ADR-027: Cloud Platform Selection — Google Cloud (GCP-native), Gated by G0

**Status:** Approved, subject to gate G0
**Date:** Step 9 of the Case Study 5 pipeline

## Context

Steps 6–8 produced three stacks, each already the best within its cloud after comparing native services against Databricks and Snowflake:

- **Azure:** Databricks core, [ADR-009](ADR-009-azure-data-platform.md) to [ADR-014](ADR-014-azure-network-identity-finops.md)
- **AWS:** native, [ADR-015](ADR-015-aws-data-platform.md) to [ADR-020](ADR-020-aws-network-identity-finops.md)
- **GCP:** native, [ADR-021](ADR-021-gcp-data-platform.md) to [ADR-026](ADR-026-gcp-network-identity-finops.md)

[`docs/decision-matrix.md`](../docs/decision-matrix.md) scores them against `requirements.md`'s weighting.

## Decision

Harborline's data and AI platform is built on **Google Cloud, using the GCP-native stack**:

| Area | Services |
|---|---|
| Data | BigQuery with Iceberg-managed tables, Dataform, BigQuery Studio |
| Governance | Dataplex, BigQuery policy tags and row policies, Sensitive Data Protection, VPC Service Controls |
| Ingestion and migration | Datastream, BigQuery Migration Service (SQL, BTEQ, TPT) |
| Retrieval | Vertex AI Vector Search (hot) + BigQuery search under row-level security (warm) |
| Models and gateway | Vertex AI (Gemini, and Claude on the US multi-region endpoint) behind Apigee with Model Armor |
| Regions | us-east4 (primary), us-central1 (DR) |

The weighted score is **3.90/5.00 (78.0%)**, against Azure's 3.68 and AWS's 3.55.

## Scoring Rationale, Criterion by Criterion

1. **Governance and security (25%): AWS 4, GCP 4, Azure 3.5.**
   - **AWS:** OpenSearch document-level security is enforced in the index ([ADR-017](ADR-017-aws-retrieval.md)), but there are three planes aligned by identity ([ADR-016](ADR-016-aws-governance-plane.md)).
   - **GCP:** engine-enforced policies for data and the warm tier, plus VPC Service Controls ([ADR-022](ADR-022-gcp-governance-plane.md)). The hot tier uses application restricts ([ADR-023](ADR-023-gcp-retrieval.md)).
   - **Azure:** the best single catalog (Unity Catalog, [ADR-010](ADR-010-azure-governance-plane.md)), but AI Search filtering is application-only ([ADR-011](ADR-011-azure-retrieval.md)).
2. **AI and RAG (20%): Azure 4.5, GCP 4, AWS 3.5.**
   - **Azure:** two frontier families in Data Zone US behind a bought gateway ([ADR-012](ADR-012-azure-models-and-ai-gateway.md)).
   - **GCP:** Gemini + Claude US multi-region (GA) behind Apigee with Model Armor ([ADR-024](ADR-024-gcp-models-and-ai-gateway.md)).
   - **AWS:** the review-retention tier is excluded and the gateway is custom ([ADR-018](ADR-018-aws-models-and-ai-gateway.md)).
3. **Data platform and Teradata (15%): GCP 4.5, AWS 4, Azure 3.5.**
   - **GCP:** a first-party GA translator for SQL, BTEQ, and TPT, plus Datastream ([ADR-025](ADR-025-gcp-ingestion-and-teradata-migration.md)).
   - **AWS:** SCT (including BTEQ → RSQL) plus DMS ([ADR-019](ADR-019-aws-ingestion-and-teradata-migration.md)).
   - **Azure:** Lakebridge plus a third-party CDC product ([ADR-013](ADR-013-azure-ingestion-and-teradata-migration.md)).
4. **Cost and FinOps (15%, directional): AWS 3.5, GCP 3.5, Azure 3.** See the decision-matrix notes.
5. **Operations and skills (15%): GCP 4, Azure 3.5, AWS 2.5.** Serverless, versus two vendors, versus many engines plus a custom gateway.
6. **Portability (10%): Azure 4, AWS 3.5, GCP 3.** Portable Databricks logic, versus native Iceberg with Redshift-shaped logic, versus Iceberg-managed tables with a parity risk and GoogleSQL logic.

## Gate G0 — Must Pass Before the Teradata Notice Decision (by mid-December 2026)

The sensitivity analysis shows GCP's lead survives either of its two known risks alone, but **not both together**. Both are testable now, so both are gated:

1. **Iceberg-parity proof of concept.** On BigQuery tables for Apache Iceberg, demonstrate:
   - CDC merges from Datastream at ≤ 15 minutes
   - the reserving-close workload (gold triangles) within performance targets
   - a successful **read by a second engine**, as ADR-001 requires

   On failure: silver moves to native BigQuery storage, with Iceberg exports for gold, and portability is re-scored.
2. **Model-terms confirmation.** Google grants the **abuse-monitoring exception** for Gemini, and Harborline legal confirms **Claude partner-model terms** on Vertex AI against NFR-4.
3. **Translation proof of concept.** Run the BigQuery translator on a representative sample (at least 200 BTEQ scripts and 150 procedures or macros) to confirm or revise the 25–35% manual-rewrite assumption. This sizes the bridge-extension decision in Step 11.

**If gates 1 and 2 both fail, this ADR is reversed in favor of the Azure track** ([ADR-009](ADR-009-azure-data-platform.md) to [ADR-014](ADR-014-azure-network-identity-finops.md)), as the sensitivity table specifies. If only one fails, GCP remains the choice, at a lower margin.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure (Databricks core), 3.68.** The strongest single catalog, model choice, and logic portability. It is the designated fallback if G0 fails on both counts.
2. **AWS (native), 3.55.** Index-side document security and the most open data layer, held back by operational load (many engines plus a custom gateway) and the excluded model tier.
3. **Databricks on GCP, 3.70 (variant).** A single catalog over GCP's models and network, at the cost of first-party BTEQ/TPT translation and serverless operations. It is the fallback if a multi-cloud requirement emerges.

## Consequences

- **Positive:** The platform with the strongest first-party answer to the **Teradata exit** is selected, and the exit's deadline is the most time-critical constraint in the case study.
- **Positive:** A serverless operating model fits a ~35-person team that must also absorb SAS retirement and AI governance.
- **Negative / accepted trade-off:** Hot-tier retrieval security is application-supplied. The red-team gate (ADR-007) and the final authorization check are the controls, and Vertex AI Search's native ACLs are re-evaluated when they reach GA.
- **Negative / accepted trade-off:** Translated logic becomes GoogleSQL. The data stays open, but a future exit would mean re-translating the logic.
- **Portfolio note:** Case Study 4 also selected GCP, for different reasons (edge autonomy and industrial protocols). Both results follow from each case study's own weights, and each ADR records exactly what would have to be true for the result to flip.
