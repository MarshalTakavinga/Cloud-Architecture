# ADR-004: Idempotency and Exactly-Once Delivery Approach

**Status:** Approved
**Date:** Step 5 of the Case Study 2 pipeline

## Context

NFR-5 requires exactly-once payment posting — a duplicated or dropped real-time payment is a regulatory incident, not just a bug. The event-driven design chosen in [ADR-001](ADR-001-mainframe-integration-approach.md) relies on an event bus, and most production message brokers guarantee **at-least-once** delivery, not exactly-once: a network retry, consumer restart, or broker failover can redeliver the same event more than once. This ADR decides how the architecture achieves exactly-once *posting outcomes* on top of at-least-once *delivery*.

## Decision

Every payment is keyed end-to-end by its incoming ISO 20022 message's **end-to-end ID** — a globally unique identifier already present in the message, not something Palisade has to generate. That ID is propagated unchanged through every event in the flow (`PaymentReceived`, `HoldPlaced`, `FraudApproved`/`FraudDeclined`, `ProvisionallyPosted`, `BatchConfirmed`) and used as the idempotency key at every step. The **Ledger-of-Intent Service** enforces a uniqueness constraint on this key: if a duplicate event reaches it after the first, the second arrival is a no-op, not a second posting. This converts the event bus's at-least-once delivery guarantee into effectively-once posting semantics without requiring the bus itself to provide exactly-once delivery.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Rely solely on the message broker's own exactly-once delivery mode**, where the chosen platform's messaging service offers one. Rejected as the *sole* mechanism — broker-level exactly-once guarantees are typically scoped to a single broker/topic and do not extend across the synchronous CICS hold call and multiple downstream services in this flow; a purely broker-level guarantee would leave gaps at every service boundary it doesn't cover.
2. **Generate a new idempotency key independently at each service boundary** (e.g., the Hold/Release Adapter mints one key, the Fraud Orchestration Service mints another). Rejected — this multiplies the number of places a bug or mismatch could silently break end-to-end correctness, and makes the audit trail (NFR-7) harder to follow, since a single payment would no longer have one consistent identifier across every event it produces.

## Consequences

- **Positive:** Deduplication logic lives in exactly one place (the Ledger-of-Intent Service) instead of being reimplemented, and potentially reimplemented inconsistently, in every service along the chain.
- **Positive:** The audit log (NFR-7) can trace a single payment end-to-end by one unchanging identifier, which is exactly the kind of reconstructable record an OCC exam or BSA/AML inquiry needs.
- **Negative / accepted trade-off:** Every service in the chain must reliably propagate the end-to-end ID without modification or loss — this is a schema and contract discipline enforced by convention and testing, not by any structural guarantee, and is called out explicitly here so it is designed for, and tested for, in every platform implementation in Steps 6–9 rather than assumed.
