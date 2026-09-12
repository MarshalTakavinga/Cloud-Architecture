### ADR-030: Migration sequencing and regional rollout order

**Context:**
ADR-029 fixed the target platform (AWS). `docs/migration-roadmap.md` (Step 11) needs an explicit order: which region goes first, and within the US region, which of the four owned components (`architecture-options-and-styles.md` §2) cuts over first. `current-state.md` §1 and `problem-statement.md` §1 establish the fact this ADR is built around: Solstice's current production traffic is 100% US/Canada  EU and APAC have no existing customers, data, or infrastructure to migrate away from, only a board-committed launch date to meet.

**Options considered:**
- Sequence all three regions symmetrically (build and launch US, EU, APAC in the same order/cadence, treating "migration" and "greenfield launch" as the same kind of work).
- US region first, on the reasoning that it's the largest existing revenue base and the most urgent outage-prevention need.
- Greenfield regions (EU, APAC) first, US region last, sequenced component-by-component within it.

**Decision:**
Greenfield regions first: EU and APAC are built and launched together in Phase 1, fully decoupled from the US cutover. The US region cuts over last, in Phase 2, component-by-component in this order: Storefront & Catalog, then Cart, then Checkout & Payment, then Inventory & Order Orchestration.

**Rationale:**
Treating all three regions symmetrically is rejected because it understates a real, structural difference this case study's own facts establish: EU and APAC launches carry zero cutover risk (no existing traffic to protect, no legacy data to reconcile), while the US region carries all of this migration's actual execution risk. Collapsing that distinction into one uniform rollout plan would either over-engineer the EU/APAC launches with cutover machinery they don't need, or under-prepare the US cutover by treating it as routine when it isn't.

US-first is rejected for a reason specific to this case study's own stated priorities, not a general preference for caution: `problem-statement.md` §4 ranks eliminating peak-traffic outages as driver #1 and enabling the EU launch as driver #2, both ahead of cost. Sequencing the highest-risk work (the US cutover) first would put driver #2's board-committed, dated deadline (`requirements.md` §5) at the mercy of driver #1's most complex execution risk  if the US cutover slips, and it's sequenced first, the EU launch date slips with it for no structural reason, since the two aren't actually dependent on each other. Building EU and APAC first decouples them completely: both are pure launches, not cutovers, and neither depends on the US cutover succeeding on any particular timeline. This directly addresses the compressed-EU-launch risk `requirements.md` §6 names as Medium likelihood/High impact.

Within the US cutover, the four-component order follows `architecture-options-and-styles.md` §2's own coupling analysis rather than an arbitrary list order. Storefront & Catalog is first because it's the most decoupled, most stateless, most independently cacheable component, and because its shared-connection-pool coupling to the rest of the monolith is the specific, named mechanism behind the November 2024 outage (`current-state.md` §2)  cutting it over first removes the case study's originating failure mode before anything else moves. Cart follows immediately because it shares Storefront & Catalog's ECS service and scaling shape (ADR-013), reusing a routing and rollback pattern the first cutover just proved rather than establishing a second one from scratch. Checkout & Payment is third, not first, despite PCI-DSS deadline pressure: proving the cutover mechanism itself on two lower-stakes components before using it on the payment path is a deliberate risk-reduction choice, and the ~12-month PCI-DSS assessment window (`requirements.md` §5) sets an outer bound on completion, not a reason to front-load the highest-compliance-stakes component. Inventory & Order Orchestration is last because its saga (reserve inventory → confirm payment → create order → hand off to fulfillment) structurally depends on Checkout & Payment already running correctly on the new architecture  cutting orchestration over earlier would mean debugging saga failures without knowing whether the fault lies in orchestration logic or in a still-transitioning upstream dependency.

**Trade-off:**
Sequencing the US cutover last means the case study's single largest named risk (a repeat outage, driver #1) isn't structurally addressed until Phase 2, later than a US-first plan would address it. This is accepted deliberately: Phase 0's shared platform foundation and Phase 1's EU/APAC build don't touch the legacy US path at all, so the existing production system's actual risk profile is unchanged, not worsened, by this sequencing  the legacy monolith keeps running exactly as it does today until Phase 2 begins, and Phase 3's full peak-event burn-in (`docs/migration-roadmap.md` §6) is the actual proof point that driver #1 is resolved, arriving after Phase 2 regardless of which region went first. Sequencing EU/APAC first doesn't delay that proof point relative to a US-first plan  a peak event on the new architecture still can't be demonstrated until all four US components have cut over either way.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Phase 1 (no cutover risk) | EU and APAC, built and launched together, fully decoupled from Phase 2 |
| Phase 2 order (cutover risk) | Storefront & Catalog → Cart → Checkout & Payment → Inventory & Order Orchestration |
| Sequencing basis | Coupling analysis from `architecture-options-and-styles.md` §2, not an arbitrary or alphabetical order |
| Deadline decoupling | EU launch (`requirements.md` §5, board-approved) has no dependency on US cutover completion or timeline |
| PCI-DSS deadline handling | Bounds Checkout & Payment's completion date (~12 months out), not its position in the cutover order |

**Status:** Approved

---

See [diagram](../diagrams/migration-sequencing-and-rollout-order.png).
