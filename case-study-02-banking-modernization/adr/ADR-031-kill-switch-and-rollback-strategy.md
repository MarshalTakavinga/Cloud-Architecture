# ADR-031: Kill-Switch and Rollback Strategy for the Real-Time Payments Capability

**Status:** Approved
**Date:** Step 12 of the Case Study 2 pipeline

## Context

Case Study 1's equivalent rollback ADR designed a weighted-traffic-shift revert, because that case study was migrating **existing live production traffic** between platforms. This case study's real-time payments capability has no existing production traffic to fall back to — it is a **net-new capability being turned on**, not a system being cut over from one place to another. Rollback here means a different question: what happens if the new capability needs to be disabled, at any point during or after [ADR-030](ADR-030-rollout-sequencing.md)'s rollout, without disrupting anything the mainframe already does.

## Decision

Rollback is a **feature-flag kill-switch at the ISO 20022/FedNow Gateway and Hold/Release Adapter layer**. Disabling the flag stops new real-time payment requests from entering the new architecture at all — the gateway declines new real-time submissions rather than routing them into the Hold/Release Adapter — while every payment already inside the flow at the moment of disablement is allowed to complete its existing state transition (a payment already holding at CICS is released or confirmed normally; nothing is left in an ambiguous state). The mainframe's nightly batch settlement is never touched by this switch in either direction, because [ADR-001](ADR-001-mainframe-integration-approach.md) never lets any component other than the single synchronous hold call touch the mainframe directly.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A weighted-traffic-shift rollback**, mirroring Case Study 1's strangler-fig revert mechanism. Rejected — that mechanism exists specifically to revert traffic that was already flowing through an old, live path back to it. There is no "old path" for real-time payments to revert to; before this initiative, no real-time posting capability existed at all. Applying that pattern here would be solving a problem this case study doesn't have.
2. **A database-level rollback** (reverting Ledger-of-Intent Service schema or data changes) as the rollback mechanism. Rejected — the risk this capability poses if something goes wrong is *new payment requests behaving incorrectly*, not *stored data becoming wrong*; [ADR-003](ADR-003-provisional-vs-confirmed-state-model.md)'s reconciliation process already exists specifically to catch and flag any state mismatch that occurs while the capability is live. A kill-switch that stops new requests, combined with the reconciliation process that's already designed to catch anomalies in what already happened, is the right pairing — a data rollback is neither necessary nor sufficient on its own.
3. **No formal kill-switch at all — rely on standard deployment rollback (redeploying a previous container image) if something goes wrong.** Rejected — a container redeploy takes minutes and doesn't stop in-flight traffic instantly; a feature flag evaluated on every request gives an immediate, request-level stop with no deployment step required, which matters specifically because the failure modes this capability is most exposed to (a fraud-scoring defect, a reconciliation mismatch pattern) are best contained by stopping new volume immediately, not by waiting for a redeploy.

## Consequences

- **Positive:** The kill-switch can be exercised at any point in [ADR-030](ADR-030-rollout-sequencing.md)'s rollout — during the Phase 4 limited pilot or after full Phase 5 rollout — with the same low-risk mechanism and the same guarantee that the mainframe's batch settlement is unaffected either way.
- **Positive:** Because the mainframe is never modified by this initiative in any phase, there is no "un-migrating" required if the new capability is disabled — the current-state batch-only posting path (which never went away) is simply what customers experience again, exactly as it did before this initiative began.
- **Negative / accepted trade-off:** Disabling the flag mid-rollout means customers lose the real-time experience they may have already started relying on, reverting to next-batch-cycle posting — a genuine customer-experience regression, accepted here as the necessary cost of having a real, immediate stop mechanism rather than a false sense of safety from a slower one.
- **Carried to Step 13:** The operational runbook and decision authority for exercising the kill-switch (who can flip it, under what conditions) is an operational-readiness item for the Phase 4 pilot, not an architecture decision resolved here.
