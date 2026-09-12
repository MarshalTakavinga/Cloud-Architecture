# ADR-025: Self-Managed PostgreSQL for the Ledger-of-Intent Store and Audit Log

**Status:** Approved
**Date:** Step 9 of the Case Study 2 pipeline

## Context

As in every other track, the Ledger-of-Intent Service's data store must enforce the [ADR-004](ADR-004-idempotency-and-exactly-once-delivery.md) idempotency uniqueness constraint, track the [ADR-003](ADR-003-provisional-vs-confirmed-state-model.md) state model, satisfy NFR-1/NFR-2's ≤2-hour RTO / ≤15-minute RPO, and retain a tamper-evident audit trail for NFR-7's 7-year window. No managed database service exists on private infrastructure — this ADR, like [ADR-024](ADR-024-private-cloud-compute-platform.md), has to decide how much of that responsibility Palisade's own team takes on directly.

## Decision

**PostgreSQL**, self-managed, deployed as a **Patroni-orchestrated high-availability cluster** with synchronous streaming replication — one node in the primary data center, one in the secondary/DR site established in [ADR-023](ADR-023-private-cloud-platform-and-facility-strategy.md), with automatic leader election and failover. Audit-log immutability is enforced at the application layer: an append-only table, an INSERT-only database role granted to the application (no UPDATE or DELETE privilege exists for it at all), and row-level checksums maintained by the application logic — a defense-in-depth control rather than a database-engine-native cryptographic guarantee.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Extend the mainframe's own Db2 engine** for the new ledger-of-intent store, reusing Palisade's existing Db2 licensing and operational expertise. Rejected — [ADR-001](ADR-001-mainframe-integration-approach.md) already established that only a single, narrowly scoped synchronous call touches the mainframe directly. A new Db2 instance for the ledger-of-intent would either sit disconnected from the actual system-of-record Db2 instance (gaining no real synergy) or, worse, invite closer integration with it than ADR-001 deliberately allows — re-coupling the real-time path to mainframe availability in exactly the way ADR-001 was designed to avoid. An independent PostgreSQL cluster preserves the same separation of concerns every other track has.
2. **A commercial HA database appliance** (e.g., a proprietary clustered database appliance) instead of self-managed, open-source PostgreSQL. Rejected — introduces new licensing cost and a new vendor relationship for a database technology Palisade has no existing investment in, for a workload every other track has already shown needs nothing beyond a relational uniqueness constraint and standard HA replication.
3. **A cryptographically verifiable ledger layer**, matching Azure's SQL Ledger feature. No equivalent exists as a self-managed open-source option with comparable first-party support; application-enforced immutability (INSERT-only role, row checksums) is a real, but honestly weaker, technical guarantee than Azure's database-native cryptographic chain — named here rather than overstated.

## Consequences

- **Positive:** Full control over the database engine, licensing, and tuning, with no consumption-based managed-service cost.
- **Negative / accepted trade-off:** Palisade's own team must operate Patroni failover orchestration, backups, patching, and capacity planning for this cluster — the exact burden a managed database service removes on every hyperscaler track. This is [ADR-024](ADR-024-private-cloud-compute-platform.md)'s core finding recurring at the database layer: what a hyperscaler platform automates, private cloud requires Palisade's own team to build and run.
- **Carried to Step 13:** Cluster sizing (node specifications, storage), and the specific backup/archival tooling needed to actually implement the 7-year NFR-7 retention window, are cost and sizing decisions deferred to Step 13.
