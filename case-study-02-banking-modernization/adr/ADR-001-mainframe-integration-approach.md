# ADR-001: Mainframe Integration Approach for Real-Time Payments

**Status:** Approved
**Date:** Step 4 of the Case Study 2 pipeline

## Context

Palisade needs to post real-time payments (FedNow/RTP, ISO 20022) with end-to-end latency ≤ 5 seconds (NFR-3) and exactly-once correctness (NFR-5), while the core ledger-of-record remains COBOL/CICS on DB2 for z/OS, batch-settled overnight (~5-hour window, NFR-8, driver 5). The core is explicitly out of scope to modify beyond a narrowly scoped, well-tested interface (constraint in `requirements.md`).

## Decision

Palisade will integrate the new real-time capability with the mainframe using a **hybrid pattern**: a single, narrowly scoped **synchronous call into CICS for balance-check-and-hold at the moment of payment authorization**, combined with **change-data-capture (CDC) off the DB2 for z/OS transaction log** for everything else — event publishing, fraud orchestration, ledger-of-intent updates, and customer notification. No other component makes direct synchronous calls into the mainframe.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Batch-file-only, cosmetic real-time front-end.** Rejected — does not satisfy NFR-3 or the actual FedNow settlement obligation; is a UX illusion, not a compliant real-time payment path.
2. **Full core replacement with a modern real-time-native core banking platform.** Rejected — violates the Step 3 constraint against replacing the core, and is infeasible within the 18-month board-committed timeline (driver 1).
3. **Direct synchronous API calls into CICS for every posting, not just the hold.** Rejected as the *sole* mechanism — couples the new system's availability and latency to the mainframe's, including during the nightly batch window when the ledger is not available for live posting, directly threatening driver 5 and NFR-3 simultaneously.
4. **CDC-only, with no synchronous hold at all.** Considered seriously, and rejected only narrowly — without a synchronous hold, a customer could authorize two real-time payments against the same available balance before either is reflected in the CDC stream (a double-spend / overdraft race condition). The synchronous hold exists specifically to close this one race condition; every other interaction stays asynchronous.

## Consequences

- **Positive:** The mainframe's availability and latency profile no longer bounds the real-time system's SLA, except for the single hold call, which is a well-understood, already-proven CICS transaction pattern at Palisade (balance inquiry/hold logic already exists in some form for other channels). No COBOL/CICS application code is rewritten.
- **Positive:** CDC decouples the batch window from the real-time path entirely — the nightly settlement run and the real-time payment rail can never contend with each other for the same synchronous resource.
- **Negative / accepted trade-off:** The system now has an explicit "provisional" vs. "batch-confirmed" state for every real-time payment, which must be modeled and surfaced honestly to customers and to BSA/AML reporting (a payment can be provisionally posted and later fail reconciliation in rare edge cases — this must be designed for, not assumed away). This becomes a first-class requirement carried into Step 5's logical design.
- **Negative / accepted trade-off:** The synchronous hold call is now a hard dependency — if CICS/DB2 is unavailable (including planned maintenance windows), real-time payment authorization cannot proceed. This is a smaller blast radius than coupling *every* posting to mainframe availability (option 3), but it is not zero, and is carried into the Step 13 risk register.

## Open Question Carried to Step 5

The exact mechanism for the hold call (existing CICS transaction reused vs. a new narrowly scoped transaction) depends on what Palisade's mainframe team confirms is safely exposable — this ADR fixes the *pattern*, not the specific CICS transaction, which is a Step 5/6 implementation detail.
