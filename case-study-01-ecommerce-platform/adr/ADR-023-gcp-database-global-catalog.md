### ADR-023: GCP database service and replication for the Global Catalog

**Context:**
ADR-003 decided the catalog's topology: single-writer, asynchronously-replicated read copies in every active region  a genuinely different pattern from the Regional Transactional Store's regional-primary partitioning (ADR-022). Same starting constraint as ADR-022: `requirements.md` §4 says the schema isn't being redesigned. The question this ADR answers is narrow on purpose: which GCP replication mechanism implements a single US-writer, multi-region-reader topology for that same PostgreSQL data.

**Options considered:**
- Cloud SQL for PostgreSQL, using its native cross-region read replica capability (single-writer primary with asynchronous cross-region replicas).
- Cloud Spanner, multi-region configuration, with the PostgreSQL interface.
- AlloyDB for PostgreSQL, cross-region replication.

**Decision:**
Cloud SQL for PostgreSQL with native cross-region read replicas: one HA primary in the US region, asynchronously-replicated, read-only replica instances in EU and APAC. The US region reads directly from the primary; EU and APAC read from their local replica.

**Rationale:**
Cloud Spanner deserves a genuinely honest look here, not a reflexive pass  it is GCP's own purpose-built product for exactly this shape of problem, and its multi-region configurations offer synchronous, strongly-consistent replication with read latency in the low milliseconds via TrueTime, a materially stronger consistency model than the low-single-digit-second lag typical of asynchronous read replicas. It is not chosen as the default here for two concrete reasons, the same two ADR-015 named for Aurora Global Database on the AWS track. First, even with Spanner's PostgreSQL interface, it remains a genuinely different distributed engine underneath  different scaling idioms, different transaction and indexing behavior at range  a real migration and re-learning cost the plain-Cloud-SQL-native-replica approach avoids entirely, and since ADR-022 already keeps the Regional Transactional Store on standard Cloud SQL for PostgreSQL, choosing Spanner here specifically would mean operating two different underlying database products for a 22-person team instead of one. Second, Spanner's headline advantage  near-real-time global consistency  solves a tighter consistency problem than this catalog actually has: `requirements.md` §3 sets a latency target for reads, not a near-real-time consistency target for catalog writes, and Cloud SQL's native cross-region read replica already clears the bar ADR-003 actually set. This is recorded as a real, close trade-off, not a foregone conclusion  Spanner is the better answer if a future revision of this case study tightens the catalog-consistency requirement. AlloyDB's cross-region replication capability was also considered, but it is a materially newer capability with a shorter operational track record than Cloud SQL's mature native cross-region read replica feature  the same "don't take on more novelty than the workload requires" reasoning ADR-022 applied to AlloyDB generally.

**Trade-off:**
Cloud SQL cross-region read replica lag is asynchronous and not a hard guarantee  a merchandising price or inventory-flag change is not instantly visible everywhere, accepted for the same reason ADR-003 already accepted "not real-time by design" at the topology level. Cross-region replica promotion (if the US primary region became unreachable) is a manual, operator-initiated action, not automatic failover  the same accepted gap ADR-007 and ADR-015 named on the other two tracks, avoiding a split-brain write scenario for the sake of a catalog-write outage that doesn't stop customers from browsing or completing an in-flight cart in their own region.

Unlike ADR-015's AWS track, the US primary here carries no migration risk  all three regions (US, EU, APAC) provision cleanly from a greenfield state (ADR-021).

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Primary | Cloud SQL for PostgreSQL, HA (regional), `db-custom-4-16384`, US region |
| Replicas | Cross-region read replicas (Cloud SQL native), same machine type, one each in EU and APAC |
| Replication mode | Asynchronous, Cloud SQL native cross-region read replication |
| Cache layer | Cloud Memorystore for Redis, one instance per region, read-through in front of each region's replica for the highest-traffic product/category pages  not a replacement for the replica, the same role ElastiCache/Azure Cache for Redis play on the other tracks |
| Promotion | Manual, operator-initiated  no automatic cross-region failover for the write path |
| Write path | US region only  merchandising/back-office tooling writes exclusively to the primary |

**Status:** Approved
