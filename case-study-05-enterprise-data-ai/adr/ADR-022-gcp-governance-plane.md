# ADR-022: GCP-Track Governance — Dataplex Universal Catalog + BigQuery Policies + VPC Service Controls

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

[ADR-002](ADR-002-unified-governance-plane.md) asks for one plane. On GCP, BigQuery natively provides column-level access control (policy tags), row-level access policies, and dynamic masking. Dataplex Universal Catalog provides the business catalog and lineage. Sensitive Data Protection discovers sensitive data. VPC Service Controls enforce a data perimeter at the API layer.

## Decision

- **Data:** **BigQuery policy tags** (Restricted / Confidential / Internal) drive column access and masking. **Row-level access policies** cover line and state. **Sensitive Data Protection** discovery proposes tags, and people confirm them for core entities. **Dataplex Universal Catalog** is the catalog and lineage view.
- **Retrieval:** the **warm tier is inside BigQuery**, so its row policies apply to retrieval too ([ADR-023](ADR-023-gcp-retrieval.md)). The hot tier receives entitlements from an entitlement service derived from the same Entra groups.
- **AI assets (G4):** Vertex AI Model Registry and evaluation results, plus a use-case register in BigQuery that Apigee enforces at runtime.
- **Perimeter:** **VPC Service Controls** around the BigQuery, Vertex AI, and Cloud Storage projects.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Unity Catalog** (with Databricks). Not selected ([ADR-021](ADR-021-gcp-data-platform.md)).
2. **Relying on Vertex AI Search ACLs for retrieval governance.** Rejected. They are preview, and they can't be changed after data-store creation ([ADR-023](ADR-023-gcp-retrieval.md)).

## Consequences

- **Positive:** **VPC Service Controls** are the strongest API-layer exfiltration and residency boundary of the three tracks. Even valid credentials cannot move data out of the perimeter.
- **Positive:** Part of retrieval (the warm tier) is governed **by the same engine policies as SQL**.
- **Negative / accepted trade-off:** The hot tier and the AI inventory are aligned through identity rather than governed by the same catalog, which is similar to AWS.
