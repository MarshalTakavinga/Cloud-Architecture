# ADR-017: AWS-Track Retrieval — OpenSearch Service with Native Document-Level Security

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

[ADR-003](ADR-003-permission-aware-retrieval.md) requires pre-filtered hybrid retrieval with zero leaks, and [ADR-006](ADR-006-retrieval-scope-and-chunking.md) requires hot, reference, and warm tiers. The AWS options are:

- **OpenSearch Service (managed domains).** Hybrid lexical + k-NN search, plus fine-grained access control with **document-level security** ("users … can see only the documents that match the query"), **field-level security**, and field masking. Roles are mapped from users, IAM roles, or backend roles such as SAML groups.
- **Bedrock Knowledge Bases.** Access control is **application-supplied metadata filtering**, with no native document ACLs.
- **S3 Vectors** (GA 2 December 2025). Up to 2 billion vectors per index, but vector-only, with no documented keyword or hybrid search.

## Decision

**Amazon OpenSearch Service** (VPC domain, fine-grained access control on) hosts three sets of indices: **hot** (hybrid), **reference** (hybrid, versioned), and **warm** (lexical only). Blue/green index versions sit behind aliases.

Enforcement is **layered**:
1. **In the index:** DLS roles restrict documents by **line, state, and Restricted entitlement**. Roles are mapped from the user's SAML groups (the same Entra groups used by Lake Formation). **Field masking** hides Restricted fields for roles without the entitlement.
2. **In the application:** a filter on **claim assignment** (claim ID or assigned unit) is added by the retrieval service, because assignments change daily and are too fine-grained for static roles.
3. **Final authorization check** on every citation, as ADR-003 requires.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Bedrock Knowledge Bases with S3 Vectors.** It is the lowest-operations option, and its scale easily covers the hot tier. Rejected because it is vector-only (the warm tier and exact-term queries such as policy numbers need lexical search) and relies purely on application filtering.
2. **OpenSearch Serverless.** It has simpler operations, but its data-access policies work at collection and index level rather than per document. The index-side DLS that makes this track distinctive would be lost.

## Consequences

- **Positive:** **The index itself enforces the coarse permission dimensions.** Even a bug in the retrieval service cannot return another state's or line's documents, or unentitled Restricted content. This is stronger than the Azure track's application-only filtering ([ADR-011](ADR-011-azure-retrieval.md)).
- **Negative / accepted trade-off:** Managed OpenSearch domains need capacity planning, and they carry the operational load of a search cluster at about 40M documents. DLS queries add query cost, which must be load-tested in the pilot.
