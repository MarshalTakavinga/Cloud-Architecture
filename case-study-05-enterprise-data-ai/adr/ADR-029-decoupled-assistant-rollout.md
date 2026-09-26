# ADR-029: Decoupled Claims Assistant Rollout — Pilot at M6, Scale by M14

**Status:** Approved
**Date:** Step 11 of the Case Study 5 pipeline

## Context

Driver 2 (the claims assistant) carries most of the operating value, and driver 1 (governed AI) is its precondition. Staff are working around the March 2026 ban on personal devices *today*. The assistant's dependencies are:
- ECM indexing ([ADR-006](ADR-006-retrieval-scope-and-chunking.md))
- ClaimCenter CDC for claim context and ACLs
- the governance plane
- the AI gateway
- the evaluation harness

**None of these depends on the Teradata exit.** The warehouse feeds analytics, not the assistant.

## Decision

The assistant is rolled out **on its own track, independent of the warehouse migration**:

- **Foundation (M3–M6):**
  - Datastream CDC from ClaimCenter.
  - Hot tier for the pilot scope.
  - Golden set of about 1,500 questions, built with Claims SMEs.
  - Red-team suite and evaluation harness.
- **Pilot (M6–M8):** about **300 adjusters** in **personal auto** across the three **Prairie Shield states**. These are Guidewire-native, and they keep NY DFS and Colorado-specific requirements out of the pilot scope.
- **Scale (M9–M14):** all lines and states, about 3,800 claims staff and about 600 underwriters. Coastal documents are indexed from M12. NY and CO use cases are reviewed against state requirements before they are enabled.
- **Gates:**
  - **A1 (go-live):** faithfulness ≥ 95%, zero red-team leaks, p95 ≤ 6 s, audit verified, models admitted only with confirmed terms, use case approved in G4.
  - **A2 (scale):** ≥ 60% weekly active, measured search-time reduction, zero leakage incidents, cost per query ≤ $0.05.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Launch the assistant after the warehouse migration.** It would delay the most visible value by more than 18 months, while shadow AI continues on personal phones. Rejected.
2. **Launch to all 4,400 users at once.** Rejected. A leak or quality problem would hit every state and line at the same moment, and there would be no measured baseline to prove value from.
3. **Pilot in New York first** (the most scrutinized state). Rejected for the *pilot*, because the first deployment should prove the platform before it meets the strictest state-specific review.

## Consequences

- **Positive:** The business sees governed AI value by **M6–M8**, and the sanctioned tool starts replacing shadow AI early, which is the real fix for forcing function 1.
- **Positive:** The pilot produces the unit-cost and adoption evidence that Step 12's value case needs.
- **Negative / accepted trade-off:** Two parallel programs (the assistant and the warehouse exit) compete for the same platform and governance team. Phase 0 staffing and the G4 approval board are shared, and are a capacity risk.
