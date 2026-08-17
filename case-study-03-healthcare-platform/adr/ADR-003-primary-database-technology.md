### ADR-003: Primary database technology for the CareLink PM core

**Context:**
CareLink PM currently runs on SQL Server 2014, out of extended support, in a single-datacenter Always On Availability Group. The replatform decision (ADR-001) keeps the application layer unchanged, but the database engine has to be chosen deliberately rather than assumed.

**Options considered:**
- A managed relational database engine (ACID transactions, SQL, compatible with CareLink PM's existing query patterns)
- A globally distributed NoSQL database (higher horizontal scalability, weaker relational/transactional guarantees)
- Continue running a self-managed SQL Server instance on cloud VMs, unmanaged

**Decision:** A managed relational database engine, API/wire-compatible with CareLink PM's existing SQL Server dependency.

**Rationale:**
CareLink PM is a vendor application Meridian doesn't control the source of — it was built against relational, ACID-transactional assumptions (scheduling and billing both require strong consistency), and changing that contract isn't an option under a replatform strategy. A NoSQL store would require rewriting the data-access layer, which is exactly the Refactor work ADR-001 ruled out. Moving to a *managed* relational engine (rather than continuing to self-manage SQL Server on VMs) removes the patching and end-of-support risk that is the actual root cause of the current unsupported-database finding, without touching the application layer at all.

**Trade-off:**
A managed relational engine constrains long-term horizontal scalability compared to a distributed NoSQL store — acceptable here because Meridian's own growth assumptions (≤5,000 peak concurrent sessions over a 36-month horizon) don't approach the scale where that constraint would bind.

**Status:** Proposed
