### ADR-003: Multi-region data topology

**Context:**
ADR-002 decided, at the level of a style, that the Storefront & Catalog read path is active-active across regions (for latency) while Cart, Checkout & Payment, and Order data are regional-primary (for consistency and GDPR residency). `requirements.md` §4 separately constrains this: the existing catalog/cart/order/customer relational schema is not being redesigned — this case study re-architects topology and elasticity, not data model. Those two facts together narrow the real question: not "what database technology," but "what deployment topology for the schema that already exists."

**Options considered:**
- A single global database for everything, with all regions reading and writing across the network to one primary — rejected outright, it's the current-state topology and the direct cause of both the latency problem and (structurally) the residency problem.
- Full multi-master replication (every region can write everything, conflicts resolved automatically) — considered for both catalog and transactional data.
- Single-writer, multi-region read replicas for the catalog; regional-primary partitioning (a separate primary per region) for cart/checkout/orders — two different patterns for two different data shapes.

**Decision:**
Catalog data: single-writer, asynchronously-replicated read copies in every active region. Cart, checkout, and order data: regional-primary partitioning — a separate primary datastore per active region (US, EU, APAC), with no cross-region replication between them.

**Rationale:**
Catalog data changes infrequently relative to storefront read volume and originates from one place (merchandising/back-office) — a single-writer model with fanned-out read replicas is the simplest pattern that satisfies the latency requirement without introducing multi-master conflict resolution the catalog's write pattern doesn't need. Full multi-master replication was considered and rejected for the catalog specifically because it solves a write-conflict problem this data doesn't have, at real operational cost. Cart, checkout, and order data is different in kind, not just degree: it's write-heavy relative to the catalog, has a real consistency requirement per transaction, and — critically — the GDPR requirement isn't satisfied by *where the data ends up eventually*, it's satisfied by where the data is written and stored as its primary copy. Regional-primary partitioning is what makes an EU customer's data actually reside in the EU as a structural property of the topology, not a downstream replication target that happens to land there.

**Trade-off:**
A customer whose home region fails over loses write availability for their in-flight cart or order until that region recovers — there is no cross-region failover for the regional-primary stores, unlike the catalog's replicated reads, which stay available everywhere even if the write region is unreachable. This is accepted explicitly: building cross-region write failover for cart/checkout/order data would mean either abandoning regional-primary partitioning (and the GDPR residency guarantee that comes with it) or building active-active multi-master writes with conflict resolution for financial transaction data — a materially riskier design this case study isn't taking on. Analytics or reporting that needs a consolidated, cross-region view of orders is not addressed by this topology and is out of scope, per `problem-statement.md` §5.

**Status:** Approved
