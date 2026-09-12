### ADR-006: Azure database service for the Regional Transactional Store

**Context:**
ADR-003 decided the deployment topology for Cart, Checkout, and Order data: regional-primary partitioning, a separate primary datastore per active region, no cross-region replication. `requirements.md` §4 constrains the technology choice directly: the existing catalog/cart/order/customer relational schema is not being redesigned. `current-state.md` §1 and §5 name what that schema actually runs on today  a single Amazon RDS for PostgreSQL instance, "a reasonably well-normalized PostgreSQL schema with no known data-integrity issues," explicitly flagged as not a headline decision to re-evaluate. The Azure-specific question this ADR answers is narrow on purpose: which Azure managed database service hosts three independent, regional-primary copies of that same PostgreSQL schema.

**Options considered:**
- Azure SQL Database or Azure SQL Managed Instance  Azure's SQL Server-compatible managed offerings, the default reach for a relational workload on Azure and the choice Case Study 3 made for CareLink PM.
- Azure Database for PostgreSQL  Flexible Server  Azure's managed PostgreSQL service, engine-compatible with the schema as it exists today.
- Azure Cosmos DB for PostgreSQL (Citus)  a distributed PostgreSQL offering, built for horizontal sharding across many nodes.

**Decision:**
Azure Database for PostgreSQL  Flexible Server, General Purpose tier, zone-redundant high availability, one server per active region (US, EU, APAC) acting as that region's primary for Cart, Checkout, and Order data. No cross-region replication is configured between the three  each is independent, per ADR-003.

**Rationale:**
Azure SQL Database/Managed Instance was the right call for Case Study 3 because CareLink PM was a vendor product that already assumed SQL Server engine behavior (SQL Agent jobs, linked servers)  there was no existing schema to preserve, only a vendor's runtime assumption to satisfy. Solstice is the opposite case: `requirements.md` §4 is explicit that the schema is not being redesigned, and that schema already runs on PostgreSQL with no named defects. Moving it to a SQL Server-compatible engine would mean a database-engine migration  schema conversion, query-dialect changes, driver changes across every service that talks to it  that nothing in this case study's scope calls for and that directly contradicts `current-state.md` §5's explicit framing that a database-technology re-evaluation "isn't a headline decision" here. Azure Database for PostgreSQL Flexible Server is the direct, same-engine target: no schema conversion, no query rewrite, and it's the deployment target `requirements.md` §4's constraint actually points to once "which Azure service" is the only open question. Cosmos DB for PostgreSQL (Citus) is rejected because it's built to solve a horizontal-sharding problem  spreading one logical dataset across many nodes for write throughput a single node can't sustain  and that isn't this data's problem. Cart, Checkout, and Order data per region is write-heavy relative to the catalog but not at a scale that outgrows a single well-sized PostgreSQL instance (`requirements.md` §1's peak of ~3,750 orders/minute system-wide splits across three regional primaries, not concentrated on one), and Citus's distribution model would add operational complexity  choosing a shard key, living with its cross-shard-query constraints  to solve a problem this workload doesn't have, the same reasoning ADR-003 already used to reject full multi-master replication for this same data.

**Trade-off:**
Zone-redundant HA protects against an Availability Zone failure within a region, but per ADR-003's already-accepted trade-off, there is no cross-region failover for this data  if a whole region becomes unreachable, customers whose home region that is lose write availability for in-flight carts and orders until it recovers. That trade-off was accepted at the topology level in ADR-003 and isn't reopened here; this ADR only answers which Azure service implements it. Flexible Server's zone-redundant HA tier also costs more than the cheaper zone-redundant-disabled option  accepted because `requirements.md` §3's 99.95%-during-peak availability target needs the zone protection, and the 30%-cost-reduction target (§3) is being chased through elasticity and rightsizing at the compute tier, not by degrading database availability.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Service | Azure Database for PostgreSQL  Flexible Server |
| Tier | General Purpose, zone-redundant HA |
| Compute per region (baseline) | Standard_D4ds_v5 (4 vCore) |
| Compute per region (peak, 25x event) | Standard_D16ds_v5 (16 vCore) via planned compute-tier scaling ahead of named peak events, not real-time autoscale  PostgreSQL Flexible Server compute scaling is a resize operation, not instantaneous, so peak-day sizing is provisioned in advance of Black Friday/Cyber Monday and the two named flash-sale days, the same operational discipline `requirements.md` §1's "named peak events" already implies is predictable, unlike a true zero-notice spike |
| Storage | Premium SSD, auto-grow enabled |
| Read replicas | None for this store (regional-primary only, no fan-out reads across regions  that's the Global Catalog's shape, not this one; see ADR-007)  in-region read scaling, if needed, uses PgBouncer connection pooling in front of the primary rather than a same-region replica, since Cart/Checkout/Order reads are predominantly single-customer point lookups, not the kind of broad browse traffic that benefits from replica fan-out |
| Regional split | One independent server per region  US, EU, APAC  no shared state between them |

**Status:** Approved

---

See [`../diagrams/adr-006-database-service.png`](../diagrams/adr-006-database-service.png) for the detailed diagram matching this ADR's Decision  one independent Azure Database for PostgreSQL – Flexible Server per active region (US, EU, APAC) acting as that region's primary for Cart, Checkout, and Order data, with no cross-region replication between them, plus the full Proposed Configuration table (compute tier, planned peak-event resize ahead of named events, storage, and the PgBouncer-based in-region read-scaling approach used instead of read replicas). Checked against this ADR across several review rounds: an early draft cited a non-existent `infrastructure-standards.md` file and carried an unused "Outbound to Payment Gateway (ADR-004)" legend entry left over from the ADR-005 diagram template  both removed, along with the now-unjustified ADR-004 citation in the References panel. One known cosmetic typo remains in the delivered diagram ("Axure Front Door" instead of "Azure Front Door" in the Global Entry box)  left uncorrected by request.
