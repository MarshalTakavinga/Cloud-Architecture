# ADR-006: Azure SQL Database for the Ledger-of-Intent Store and Audit Log

**Status:** Approved
**Date:** Step 6 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md) defined the Ledger-of-Intent Service's data store as the system that enforces the idempotency uniqueness constraint decided in [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md), tracks each payment's provisional-vs-confirmed state ([ADR-003](ADR-003-provisional-vs-confirmed-state-model.md)), and — for the Audit/Compliance Log — must retain a tamper-evident record for 7 years to satisfy NFR-7 and BSA/AML recordkeeping obligations. Both workloads need strong consistency and relational integrity; the audit log specifically needs demonstrable immutability, since "we didn't alter the record" has to be provable to an OCC examiner, not just asserted.

## Decision

The Ledger-of-Intent Service's data store and the Audit/Compliance Log both run on **Azure SQL Database**. The audit log specifically uses the **Azure SQL Ledger** feature (cryptographically verifiable, append-only tables) to provide tamper-evidence, with older records archived to **Azure Blob Storage** under an immutability (WORM) policy once they age past the active query window, keeping the full 7-year NFR-7 retention without holding all of it in the transactional database indefinitely.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure Cosmos DB.** Rejected — Cosmos DB's strengths (global multi-region writes, flexible schema, massive horizontal scale) do not match this workload's actual needs. The Ledger-of-Intent Service needs a hard uniqueness constraint on the idempotency key and relational integrity between payment state and audit records — a strict relational model is a more direct fit than a globally-distributed document store, and NFR-6 (US-only data residency) removes the multi-region-write case entirely.
2. **A generic NoSQL key-value store for the ledger-of-intent, with a separate relational store for audit.** Rejected — splitting the two stores would mean the idempotency-key enforcement (ADR-004) and the audit trail for that same payment live in two different systems with two different consistency models, directly working against the "one identifier, traceable end-to-end" goal ADR-004 already established.
3. **Reusing PostgreSQL** (the choice Case Study 1 made for its own data tier). Rejected — Case Study 1's PostgreSQL choice was driven by that case study's own constraints (an existing vendor/ecosystem preference), which do not apply to Palisade. Evaluated independently here, Azure SQL Database's native Ledger feature is a more direct fit for this case study's specific tamper-evidence requirement, and Palisade carries no prior PostgreSQL investment that would otherwise tip the decision.

## Consequences

- **Positive:** SQL Ledger's cryptographic verification directly answers the "prove this record wasn't altered" question that OCC and BSA/AML scrutiny will eventually ask, without Palisade building custom tamper-evidence logic.
- **Positive:** One relational engine serving both the ledger-of-intent and the audit log keeps the idempotency key genuinely traceable end-to-end, consistent with ADR-004's design intent.
- **Negative / accepted trade-off:** Azure SQL Database is a regional, vertically-scaled service, not a globally-distributed one — acceptable here specifically because NFR-6 already requires US-only residency, so global distribution is not a capability this case study needs to buy.
- **Carried to Step 13:** Specific service tier / DTU-vs-vCore sizing, and the exact archive-to-Blob-Storage aging policy, are cost and sizing decisions deferred to Step 13.
