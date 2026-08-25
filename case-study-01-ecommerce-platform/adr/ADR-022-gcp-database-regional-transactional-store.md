### ADR-022: GCP database service for the Regional Transactional Store

**Context:**
ADR-003 decided the deployment topology for Cart, Checkout, and Order data: regional-primary partitioning, a separate primary datastore per active region, no cross-region replication. `requirements.md` §4 constrains the technology choice directly: the existing catalog/cart/order/customer relational schema is not being redesigned. As on the AWS track (ADR-014), this ADR is narrower than it might first appear: the question is which GCP database *product and topology* implements ADR-003's regional-primary pattern for an existing PostgreSQL schema  not whether to change the schema or engine family.

**Options considered:**
- Cloud SQL for PostgreSQL, high-availability (regional) configuration, one independent instance per active region.
- AlloyDB for PostgreSQL, GCP's newer, higher-throughput PostgreSQL-compatible engine.
- Cloud Spanner, GCP's globally-distributed relational database (PostgreSQL-interface option available).

**Decision:**
Cloud SQL for PostgreSQL, high-availability configuration (regional, synchronous standby in a second zone), one independent instance per active region (US, EU, APAC) acting as that region's primary for Cart, Checkout, and Order data. No cross-region replication is configured between the three, per ADR-003.

**Rationale:**
AlloyDB for PostgreSQL was seriously considered  it is GCP's own higher-throughput, disaggregated-storage engine, wire-compatible with PostgreSQL, so it would not force a schema conversion. It is not chosen as the default here for the identical reason ADR-006 and ADR-014 rejected their own platforms' higher-throughput options: AlloyDB's storage-layer and columnar-cache advantages primarily pay off at a write-throughput scale beyond what a single regional primary handling Cart/Checkout/Order traffic needs  `requirements.md` §1's peak of ~3,750 orders/minute system-wide splits across three regional primaries, not concentrated on one. AlloyDB is also a materially newer product with a shorter operational track record than Cloud SQL for PostgreSQL, an added-novelty cost this workload's actual scale doesn't justify taking on. Cloud Spanner is rejected outright for this specific store, not as a close call: Spanner's entire value proposition is synchronous, globally-consistent multi-region replication, and this store deliberately has **no** cross-region replication at all, per ADR-003  choosing Spanner here would mean paying for and operating a distributed-consistency engine to solve a problem this particular data doesn't have, the same "solves a problem this workload doesn't have" reasoning ADR-007 used to reject Cosmos DB for the wrong shape of problem on Azure. Cloud SQL for PostgreSQL, standard HA configuration, is the direct, lower-operational-novelty choice, and it keeps this design on the same PostgreSQL engine family every other platform track uses, without asking the team to learn a new database product for a workload that doesn't need one.

**Trade-off:**
Cloud SQL HA protects against a zonal failure within a region via a synchronous standby, but per ADR-003's already-accepted trade-off, there is no cross-region failover for this data  a customer whose home region becomes unreachable loses write availability for in-flight carts and orders until that region recovers. That trade-off was accepted at the topology level in ADR-003 and isn't reopened here.

One gap worth naming honestly rather than smoothing over: unlike AWS's RDS Proxy (a first-party managed connection-pooling proxy, see ADR-014), Cloud SQL does not currently offer an equivalent first-party managed connection-pooling product. In-region read/connection scaling for this store relies on application-level or sidecar connection pooling (e.g., PgBouncer deployed alongside the Cloud Run service) rather than a managed proxy service  a genuine, if narrow, platform capability gap worth carrying into Step 9's comparison rather than assumed away. Unlike ADR-014's US-region migration risk, this track has no equivalent asymmetry (ADR-021)  all three regions provision cleanly from a greenfield state.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Cloud SQL for PostgreSQL |
| Deployment | High availability (regional), synchronous standby in a second zone within-region |
| Machine type per region (baseline) | `db-custom-4-16384` (4 vCPU / 16 GiB) |
| Machine type per region (peak, 25x event) | `db-custom-16-65536` (16 vCPU / 64 GiB), via a planned machine-type resize ahead of named peak events  Cloud SQL machine-type changes are not instantaneous, the same planned-scaling discipline ADR-006/ADR-014 used on the other tracks |
| Storage | SSD, storage auto-increase enabled |
| Read replicas | None for this store (regional-primary only)  in-region connection scaling uses application/sidecar connection pooling (e.g., PgBouncer) in front of the primary, since Cloud SQL has no first-party managed proxy-pooling product equivalent to RDS Proxy |
| Regional split | One independent instance per region  US, EU, APAC  no shared state between them; all three regions are greenfield (no existing GCP production instance to migrate, unlike ADR-014's AWS track) |

**Status:** Approved
