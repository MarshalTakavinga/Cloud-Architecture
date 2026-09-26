# ADR-006: Retrieval Scope, Index Tiers, and Chunking

**Status:** Approved
**Date:** Step 5 of the Case Study 5 pipeline

## Context

ECM holds about 95M documents. About 40M of them carry text, roughly **8 TB of text**. Embedding all of it at typical chunk sizes (~750 tokens, ~3 KB) would produce **billions of chunks**, and several terabytes of vectors even after quantization. The cost falls on storage, indexing, and filtered-search performance ([ADR-003](ADR-003-permission-aware-retrieval.md)), and it works directly against the $0.05-per-query ceiling (NFR-11).

Adjusters overwhelmingly ask about **their assigned, open claims** and about **coverage forms and state handling guidelines**. Questions about claims closed years ago are rare, and are usually made while reopening or litigating them.

## Decision

**1. The index is organized in tiers.**

| Tier | Content | Search | Approximate text |
|---|---|---|---|
| **Hot** | All documents on **open claims**, plus claims **closed within 24 months** | Hybrid (lexical + vector + rerank) | ~25% of text (~2 TB) |
| **Reference** | Coverage forms (by edition and state), state claim-handling guidelines, underwriting guidelines, internal procedures | Hybrid, versioned by edition and effective date | Small, curated |
| **Warm** | Older closed claims | **Lexical only** | Remainder |
| **On-demand** | A warm-tier claim is **reopened, assigned, or placed under litigation** | It is promoted to hot and embedded within **1 hour** | — |

**2. Chunks follow the document's structure, not fixed token windows.**
- Adjuster notes are chunked one entry per chunk, with author and timestamp.
- Estimates and reports are chunked by section.
- Medical records are chunked by encounter and section, and are **Restricted** ([ADR-003](ADR-003-permission-aware-retrieval.md)).
- The target size is 300–800 tokens, with small overlaps only where a section is split.

**3. Every chunk carries its identity:**
- document ID, claim ID, document type and date
- a **citation anchor** (page and section), so the assistant can deep-link to the exact spot
- ACL attributes and classification
- the embedding model version

**4. Photos and images are not embedded in this initiative.** Their metadata and any captions are indexed lexically. Image understanding is a future use case that must go through [ADR-007](ADR-007-evaluation-and-release-gating.md).

**5. Embedding-model changes use a blue/green index.** A new embedding model builds a parallel index version. It must pass ADR-007 before traffic switches, and the old version is kept until rollback is no longer needed. Embeddings are never mixed across model versions in one index.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Embed everything.** It maximizes recall on rare historical questions, but multiplies index cost and filtered-search load for queries that seldom happen. Lexical search and on-demand promotion cover them.
2. **Embed only the current claim at query time (no standing index).** It is cheap, but it would make cross-claim and guideline questions impossible, and it adds embedding latency to every query (NFR-1).
3. **Fixed token windows.** They are simpler, but they split adjuster notes and estimate sections mid-thought, which weakens citations and faithfulness.

## Consequences

- **Positive:** Index size and cost track the *working set* of claims rather than 12 years of history. That is the main structural lever on unit cost.
- **Positive:** Structure-aware chunks with anchors make citations precise, which NFR-2 and adjuster trust both depend on.
- **Negative / accepted trade-off:** A question about an old closed claim, asked before it is promoted, gets lexical-only recall. The assistant says so explicitly ("older claim — keyword search only") rather than giving a weaker answer silently.
- **Negative / accepted trade-off:** The pipeline has to maintain tier transitions (claim closure + 24 months → warm, reopen → hot), which adds logic to I3 and I4.
