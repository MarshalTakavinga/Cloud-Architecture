# ADR-003: Permission-Aware Retrieval for the Claims Assistant

**Status:** Approved
**Date:** Step 4 of the Case Study 5 pipeline

## Context

NFR-3 requires that a user can retrieve only documents they may open in ClaimCenter or ECM, with **zero** cross-permission leakage in red-team testing. Harborline's document permissions combine four attributes:
- line of business
- state
- claim assignment (the adjuster's unit, and whether the user is assigned to the claim)
- an entitlement for Restricted content (for example, bodily-injury medical records)

Claims are reassigned daily. The index will hold about 40M documents, growing by about 25K a day. The most common RAG security failure is an index built by a service account with permissions applied *after* retrieval, or not at all.

## Decision

1. **ACL metadata on every chunk.** Each chunk inherits its document's line, state, claim ID, assigned unit or adjuster set, and Restricted flag. An **ACL sync** from ClaimCenter and ECM updates this metadata within **15 minutes** of a reassignment or permission change (the same budget as NFR-7).
2. **Pre-filtered search.** At query time, the retrieval service gets the user's entitlements from the governance plane ([ADR-002](ADR-002-unified-governance-plane.md)) and turns them into a **filter applied inside** the vector and lexical (hybrid) search. Chunks the user may not see are never candidates, so they cannot starve or leak into the top-k results.
3. **Final authorization check.** Before a response is shown, every cited source is re-checked against the source system's live permission. A failure removes the citation *and* the content drawn from it, and the event is logged as a security signal.
4. **Restricted content by entitlement only.** Chunks from Restricted documents are retrievable only by users with that entitlement. For everyone else they do not exist, and not even their existence is revealed.
5. **Red-team suite.** A standing set of cross-permission probes (other states, unassigned claims, Restricted medical content) runs with the evaluation harness on every index, prompt, or model change. It must return zero leaks.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Post-filtering results.** A filter bug is a leak, and heavy filtering silently degrades answers when the top-k are all removed.
2. **Separate indexes per permission group.** The combinations explode (line × state × assignment × entitlement), and daily reassignments would mean moving documents between indexes.
3. **Rely on the model to "not mention" restricted content.** Rejected outright. Prompt instructions are not an access control.

## Consequences

- **Positive:** Authorization is enforced at the two places that matter: before retrieval, which prevents leaks, and before display, which catches sync lag. It is defined once, in the governance plane.
- **Negative / accepted trade-off:** The vector store must support **efficient filtered search** at about 40M documents with high-cardinality filters (claim IDs). Not every vector index does this well, so it is a named evaluation item for Steps 6–8.
- **Negative / accepted trade-off:** ACL sync is a new, security-critical pipeline. Its lag is monitored as a first-class metric, and the final authorization check is its safety net.
