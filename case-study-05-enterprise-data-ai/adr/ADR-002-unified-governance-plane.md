# ADR-002: Unified Governance Plane for Data and AI Assets

**Status:** Approved
**Date:** Step 4 of the Case Study 5 pipeline

## Context

Harborline's warehouse grants access schema by schema, so most analysts can see PII they don't need (`current-state.md` §5). There is no catalog, no lineage, and no model inventory. The NAIC bulletin (driver 1) expects documented governance of AI systems, including their data. NFR-3 requires the assistant to honor the same permissions as the source systems. The written classification policy exists but is applied nowhere.

## Decision

A **single governance plane** is authoritative for data *and* AI assets:

- **Catalog:** tables, views, documents and document collections, retrieval indexes, models, prompts, and evaluation sets.
- **Classification-driven policy:** Restricted, Confidential, and Internal tags on columns and documents drive masking and row filtering **automatically**. A new column tagged Restricted is masked by default until an entitlement grants it.
- **Enforcement everywhere:** SQL engines, BI, notebooks, **and the retrieval service** ([ADR-003](ADR-003-permission-aware-retrieval.md)) enforce the same policies. Permissions are not re-implemented in each tool.
- **Lineage** from source through bronze, silver, and gold to reports **and to models and indexes**.
- **Model and use-case inventory:** each AI use case records its owner, purpose, data classes used, admitted models, evaluation results, and approval. This is the NAIC bulletin's documentation expectation, held in the same system as the data it governs.
- **Identity:** Entra ID (Harborline's existing identity provider) for all people, with workload identities for services.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Governance per tool** (warehouse grants, BI row-level security, assistant-side checks). Rejected. The same rule would be defined three or more times, and the copies drift. That is how the current PII over-exposure happened.
2. **A standalone third-party catalog layered over every platform.** Considered. It is attractive for multi-platform estates, but it adds a product whose enforcement depends on each engine's integration. It is deferred to the platform tracks: if a track's native governance cannot span SQL, BI, notebooks, and retrieval, a third-party catalog becomes that track's answer, and the track is scored accordingly.

## Consequences

- **Positive:** One answer to an examiner's question "who can see this, and which AI uses it", with evidence.
- **Positive:** Classification finally becomes operative, and the schema-wide PII exposure is closed as a side effect of the migration.
- **Negative / accepted trade-off:** Governance coverage across *retrieval* is where platforms differ most. Many catalogs govern tables well and indexes poorly. This is the highest-weighted criterion in Step 9 for exactly that reason.
- **Negative / accepted trade-off:** Classifying about 450 TB of data and about 40M documents is a program in its own right. Automated classification helps, but Restricted tagging needs human confirmation for the core insurance entities.
