# ADR-003: Provisional vs. Confirmed State Model and Reconciliation

**Status:** Approved
**Date:** Step 5 of the Case Study 2 pipeline

## Context

[ADR-001](ADR-001-mainframe-integration-approach.md) established that real-time payments are provisionally posted based on CDC-observed and event-driven processing, while final settlement still happens in the mainframe's unmodified nightly batch run. That ADR explicitly flagged, as a consequence, that "provisional" and "batch-confirmed" states must be modeled and surfaced honestly rather than assumed to always agree. This ADR resolves how.

## Decision

Every real-time payment moves through a three-state model owned by the **Ledger-of-Intent Service**: `Authorized/Held` → `Provisionally Posted` → `Confirmed`. A nightly **Reconciliation Process** compares `Provisionally Posted` entries against `BatchConfirmed` events (emitted by the CDC Connector once the mainframe's batch run actually books the transaction), matching them by the [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md) idempotency key. A clean match automatically promotes the entry to `Confirmed`. Any `Provisionally Posted` entry with no matching `BatchConfirmed` event by the next business day is raised as a manual-review exception — it is never silently dropped and never silently auto-confirmed.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Treat "provisional" as final, customer-visible truth, with no reconciliation step at all.** Rejected — a rare batch-settlement rejection (for reasons independent of the real-time hold, e.g. a downstream compliance hold applied during batch processing) would then have no correction mechanism, directly risking both NFR-5 (posting correctness) and BSA/AML recordkeeping integrity.
2. **Don't expose anything to the customer until the mainframe batch confirms it that night.** Rejected — this is functionally identical to the current-state batch-only experience and defeats driver 1 (real-time payments parity) entirely; two competitors already show customers instant status.
3. **Real-time two-phase commit between the Ledger-of-Intent Service and the mainframe batch process.** Rejected — the batch run is a fixed, scheduled job, not a participant in a distributed transaction protocol; forcing this would mean re-architecting the batch window itself, which directly violates driver 5 and the Step 3 constraint against modifying core COBOL/CICS logic.

## Consequences

- **Positive:** Customers get an honest, real-time status that is clearly distinguished as pending vs. posted, rather than a false promise of final settlement — this is a better customer experience than either silently guessing or hiding the state entirely.
- **Positive:** The rare mismatch between provisional and batch-confirmed state is caught systematically, every business day, rather than discovered later through a customer complaint or an audit finding.
- **Negative / accepted trade-off:** This introduces a genuine new operational process — someone has to review and resolve reconciliation exceptions every business day. This is carried forward as a named operational-cost line item into the Step 13 cost and risk analysis, not treated as a one-time engineering cost.
- **Negative / accepted trade-off:** The customer-facing "pending" state has to be designed and communicated carefully (both in the UI and in any regulatory disclosures) — a rushed or unclear treatment of this state would undermine the trust real-time payments are supposed to build. This is noted as a UX/compliance-review dependency for whichever team implements Digital Banking Integration in Steps 6–9.
