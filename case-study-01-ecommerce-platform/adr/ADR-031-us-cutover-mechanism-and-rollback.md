### ADR-031: US region cutover mechanism and rollback strategy

**Context:**
ADR-030 fixed the order of the US region's four-component cutover. This ADR decides the actual mechanism each cutover uses  how traffic moves from the legacy monolith to the new architecture, and what happens when a cutover needs to be reversed. `current-state.md` §1 establishes the fact this ADR's risk reduction depends on: Solstice's current production traffic (100% US/Canada) sits on a single Amazon RDS for PostgreSQL instance, and that instance is not being replaced or migrated away from  the target US Regional Transactional Store (ADR-014) is a right-sized, Multi-AZ continuation of the same database.

**Options considered:**
- A single hard cutover per component (DNS/routing switch, all traffic moves at once, no gradual rollout).
- Dual-write to both the legacy monolith's database and a newly migrated, separate database, with a data-reconciliation step before final cutover.
- Weighted traffic shifting at the CloudFront/API Gateway layer (canary → gradual percentage shift → full cutover), with both the legacy monolith and the new architecture reading and writing the same underlying database throughout the transition.

**Decision:**
Weighted traffic shifting at the CloudFront/API Gateway layer, per component, against a continuously shared database  not a migrated one. Each component's cutover moves through a canary stage (a small, monitored percentage of traffic), a gradual weighted shift, full cutover, and a mandatory burn-in period with the legacy path kept warm as an immediate rollback target, before the next component's cutover begins.

**Rationale:**
A single hard cutover per component is rejected because it removes the single largest advantage this migration has over a typical platform migration: the ability to compare new-architecture behavior against legacy behavior on live traffic, in real time, before committing fully. A hard cutover means the first real signal of a problem is a full-traffic incident, not a canary-stage warning  precisely the kind of blind commitment that turned the November 2024 Auto Scaling Group response from a mitigation into an accelerant (`current-state.md` §2): the ASG reacted to a symptom without visibility into whether its reaction was actually helping.

Dual-write with a separate, newly migrated database is rejected for a reason specific to this case study's facts, not a generic preference against data migration: it solves a problem this migration doesn't actually have. `current-state.md` §1's single RDS instance already holds only US/Canada data, and ADR-014's target US store is architecturally a continuation of that same instance (right-sized, Multi-AZ), not a distinct target requiring data to move into it. Building a dual-write/reconciliation mechanism would add real complexity and a real data-consistency risk window to solve a data-migration problem that this specific transition doesn't have, since the database itself isn't moving  only the compute layer in front of it is.

Weighted traffic shifting against the shared, unmigrated database gets the real benefit of a gradual rollout (canary visibility, a fast, low-risk rollback path) without paying the cost of a data migration that isn't structurally necessary here. Both the legacy monolith and the new ECS/Fargate services read and write the identical database throughout the transition window for each component, so a rollback is a routing change, not a data reversal  the same underlying data is correct and current on both sides of the traffic split at every point during the shift.

**Trade-off:**
Running the legacy monolith and the new architecture against the same live database simultaneously means both code paths have to agree on schema and write semantics for the duration of each component's transition window  a coordination cost that a fully isolated, separately-migrated database wouldn't carry. This is accepted because `requirements.md` §4 already ruled out a schema redesign for this case study, so both paths are already targeting the same, unchanged schema by construction; the coordination cost is real but narrow; it does not require either path to work around a schema difference, only around which service currently owns write responsibility for a given request during the shift. A second trade-off: keeping the legacy monolith warm through each component's burn-in period, and through the whole of Phase 3's peak-event validation, means running (and paying for) both the old and new compute paths in parallel for longer than a hard-cutover plan would  an accepted cost, deferred to Step 12's cost model rather than resolved here, in exchange for the rollback safety net this entire roadmap depends on.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Cutover mechanism | Weighted traffic shifting at CloudFront + regional API Gateway (ADR-020), canary → gradual shift → full cutover |
| Database strategy | Shared, continuously-operating database throughout each component's transition  no dual-write, no data migration, no reconciliation step |
| Canary stage | Small, monitored percentage of production traffic, first exposure of the new component to live load |
| Rollback trigger | Pre-committed error-rate and latency thresholds per component, tied to business-relevant signals (checkout success rate, cart-to-order conversion latency  closing the gap `current-state.md` §4 named), not a live judgment call during an incident |
| Rollback mechanism | Routing-weight revert to the legacy monolith path  no reverse data-sync step, since both paths share the same database |
| Legacy path retention | Kept warm (not decommissioned) through the cutting-over component's full burn-in period and through Phase 3's peak-event validation |
| Decommission trigger | Only after Phase 3 (`docs/migration-roadmap.md` §6) passes cleanly  a full peak event served entirely by the new architecture |

**Status:** Approved
