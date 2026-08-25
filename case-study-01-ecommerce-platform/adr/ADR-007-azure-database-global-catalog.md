### ADR-007: Azure database service and replication for the Global Catalog

**Context:**
ADR-003 decided the catalog's topology: single-writer, asynchronously-replicated read copies in every active region  a genuinely different pattern from the Regional Transactional Store's regional-primary partitioning (ADR-006), which is exactly why it gets its own ADR here instead of being folded into ADR-006. Same starting constraint as ADR-006, though: `requirements.md` §4 says the schema isn't being redesigned, and `current-state.md` names it as PostgreSQL today.

**Options considered:**
- Azure Database for PostgreSQL  Flexible Server, using its native geo-replication (single-writer primary with cross-region read replicas).
- Azure Cosmos DB, re-modeling the catalog into a globally-distributed NoSQL store.
- Azure Cache for Redis (Enterprise, active geo-replication) as the actual multi-region read path, with PostgreSQL demoted to a write-side system of record only.

**Decision:**
Azure Database for PostgreSQL  Flexible Server geo-replication: one primary server in the US region (the catalog's write source, matching where merchandising/back-office operates today), with asynchronously-replicated, read-only replica servers in the EU and APAC regions. The US region reads directly from the primary; EU and APAC read from their local replica.

**Rationale:**
Cosmos DB is rejected for the same schema-preservation reason ADR-006 rejected a database-engine change for the transactional store: the catalog already has a working relational schema, and `requirements.md` §4 doesn't call for a data-model rebuild, only a different deployment topology for data that already exists. Re-modeling the catalog as NoSQL documents would be solving a modeling problem this case study was never asked to solve, at real migration cost and risk, for a workload whose actual problem  read latency at range  is a topology problem PostgreSQL geo-replication already solves directly. Using Redis as the real multi-region read path was seriously considered, because catalog reads are exactly the kind of cacheable, infrequently-changing data Redis excels at, and Solstice already runs a (self-managed) Redis cache for this purpose today per `current-state.md` §1  but it's rejected as the *primary* replication mechanism, not as a cache: Redis geo-replication would mean the source of truth for "what does EU see" is a cache invalidation and geo-sync policy, not a database with its own consistency guarantees, which is a materially riskier place to put catalog correctness than PostgreSQL's native, transactionally-consistent replica stream. The right answer keeps both: PostgreSQL geo-replication is the durable, authoritative multi-region read path (this ADR); a managed Redis cache sits in front of each region's replica purely as a read-through accelerator for the hottest product pages, not as the replication mechanism itself  see `application-architecture.md` §1 for how Storefront & Catalog actually uses it. Geo-replication (not full multi-master) matches ADR-003's already-decided rationale directly: catalog writes originate from one place, so a single-writer model avoids conflict-resolution complexity this write pattern doesn't need.

**Trade-off:**
Flexible Server geo-replication is asynchronous  EU and APAC replicas can lag the US primary by a small, real interval (typically low single-digit seconds, but not a guarantee), so a merchandising price or inventory-flag change is not instantly visible everywhere. Accepted because `requirements.md` §3 sets a latency target for reads, not a real-time-consistency target for catalog writes, and ADR-003 already accepted "not real-time by design" as the trade-off for this pattern at the topology level. Cross-region replica promotion (if the US primary region became unreachable) is a manual, operator-initiated action, not automatic failover  losing the single write path until an operator promotes a replica is an accepted gap for the same reason ADR-003 accepted no cross-region write failover for the transactional stores: building automatic cross-region promotion risks a split-brain write scenario for the sake of a catalog-write outage that, unlike a checkout outage, doesn't stop customers from browsing or completing an in-flight cart in their own region.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Primary | Azure Database for PostgreSQL Flexible Server, General Purpose, Standard_D4ds_v5, US region |
| Replicas | Read-only geo-replicas, same tier, one each in EU and APAC regions |
| Replication mode | Asynchronous, Flexible Server native geo-replication |
| Cache layer | Azure Cache for Redis (Standard, per region), read-through in front of each region's replica for the highest-traffic product/category pages  sized and detailed in `application-architecture.md` §1, not a replacement for the replica |
| Promotion | Manual, operator-initiated via Azure Portal/CLI  no automatic cross-region failover for the write path |
| Write path | US region only  merchandising/back-office tooling writes exclusively to the primary |

**Status:** Approved

---

See [`../diagrams/adr-007-database-service.png`](../diagrams/adr-007-database-service.png) for the detailed diagram matching this ADR's Decision  the single-writer US primary with asynchronously-replicated, read-only replicas in EU and APAC, the per-region Redis read-through cache in front of each replica, and the full Proposed Configuration table. Checked against this ADR across one review round: an early draft carried a "Zone-redundant HA" bullet on both the EU and APAC read-replica boxes, inherited from the ADR-006 diagram template  in ADR-006's topology every regional server genuinely is an independent primary, so HA legitimately applies to all three, but Azure Database for PostgreSQL Flexible Server does not support HA on read replicas at all, and this ADR's own Proposed Configuration table never specified it for the replicas either. Removed from both replica boxes; the US Primary box keeps Zone-redundant HA marked "(optional)" since the Proposed Configuration table above doesn't specify it either way. The References panel was also missing ADR-010 despite the diagram body citing it inline on the Identity Provider box  added. One known cosmetic item: the second "Async Geo-Replication" arrow (US Primary → APAC replica) is drawn as a diagonal line crossing behind the EU region box rather than a clean fan-out from the primary; a text-note alternative was suggested to avoid any reading of chained EU→APAC replication (this ADR's Decision and Key Topology Points are explicit that both replicas read directly from the US primary, not from each other), but the delivered diagram kept the arrow as drawn  left as delivered by request.
