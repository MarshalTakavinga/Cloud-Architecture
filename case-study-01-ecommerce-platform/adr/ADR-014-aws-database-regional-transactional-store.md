### ADR-014: AWS database service for the Regional Transactional Store

**Context:**
ADR-003 decided the deployment topology for Cart, Checkout, and Order data: regional-primary partitioning, a separate primary datastore per active region, no cross-region replication. `requirements.md` §4 constrains the technology choice directly: the existing catalog/cart/order/customer relational schema is not being redesigned. `current-state.md` §1 and §5 name what that schema already runs on in production today  a single Amazon RDS for PostgreSQL instance (`db.r5.4xlarge`), Multi-AZ for failover only, no read replicas  explicitly flagged as "a reasonably well-normalized PostgreSQL schema with no known data-integrity issues," not a headline decision to re-evaluate. This ADR is narrower than it might first appear: the technology is already decided by what's already running; the question is which AWS database *topology* implements ADR-003's regional-primary pattern.

**Options considered:**
- Amazon RDS for PostgreSQL, Multi-AZ, one independent instance per active region  the same engine already in production, redeployed with a different topology.
- Amazon Aurora PostgreSQL-Compatible, Multi-AZ cluster, one cluster per active region.
- Amazon Aurora Serverless v2, auto-scaling capacity per active region.

**Decision:**
Amazon RDS for PostgreSQL, Multi-AZ deployment, one independent instance per active region (US, EU, APAC) acting as that region's primary for Cart, Checkout, and Order data. No cross-region replication is configured between the three, per ADR-003.

**Rationale:**
Aurora PostgreSQL-Compatible was seriously considered, not dismissed out of hand  it's AWS's own higher-throughput, self-healing storage layer, and it is wire-compatible with PostgreSQL, so it wouldn't force a schema conversion either. It's not chosen as the default here because Aurora's storage-layer advantages (six-way replicated storage, fast crash recovery, storage that scales independently of compute) primarily pay off at a write-throughput and instance-hour scale beyond what a single regional primary handling Cart/Checkout/Order traffic needs: `requirements.md` §1's peak of ~3,750 orders/minute system-wide splits across three regional primaries, not concentrated on one  the identical "this workload doesn't have the problem this product solves" reasoning ADR-006 used to reject Cosmos DB for PostgreSQL (Citus) on the Azure track. Standard RDS for PostgreSQL Multi-AZ is the direct, lower-operational-novelty choice, and it carries a concrete advantage specific to this platform: it's the exact database service Solstice already runs in production (`current-state.md` §1), so this decision changes the *topology*  one Multi-AZ instance per region instead of one Multi-AZ instance globally with zero read replicas  without asking the team to learn a new database engine or product from scratch, the same "same engine, different topology" discipline ADR-006 applied on Azure. Aurora Serverless v2 is rejected for this specific workload because Cart/Checkout/Order traffic during a named peak event is predictable and can be provisioned ahead of time  the same planned-scaling discipline ADR-006 used for Azure's Flexible Server compute tier  and Serverless v2's per-second capacity billing is a better fit for genuinely unpredictable, spiky workloads than for a workload whose peaks are named calendar dates.

**Trade-off:**
Multi-AZ protects against an Availability Zone failure within a region, but per ADR-003's already-accepted trade-off, there is no cross-region failover for this data  a customer whose home region becomes unreachable loses write availability for in-flight carts and orders until that region recovers. That trade-off was accepted at the topology level in ADR-003 and isn't reopened here.

One trade-off genuinely specific to this platform track: because the US region's RDS instance already exists in production, this ADR requires either an in-place Multi-AZ topology change on the current instance or a parallel cutover to a newly-provisioned instance with data migrated via AWS Database Migration Service  a real, non-zero-downtime-risk migration step that the EU and APAC instances (both greenfield) don't carry. This is named here as a planning input for the migration-roadmap stage, not resolved in this ADR.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Amazon RDS for PostgreSQL |
| Deployment | Multi-AZ (synchronous standby in a second Availability Zone within-region) |
| Instance class per region (baseline) | `db.r6g.xlarge` (4 vCPU) |
| Instance class per region (peak, 25x event) | `db.r6g.4xlarge` (16 vCPU), via planned instance-class resize ahead of named peak events  RDS instance-class changes are not instantaneous, the same planned-scaling discipline ADR-006 used on the Azure track |
| Storage | Provisioned IOPS SSD (io2), storage auto-scaling enabled |
| Read replicas | None for this store (regional-primary only)  in-region read scaling, if needed, uses Amazon RDS Proxy connection pooling in front of the primary rather than a same-region read replica, since Cart/Checkout/Order reads are predominantly single-customer point lookups |
| Regional split | One independent instance per region  US, EU, APAC  no shared state between them; the US instance is a topology migration of the existing production RDS instance named in `current-state.md` §1, EU and APAC are net-new |

**Status:** Approved

---

See [diagram](../diagrams/aws-database-regional-transactional-store.png).
