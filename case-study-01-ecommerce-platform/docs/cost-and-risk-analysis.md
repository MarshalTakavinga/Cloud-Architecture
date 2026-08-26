# Cost and Risk Analysis  Solstice Retail Group

Step 12 closes the loop Step 9's decision matrix opened directionally in its cost criterion, and consolidates every trade-off named across all 31 ADRs into one risk register instead of leaving them scattered across eight ADR sets. Two disciplines carried from earlier steps apply here without exception: numbers not grounded in `current-state.md` or public list pricing are labeled as illustrative assumptions, not asserted as fact, and every risk below cites the specific ADR that named it rather than being re-derived from scratch.

## 1. Cost Baseline, Derived From What's Actually Documented

`current-state.md` §1 names the current fleet precisely enough to anchor a baseline without inventing figures: 12–18 `m5.2xlarge` EC2 instances (sized for November peak, not daily demand), one `db.r5.4xlarge` RDS instance (Multi-AZ), self-managed Redis and Elasticsearch on EC2, and S3 with no CDN. Using AWS's public on-demand list pricing (`us-east-1`, illustrative  Solstice's actual reserved-instance/savings-plan pricing would differ, and isn't available in this case study) as an anchor, not a vendor quote:

| Component | Illustrative Annual Run-Rate | Basis |
| --- | --- | --- |
| EC2 fleet (15 avg × `m5.2xlarge`, on-demand) | ~$755,000 | Sized for peak year-round, per `current-state.md` §1 |
| RDS `db.r5.4xlarge`, Multi-AZ | ~$130,000 | Single instance, no read replicas |
| Self-managed Redis + Elasticsearch (EC2-hosted) | ~$95,000 | 3-node ES cluster + Redis primary/replica pair |
| S3 + no-CDN egress | ~$40,000 | Every request, domestic and international, served from `us-east-1` |
| **Illustrative baseline total** | **~$1.02M/year** | Anchor figure only  the actual comparison below is about *shape*, not this specific number |

This baseline confirms the CFO's own named trend (`problem-statement.md` §3): infrastructure is sized for peak year-round, so every dollar above what daily baseline traffic (`requirements.md` §1: ~150 orders/minute vs. ~3,750 at peak) actually needs is pure overprovisioning cost  the exact defect a consumption-priced, autoscaling architecture exists to remove.

## 2. Directional TCO Comparison  What Each Platform Track Would Have Cost

Not a re-litigation of Step 9 (ADR-029 already decided the platform)  this closes Step 9's own cost criterion with real cost-driver reasoning instead of leaving it at a directional 1–5 score. Three structural cost drivers differ meaningfully across the platforms actually specified in ADR-005–012, ADR-013–020, and ADR-021–028:

| Cost Driver | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Compute pricing shape | Container Apps Consumption + Dedicated mixed profile  pay-per-use with a provisioned floor | Fargate  pay-per-task, no EC2 fleet to keep warm | Cloud Run  pure per-request, closest fit to bursty-then-idle traffic (ADR-021) |
| Network/hub overhead | Virtual WAN bundles Azure Firewall into the hub (ADR-011)  one line item | Transit Gateway + a *separately* provisioned Network Firewall (ADR-019)  two line items | No hub product at all (ADR-027)  the lowest fixed network overhead of the three |
| Messaging overhead | Service Bus  one product | EventBridge + SQS FIFO  two products, two sets of request/message charges (ADR-017) | Pub/Sub  one product (ADR-025) |
| Managed-database premium | Flexible Server, comparable to self-managed at this scale | RDS, comparable to self-managed at this scale, but **zero migration cost** since it's the same engine already in production | Cloud SQL, comparable to self-managed at this scale |

**Directionally, GCP would have had the lowest steady-state run-rate of the three**  the pure per-request compute model, no hub-product overhead, and single-product messaging all reduce cost surface relative to the other two. **AWS has the lowest *transition* cost**  no database migration, no new platform to provision from zero, and (per ADR-031) no dual-write/reconciliation infrastructure needed for the US cutover. Since `requirements.md` §3's cost target is explicitly scoped to *"within 18 months"*  a transition-era window, not a steady-state one  AWS's transition-cost advantage matters more to the stated target than GCP's marginally better steady-state shape, reinforcing ADR-029's decision rather than reopening it. This is a real, quantifiable point in GCP's favor for a future case study without an 18-month transition window forcing the comparison.

## 3. Three-to-Five-Year TCO Trajectory  AWS Target Architecture

Directional, illustrative, and explicitly shaped around the migration roadmap's own phasing (`docs/migration-roadmap.md`), not a flat run-rate projection:

| Year | Phase | Cost Shape | Why |
| --- | --- | --- | --- |
| Year 1 (Months 1–9) | Phase 0–1 (foundation, EU/APAC build) | Baseline (~$1.02M) **plus** new-region build cost, running in parallel  a temporary increase | New infrastructure stood up while the legacy fleet keeps running unchanged (ADR-030: EU/APAC build doesn't touch legacy) |
| Year 1–2 (Months 9–15) | Phase 2 (US cutover) | Baseline **plus** new US architecture, both running simultaneously  the peak cost point of the entire roadmap | ADR-031's deliberate choice: legacy kept warm through each component's burn-in and through Phase 3, a named, accepted cost for the rollback safety net it buys |
| Year 2 (Month ~15+) | Phase 3–4 (peak burn-in, decommission) | Cost drops sharply as the legacy EC2/RDS/self-managed fleet is decommissioned | The single largest cost inflection point in the whole trajectory  `requirements.md` §3's 30% target becomes achievable only after this step, not before |
| Years 3–5 | Steady state, three active regions | Cost grows with the business (15–20%/year order growth, `requirements.md` §1) but *per-order* cost declines, since Fargate/RDS/EventBridge all scale with actual demand instead of year-round peak provisioning | Directly answers `problem-statement.md` §4's driver #4  the CFO's named 22%-YoY-cost-growth-against-9%-order-growth trend inverts once peak-only provisioning is replaced with elastic, demand-matched compute |

**The 30% cost-per-order reduction target (`requirements.md` §3) is structurally plausible under this shape, but is not asserted as achieved here.** The mechanism is real and named precisely: replacing a fleet sized year-round for November peak with Fargate's target-tracking autoscaling (ADR-013) removes the specific overprovisioning `current-state.md` §1 describes. Confirming the actual 30% figure requires real post-cutover telemetry this case study doesn't have  asserting it here without that data would repeat the exact mistake `requirements.md` §6 warns against: *"the 30% cost-per-order target tempts under-provisioning peak capacity if not modeled carefully."* This document names the mechanism and the trajectory shape; it does not claim to have modeled the number.

## 4. Consolidated Risk Register

Every named trade-off across all 31 ADRs, in one place, organized by category rather than by ADR number  the point of consolidating is to see which categories cluster, not to re-list every ADR in order.

### Migration / execution risk

| Risk | Likelihood | Impact | Mitigation | Source |
| --- | --- | --- | --- | --- |
| US-region cutover introduces a new incident during the transition itself | Medium | High | Weighted canary rollout, pre-committed rollback triggers, shared (unmigrated) database removes reverse-data-sync risk | ADR-029 (Trade-off), ADR-031 |
| A component's cutover is sequenced before its dependencies are proven | Low | Medium | Explicit coupling-based ordering (Storefront & Catalog → Cart → Checkout & Payment → Order Orchestration) | ADR-030 |
| Legacy and new architecture disagree on write semantics during a shared-database transition window | Low | Medium | Schema unchanged by `requirements.md` §4 constraint; both paths target the identical, already-validated schema | ADR-031 (Trade-off) |

### Compliance / data-residency risk

| Risk | Likelihood | Impact | Mitigation | Source |
| --- | --- | --- | --- | --- |
| A compressed EU launch timeline forces a partial rollout missing latency/residency targets | Medium | High | EU/APAC build fully decoupled from US cutover timeline (Phase 1 vs. Phase 2) | ADR-030, `requirements.md` §6 |
| PCI-DSS assessment cycle deadline (~12 months out) missed | Low–Medium | High (loss of card-not-present processing standing) | Checkout & Payment structurally isolated (dedicated ECS service, subnet, security group) ahead of the deadline, sequenced third of four, not last | ADR-013, ADR-030 |
| Cognito's three regional pools create three separate configuration surfaces to keep in sync | Low | Low–Medium | Same operational discipline named for API Gateway's per-region deployments | ADR-018, ADR-020 |

### Cost-model risk

| Risk | Likelihood | Impact | Mitigation | Source |
| --- | --- | --- | --- | --- |
| The 30% cost-per-order target tempts under-provisioning peak capacity | Medium | Medium | Named explicitly here (§3 above); real modeling required before the target is asserted as met | `requirements.md` §6, this document §3 |
| Running legacy and new architecture in parallel during Phase 2 is more expensive than a hard cutover | High (accepted) | Low–Medium | Explicitly accepted in exchange for the rollback safety net  not a surprise cost | ADR-031 (Trade-off) |
| Step Functions' per-transition pricing needs modeling against fixed compute at Solstice's actual saga volume | Medium | Low–Medium | Flagged forward from ADR-016, not resolved here  a concrete Step 12/ops-readiness follow-up | ADR-016 (Trade-off) |

### Operational risk

| Risk | Likelihood | Impact | Mitigation | Source |
| --- | --- | --- | --- | --- |
| AWS Transit Gateway doesn't bundle a firewall  Network Firewall must be separately provisioned and kept correctly configured per region | Medium | Medium | Named explicitly as an accepted trade-off relative to Azure's bundled Virtual WAN firewall | ADR-019 (Trade-off) |
| No distributed tracing / business-level signal gap repeats if observability isn't built ahead of cutover | Low | High | Observability platform built and validated in Phase 0, before any production traffic depends on it | `current-state.md` §4, `docs/migration-roadmap.md` §3 |
| A 22-person engineering org is stretched running legacy and new architecture in parallel through Phase 2–3 | Medium | Medium | Bandwidth constraint (`requirements.md` §4) already collapses this to one initiative by staying on AWS (ADR-029); still a real staffing load worth naming | ADR-029, `requirements.md` §4 |

### Vendor / product-maturity risk

| Risk | Likelihood | Impact | Mitigation | Source |
| --- | --- | --- | --- | --- |
| Aurora PostgreSQL-Compatible or Aurora Global Database would have better fit a future higher-throughput or tighter-consistency requirement | Low (current scale) | Low | Explicitly named as a "close call, not resolved," revisit if requirements tighten | ADR-014, ADR-015 |
| A future AWS-native saga/messaging product change affects Step Functions or EventBridge/SQS's cost or capability shape | Low | Low–Medium | Standard platform-currency risk, not unique to this design | ADR-016, ADR-017 |

## 5. What Step 12 Does Not Resolve

Consistent with every prior step's own "Explicitly Deferred" sections: this document gives the trajectory shape and the mechanism, not an audited financial model. Confirming the actual 30% figure, negotiating reserved-instance/savings-plan pricing, and running a real vendor cost estimate against Solstice's actual (not illustrative) usage all remain implementation-phase work, explicitly out of this case study's scope per `problem-statement.md` §5's own stated boundaries.

## 6. Case Study Status

All twelve steps are now complete: business case, current state, requirements, architecture options, vendor-neutral logical design, three full platform implementations (Azure, AWS, GCP), a weighted decision matrix, the AWS target architecture, a phased migration roadmap, and this cost/risk analysis  31 ADRs in total, ADR-001 through ADR-031.
