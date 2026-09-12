# ADR-018: Cloud SQL for PostgreSQL for the Ledger-of-Intent Store and Audit Log

**Status:** Approved
**Date:** Step 8 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md) defined the Ledger-of-Intent Service's data store as the system that enforces the idempotency uniqueness constraint decided in [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md), tracks each payment's provisional-vs-confirmed state ([ADR-003](ADR-003-provisional-vs-confirmed-state-model.md)), and — for the Audit/Compliance Log — must retain a tamper-evident record for 7 years to satisfy NFR-7 and BSA/AML recordkeeping obligations. Both workloads need strong consistency and relational integrity, and the Ledger-of-Intent Service participates in "critical banking functions" as `requirements.md` defines them, putting it in scope for NFR-1/NFR-2's ≤2-hour RTO and ≤15-minute RPO.

## Decision

The Ledger-of-Intent Service's data store and the Audit/Compliance Log both run on **Cloud SQL for PostgreSQL, in a regional (high-availability) configuration** — a primary instance with a synchronous standby in a second zone within the same region, giving automatic failover typically well inside a minute. The audit log is an append-only table on the same instance; once records age past the active query window, they archive to **Google Cloud Storage with Bucket Lock** (a retention policy that cannot be shortened or removed once set — a true WORM guarantee), keeping the full 7-year NFR-7 retention without holding all of it in the transactional database indefinitely.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cloud Spanner.** Considered and rejected — Spanner's headline strengths are horizontal scale and strong multi-region consistency for globally distributed writes, neither of which this workload needs: NFR-6 already mandates US-only, single-region data residency, and Cloud SQL's regional HA failover time already comfortably clears NFR-1's 2-hour RTO with room to spare. Choosing Spanner here would mean paying for a stronger consistency and scale guarantee than the requirement actually asks for — the same reasoning this portfolio's other Cloud SQL-vs-Spanner decisions have used.
2. **Firestore or Bigtable (NoSQL).** Rejected — same reasoning [ADR-006](ADR-006-azure-ledger-of-intent-database.md) and [ADR-012](ADR-012-aws-ledger-of-intent-database.md) used to reject Cosmos DB and DynamoDB: this workload needs a hard uniqueness constraint on the idempotency key and relational integrity between payment state and audit records, which a relational engine provides natively and a document/wide-column store would require working around.
3. **A dedicated, cryptographically verifiable ledger product**, analogous to Azure's SQL Ledger feature. Not available on GCP as a first-party managed database service today — GCP has no direct equivalent, the same gap [ADR-012](ADR-012-aws-ledger-of-intent-database.md) already named for AWS after Amazon QLDB's discontinuation. Named here for completeness rather than treated as an oversight specific to this track.

## Consequences

- **Positive:** One relational engine serving both the ledger-of-intent and the audit log keeps the idempotency key genuinely traceable end-to-end, consistent with [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md)'s design intent.
- **Positive:** Regional HA failover directly supports NFR-1 and NFR-2; Cloud Storage Bucket Lock gives a provable WORM guarantee for the archived audit trail, satisfying NFR-7.
- **Negative / accepted trade-off:** Like the AWS track, this design has no database-native cryptographic hash-chain proving record integrity — immutability here rests on Bucket Lock and IAM/bucket policy rather than a cryptographic chain built into the database engine. This is now a **consistent finding across two of the three hyperscaler tracks** (AWS and GCP both lack it; only Azure's SQL Ledger provides it natively) — worth carrying into Step 10 as a genuine Azure differentiator, not a coincidence of this one ADR.
- **Carried to Step 13:** Cloud SQL instance sizing (vCPU/memory tier) and the Cloud Storage lifecycle policy governing when records move from the active table to the archive are cost and sizing decisions deferred to Step 13.
