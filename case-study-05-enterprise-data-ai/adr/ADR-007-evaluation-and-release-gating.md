# ADR-007: Evaluation and Release Gating for AI Changes

**Status:** Approved
**Date:** Step 5 of the Case Study 5 pipeline

## Context

NFR-2 requires ≥ 95% faithfulness on a curated evaluation set, re-run on every change. NFR-3 requires zero cross-permission leakage in red-team testing. The NAIC bulletin expects AI systems to be tested, documented, and monitored, and examiners may ask for that evidence. Model versions, prompts, chunking, and embedding models will all change repeatedly over the platform's life ([ADR-004](ADR-004-ai-gateway-and-model-access.md) keeps them swappable). Each change can silently degrade quality or open a leak.

## Decision

**1. A golden set, owned by Claims.** About **1,500 questions** across the lines, the top states, and the main question types (coverage, file facts, next steps, guideline lookup, summarization, drafting). Each has the expected answer points and the **source documents that should be cited**. The set is curated and refreshed quarterly by claims subject-matter experts, and it is versioned in G4.

**2. Metrics on every candidate change:**

| Metric | Gate |
|---|---|
| Faithfulness (answer supported by retrieved sources) | ≥ 95% |
| Citation precision and recall against expected sources | No regression > 2 points |
| Correct refusal ("I can't find that in this claim file") | ≥ 90% on the unanswerable subset |
| **Red-team leakage probes** (cross-state, unassigned claims, Restricted medical content, prompt injection embedded in documents) | **0 leaks** (hard gate) |
| p95 latency | ≤ 6 s (NFR-1) |
| Cost per query | ≤ the ADR-008 budget |

**3. Scoring:** automated scoring (model-graded, with a *different* model from the one under test) plus **human SME review of a 5% sample** of every run. Model-graded scores are calibrated against the human sample every quarter.

**4. Release path:** change proposed → full harness run → results written to G4 → **canary** at 5% of users with online metrics (thumbs, edit rate on drafts, citation click-through, escalations) → full rollout. Anything that is not approved in G4 cannot receive traffic, because A4 checks this.

**5. Production monitoring:** weekly sampled review, drift alerts on online metrics, and any leakage signal from the final authorization check ([ADR-003](ADR-003-permission-aware-retrieval.md)) treated as a security incident.

**6. Risk tiering in G4:**
- Q&A and summarization: **Tier 2** (advisory).
- Correspondence drafts: **Tier 2 with mandatory human send**.
- Any future use case that would *inform* a coverage, reserve, or rating decision: **Tier 1**, which requires unfair-discrimination testing and compliance approval before release. No such use case is in scope.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Vendor benchmark scores as the release criterion.** Rejected, because they say nothing about Harborline's documents, states, or permission model.
2. **Human review only.** It is too slow for frequent model and prompt changes and too small a sample for leakage testing. Human review calibrates the automated scoring instead.
3. **Evaluate once at launch.** Rejected. Models, prompts, and data all change, and a one-time evaluation certifies a system that no longer exists.

## Consequences

- **Positive:** Every AI change leaves an evidence record: what changed, how it scored, who approved it. That is exactly what the NAIC bulletin and an examiner ask for.
- **Positive:** Model swaps become routine, which keeps Harborline able to follow price and quality improvements without re-architecting.
- **Negative / accepted trade-off:** The golden set is an ongoing cost of SME time, and it is only as good as its curation. Claims owns it as a product, not as a one-off project.
