# Migration Roadmap  Solstice Retail Group

Step 11 turns Step 10's fixed target architecture into an actual sequence of work: which region goes first, which component within a region goes first, how a live cutover happens without repeating November 2024, and what happens when  not if  a phased migration doesn't go cleanly on the first attempt. Every phase below is ordered by a concrete risk or dependency argument, not a default "US first because it's home" assumption.

## 1. The Insight That Shapes This Whole Plan

`current-state.md` §1 and `problem-statement.md` §1 both establish a fact worth stating plainly before any phasing decision, because it changes the actual risk profile of this migration: **Solstice's current production traffic is 100% US/Canada.** There are no existing EU or APAC customers, no existing EU or APAC data, and no existing EU or APAC infrastructure to migrate anything away from. That means this isn't a three-region migration  it's one region's genuine migration (US) plus two regions' greenfield builds (EU, APAC) that happen to share a target architecture. Treating all three as symmetric "regional rollouts" would understate how much lower-risk EU and APAC actually are, and would risk sequencing the hardest, highest-stakes work (the US cutover) ahead of the work that's actually gating the board-committed deadline (the EU launch). This roadmap sequences accordingly: **greenfield regions first, migration region last**, the opposite of a naive "home region first" default.

A second, related insight de-risks the US cutover itself: because today's single Amazon RDS for PostgreSQL instance (`current-state.md` §1) already holds only US/Canada data, the target architecture's "US Regional Transactional Store" (ADR-014) isn't a new store requiring a data migration *into* it  it's a right-sized, Multi-AZ continuation of the same database Solstice already operates, now sitting behind new compute instead of old. The US cutover is a **compute-layer strangler-fig migration against a continuous, unmigrated database**, not a full data migration. That distinction is the single biggest risk reducer in this plan, and it's named explicitly in ADR-031.

## 2. Phase Overview

| Phase | What | Region(s) | Risk Profile |
| --- | --- | --- | --- |
| 0 | Shared platform foundation | All (built once) | No cutover risk  nothing touches production traffic |
| 1 | New-market greenfield build and launch | EU, APAC | No cutover risk  zero existing traffic to migrate |
| 2 | US strangler-fig cutover, component by component | US | The plan's real risk  managed explicitly in ADR-031 |
| 3 | First full peak-event burn-in on the new architecture | US (all regions serving) | Validation, not build  the actual proof this design works |
| 4 | Decommission the legacy monolith and single-instance database fleet | US | Low risk  only after Phase 3 passes cleanly |

## 3. Phase 0  Shared Platform Foundation

Everything here is additive and parallel-safe: it stands up new infrastructure without touching the EC2 Auto Scaling Group, the single RDS instance, or any live traffic path named in `current-state.md` §1. This phase can start immediately and run for its full duration without any customer-facing risk.

- AWS account/VPC structure, Transit Gateway per region and inter-region peering, AWS Network Firewall (ADR-019).
- CI/CD pipelines and the CloudFormation/CDK IaC baseline (`aws-implementation.md` §12).
- Observability platform: CloudWatch, X-Ray, dashboards and alerts tied to the specific signals `aws-implementation.md` §10 names (SQS DLQ depth, RDS replication lag, ECS ceiling approach, Step Functions failure rate)  built and validated *before* any production traffic depends on it, not bolted on afterward the way `current-state.md` §4 describes today's gap.
- Cognito User Pools provisioned for all three regions (ADR-018), CloudFront distribution and regional API Gateway instances provisioned but not yet carrying customer traffic (ADR-020).
- Global Catalog target topology stood up: the US Amazon RDS for PostgreSQL primary (ADR-015) is provisioned as a **read replica of the existing production database** initially  an additive, zero-risk way to validate the new replication topology against real data before anything cuts over.

**Exit criterion:** every shared platform component passes a synthetic load test at the 25x elasticity target (`requirements.md` §3) with zero production traffic on it yet.

## 4. Phase 1  New-Market Regions (EU, APAC): Greenfield Build and Launch

Built and launched together, in parallel with each other, since neither has any existing traffic or data to protect and both draw on the identical Phase 0 foundation. EU is prioritized for go-live readiness given its explicit board-approved timeline and the GDPR/data-residency requirement's compliance urgency (`problem-statement.md` §3); APAC follows on the same build track without a hard external deadline forcing it further behind.

- Full target architecture stood up region-by-region: ECS/Fargate services (ADR-013), Regional Transactional Store (ADR-014), EventBridge + SQS (ADR-017), Step Functions orchestration (ADR-016), regional Cognito pool and API Gateway (ADR-018, ADR-020).
- EU and APAC Global Catalog read replicas (ADR-015) seeded from the US primary  by this point already validated in Phase 0.
- Go-live is a pure launch, not a cutover: EU and APAC customers are, by definition, new to Solstice, so there's no existing traffic to shift and no rollback-to-legacy path needed for these two regions at all.

**Exit criterion:** EU and APAC serving live customer traffic, meeting `requirements.md` §3's latency target (p95 ≤ 150ms) and the EU data-residency requirement, independently verified before Phase 2 begins  decoupling the board-committed EU deadline from the higher-risk work still to come in Phase 2, directly addressing the compressed-timeline risk `requirements.md` §6 names.

## 5. Phase 2  US Region: Strangler-Fig Cutover

The only phase with real migration risk, and the only one sequenced component-by-component rather than launched all at once. Order follows `architecture-options-and-styles.md` §2's own coupling analysis  the component least entangled with the rest of the monolith goes first, the most dependent goes last:

1. **Storefront & Catalog**  the most read-heavy, most stateless, most independently cacheable component (`architecture-options-and-styles.md` §2), and the one whose shared-connection-pool coupling directly caused the November 2024 outage. Cutting it over first, behind weighted CloudFront/API Gateway routing (ADR-031), immediately removes the specific failure mode this entire case study exists to fix, before anything else moves.
2. **Cart**  shares its ECS service and scaling shape with Storefront & Catalog (ADR-013), so cutting it over second reuses a now-proven routing and rollback pattern rather than establishing a new one.
3. **Checkout & Payment**  deliberately not first, despite the PCI-DSS deadline pressure: cutting over the two lower-stakes, higher-confidence components first proves the cutover mechanism itself before it's used on the payment path. The approaching PCI-DSS assessment cycle (~12 months out, `requirements.md` §5) sets the outer bound on when this step must complete, not the order it happens in relative to Storefront/Cart.
4. **Inventory & Order Orchestration**  last, on purpose: the saga (reserve inventory → confirm payment → create order → hand off to fulfillment) depends on Checkout & Payment already being stable and correctly integrated with the new architecture. Cutting orchestration over before its dependencies are proven would mean debugging saga failures without knowing whether the fault is in the orchestration logic or in a still-transitioning upstream component.

Each component follows the identical cutover mechanism (canary → weighted shift → full cutover → legacy standby → decommission), detailed in ADR-031 rather than repeated four times here.

**Exit criterion per component:** 100% of production traffic served by the new architecture, the legacy monolith path kept warm (not decommissioned) as an immediate rollback target, for a minimum burn-in window before the next component begins its own cutover.

## 6. Phase 3  First Full Peak-Event Burn-In

Every component has cut over, but the plan isn't finished until the new architecture proves itself against the exact scenario that started this case study: a named peak event at or near the 25x planning figure (`requirements.md` §1). This phase is validation, not additional build work  it exists because a migration that looks complete under baseline load and hasn't yet been proven under peak load is not actually complete, per this case study's own driver #1 priority.

**Exit criterion:** a full peak event (Black Friday/Cyber Monday or an equivalent flash-sale event) served entirely by the new architecture, meeting the 99.95% peak-event availability target (`requirements.md` §3), with the legacy monolith serving zero production traffic throughout.

## 7. Phase 4  Decommission

Only after Phase 3 passes cleanly: the EC2 Auto Scaling Group, the original single RDS instance's legacy connection paths, self-managed Redis, and self-managed Elasticsearch (`current-state.md` §1) are decommissioned. Not before  keeping the legacy path warm through a full peak cycle is the rollback safety net this entire roadmap is built around, and decommissioning early would remove it exactly when it's still needed most.

## 8. Rollback Strategy

Named once here rather than repeated per phase, since the mechanism is identical everywhere it applies:

- **New-market regions (Phase 1) need no rollback mechanism at all**  there is no prior state to revert to for customers who didn't exist on the platform before. A serious defect there is fixed forward, not rolled back to.
- **The US cutover (Phase 2) is a weighted-routing revert, not a data migration reversal.** Because the US Regional Transactional Store is a continuation of the existing production database (Section 1) rather than a newly migrated one, rolling back a component means shifting CloudFront/API Gateway routing weight back to the legacy monolith path  both paths read and write the same underlying database throughout the transition window, so there is no reverse data-sync step blocking a fast rollback. See ADR-031 for the specific routing and monitoring mechanism.
- **Explicit rollback triggers, not judgment calls made under pressure:** error-rate and latency thresholds are defined per component *before* its cutover begins, tied to the same business-relevant signals `current-state.md` §4 flagged as missing today (checkout success rate, cart-to-order conversion latency)  the decision to roll back is pre-committed, not debated live during an incident.

## 9. Risk Register, Carried Forward From Step 2 With Mitigations

| Risk (`requirements.md` §6) | Mitigation in this roadmap |
| --- | --- |
| A compressed EU launch timeline forces a partial rollout that doesn't meet latency/residency targets | Phase 1 (EU/APAC) is fully decoupled from Phase 2's higher-risk US cutover work and can complete independently  a slip in Phase 2 doesn't threaten the EU launch date |
| 2025 peak traffic exceeds the 25x planning figure, repeating a larger-scale outage | Phase 3 exists specifically to prove the new architecture against a real peak event before the legacy fallback is removed  the plan doesn't call itself done until this is demonstrated, not assumed |
| The 30% cost-per-order target tempts under-provisioning peak capacity | Deferred explicitly to Step 12's cost model, which is asked to show its work against this exact target  not addressed by sequencing, and not pre-empted here |
| The one-parallel-initiative bandwidth constraint is exceeded if not sequenced carefully | This entire roadmap *is* the one initiative  Phase 1's EU/APAC build is treated as part of the re-architecture program, not a second program, consistent with ADR-029's reasoning for staying on AWS in the first place |

## 10. ADRs From This Step

- [ADR-030  Migration Sequencing and Regional Rollout Order](../adr/ADR-030-migration-sequencing-and-rollout-order.md)
- [ADR-031  US Region Cutover Mechanism and Rollback Strategy](../adr/ADR-031-us-cutover-mechanism-and-rollback.md)

## 11. What's Next: Step 12 (Cost and Risk Analysis)

The roadmap above is sequenced and de-risked, but not yet costed or exhaustively risk-scored  that's Step 12's job: a 3–5 year TCO comparison across what the three platform tracks would each have cost (closing the loop Step 9's decision matrix opened, directionally, in its cost criterion) and a consolidated risk register pulling together every trade-off named across all 31 ADRs into one place.
