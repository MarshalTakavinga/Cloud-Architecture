### ADR-015: AWS database service and replication for the Global Catalog

**Context:**
ADR-003 decided the catalog's topology: single-writer, asynchronously-replicated read copies in every active region — a genuinely different pattern from the Regional Transactional Store's regional-primary partitioning (ADR-014). Same starting constraint as ADR-014: `requirements.md` §4 says the schema isn't being redesigned, and `current-state.md` names it as PostgreSQL, already running on Amazon RDS today. The question this ADR answers is narrow on purpose: which AWS replication mechanism implements a single US-writer, multi-region-reader topology for that same PostgreSQL data.

**Options considered:**
- Amazon RDS for PostgreSQL, using its native cross-region read replica capability (single-writer primary with asynchronous cross-region replicas).
- Amazon Aurora Global Database, PostgreSQL-compatible edition (one primary region, up to five secondary read regions, storage-level replication).
- Amazon DynamoDB Global Tables, re-modeling the catalog into a globally-distributed NoSQL store.

**Decision:**
Amazon RDS for PostgreSQL with native cross-region read replicas: one Multi-AZ primary in the US region, asynchronously-replicated, read-only replica instances in EU and APAC. The US region reads directly from the primary; EU and APAC read from their local replica.

**Rationale:**
DynamoDB Global Tables is rejected for the same schema-preservation reason ADR-007 rejected Cosmos DB on the Azure track: the catalog already has a working relational schema, and `requirements.md` §4 doesn't call for a data-model rebuild, only a different deployment topology for data that already exists. Re-modeling the catalog as NoSQL documents would solve a modeling problem this case study was never asked to solve, at real migration cost and risk, for a workload whose actual problem — read latency at range — is a topology problem RDS's native replication already solves directly.

Aurora Global Database deserves a genuinely honest look rather than a reflexive pass, because it's AWS's own purpose-built product for exactly this shape of problem, and it's a materially different offer than the Azure track's equivalent decision had available: typically sub-second cross-region replication lag via dedicated storage-level replication, rather than the standard WAL-shipping RDS cross-region replicas use. It is not chosen as the default here for two concrete reasons. First, it requires migrating off standard RDS PostgreSQL onto Aurora's storage engine — a real migration step the plain-RDS-native-replica approach avoids entirely, and since ADR-014 already keeps the Regional Transactional Store on standard RDS PostgreSQL, choosing Aurora here specifically would mean operating two different underlying database products for a 22-person team instead of one. Second, Aurora Global Database's headline advantage — sub-second lag — solves a tighter consistency problem than this catalog actually has: `requirements.md` §3 sets a latency target for reads, not a near-real-time consistency target for catalog writes, and RDS's native cross-region read replica (typically low-single-digit-second lag, occasionally more under load) already clears the bar ADR-003 actually set. This is recorded as a real, close trade-off, not a foregone conclusion — Aurora Global Database is the better answer if a future revision of this case study tightens the catalog-consistency requirement, and that's worth saying plainly rather than defaulting to the simpler option out of habit.

**Trade-off:**
RDS cross-region read replica lag is asynchronous and not a hard guarantee — a merchandising price or inventory-flag change is not instantly visible everywhere, accepted for the same reason ADR-003 already accepted "not real-time by design" at the topology level. Cross-region replica promotion (if the US primary region became unreachable) is a manual, operator-initiated action via the RDS console or API, not automatic failover — the same accepted gap ADR-007 named on Azure, avoiding a split-brain write scenario for the sake of a catalog-write outage that doesn't stop customers from browsing or completing an in-flight cart in their own region.

As with ADR-014, the US primary here is a topology migration of the existing production instance named in `current-state.md` §1; EU and APAC replicas are net-new, so only the US leg of this decision carries migration risk.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Primary | Amazon RDS for PostgreSQL, Multi-AZ, `db.r6g.xlarge`, US region |
| Replicas | Cross-region read replicas (RDS native), same instance class, one each in EU and APAC |
| Replication mode | Asynchronous, RDS native cross-region read replication |
| Cache layer | Amazon ElastiCache for Redis, one cluster per region, read-through in front of each region's replica for the highest-traffic product/category pages — not a replacement for the replica, the same role ADR-007's Azure Cache for Redis plays |
| Promotion | Manual, operator-initiated (RDS "promote read replica" action) — no automatic cross-region failover for the write path |
| Write path | US region only — merchandising/back-office tooling writes exclusively to the primary |

**Status:** Approved
