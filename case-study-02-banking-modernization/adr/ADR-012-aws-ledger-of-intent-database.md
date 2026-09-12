# ADR-012: Amazon Aurora PostgreSQL for the Ledger-of-Intent Store and Audit Log

**Status:** Approved
**Date:** Step 7 of the Case Study 2 pipeline

## Context

[Step 5](../docs/logical-design.md) defined the Ledger-of-Intent Service's data store as the system that enforces the idempotency uniqueness constraint decided in [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md), tracks each payment's provisional-vs-confirmed state ([ADR-003](ADR-003-provisional-vs-confirmed-state-model.md)), and — for the Audit/Compliance Log — must retain a tamper-evident record for 7 years to satisfy NFR-7 and BSA/AML recordkeeping obligations. Both workloads need strong consistency and relational integrity, and the Ledger-of-Intent Service specifically participates in "critical banking functions" as `requirements.md` defines them, so it is in scope for NFR-1/NFR-2's ≤2-hour RTO and ≤15-minute RPO, not just NFR-7's retention target.

## Decision

The Ledger-of-Intent Service's data store and the Audit/Compliance Log both run on **Amazon Aurora PostgreSQL, in a Multi-AZ cluster** (one writer, at least one reader for fast failover). The audit log is an append-only table on the same cluster; once records age past the active query window, they archive to **Amazon S3 with S3 Object Lock in Compliance mode** (a true WORM guarantee — not even the account root user can delete or shorten the retention period once set), keeping the full 7-year NFR-7 retention without holding all of it in the transactional database indefinitely.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Amazon QLDB.** Rejected outright — AWS discontinued Quantum Ledger Database for new customers in 2024 and has directed existing customers to migrate off it. QLDB would otherwise have been the closest AWS-native analog to Azure's SQL Ledger feature (a purpose-built, cryptographically verifiable ledger database), but recommending a retired managed service for new-build architecture is a design error, not a legitimate trade-off — named here honestly rather than glossed over.
2. **Amazon DynamoDB.** Rejected — same reasoning [ADR-006](ADR-006-azure-ledger-of-intent-database.md) used to reject Cosmos DB: this workload needs a hard uniqueness constraint on the idempotency key and relational integrity between payment state and audit records. DynamoDB's global-scale, flexible-schema strengths don't match a single-region (NFR-6), strongly-consistent, relationally-constrained workload, and enforcing a uniqueness constraint on the idempotency key would require a conditional-write pattern standing in for what a relational database provides natively.
3. **Amazon RDS for PostgreSQL (standard Multi-AZ, not Aurora).** Considered and rejected narrowly — standard RDS Multi-AZ failover typically completes in 60–120 seconds versus Aurora's sub-30-second failover; both fit comfortably inside NFR-1's 2-hour RTO, but Aurora's faster failover and its storage layer (six copies of data replicated across three Availability Zones) give a stronger RPO story for a workload the OCC heightened-standards scrutiny is specifically about. Between two compliant options, the deliberately stronger one is the more defensible choice to have made.

## Consequences

- **Positive:** One relational engine serving both the ledger-of-intent and the audit log keeps the idempotency key genuinely traceable end-to-end, consistent with [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md)'s design intent.
- **Positive:** Aurora's sub-30-second failover and six-way storage replication directly support NFR-1 and NFR-2; S3 Object Lock Compliance mode gives a provable WORM guarantee for the archived audit trail, satisfying NFR-7 without a discontinued ledger product.
- **Negative / accepted trade-off:** Without QLDB (or an equivalent to Azure's SQL Ledger feature), this design has no database-native cryptographic hash-chain proving record integrity — immutability here is enforced by S3 Object Lock and IAM/bucket policy rather than a cryptographically verifiable chain built into the database engine itself. This is a real, named capability gap relative to Azure's SQL Ledger, carried forward honestly into Step 10's platform comparison rather than asserted as equivalent.
- **Carried to Step 13:** Aurora instance class and reader-count sizing, and the S3 lifecycle policy governing when records move from the active table to the archive, are cost and sizing decisions deferred to Step 13.
