# ADR-023: GCP-Track Retrieval — Vertex AI Vector Search (hot/reference) + BigQuery Search (warm)

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

[ADR-003](ADR-003-permission-aware-retrieval.md) and [ADR-006](ADR-006-retrieval-scope-and-chunking.md) define the retrieval requirements. The GCP options are:

- **Vertex AI Search**, with document ACLs through `acl_info` readers and Entra via Workforce Identity Federation. **Preview**, a maximum of **3,000 readers per document**, and ACLs **cannot be toggled after data-store creation**.
- **Vertex AI Vector Search**, with hybrid dense + sparse search and **restricts** (namespace filters) applied at query time.
- **BigQuery search indexes and vector search**, which run inside BigQuery under its **row-level security**.

## Decision

- **Hot and reference tiers:** **Vertex AI Vector Search**, hybrid dense + sparse. Every datapoint carries **restricts** for line, state, claim/unit, and Restricted. The retrieval service builds the restricts from the user's entitlements and runs the final authorization check. Blue/green indexes sit behind the endpoint deployment.
- **Warm tier (lexical):** a **BigQuery table with a search index**. Warm-tier queries run with `SEARCH` **as the user's identity** (or a policy-scoped service identity), so **BigQuery's row-level access policies enforce** line, state, and Restricted entitlements in the engine.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Vertex AI Search with native ACLs.** It is the closest to "the index enforces identity". Rejected for now because it is **preview**, its ACL setting is permanent from data-store creation, and its **principal-list model** (readers per document) fits daily claim reassignment worse than attribute filters. It is **re-evaluated at GA**.
2. **BigQuery vector search for the hot tier as well.** This would give full engine-side governance. Rejected for the hot tier because interactive latency within ADR-003's ~1-second retrieval budget is not assured. It remains the fallback if Vector Search's filtering or cost disappoints.

## Consequences

- **Positive:** The warm tier gets **engine-enforced** permissions at low cost, and the hot tier gets low-latency hybrid search.
- **Negative / accepted trade-off:** Hot-tier security is **application-supplied restricts**, the same class of control as Azure AI Search's security filters. The red-team gate and final authorization check are the backstop.
- **Negative / accepted trade-off:** There are two retrieval engines to operate and evaluate.
