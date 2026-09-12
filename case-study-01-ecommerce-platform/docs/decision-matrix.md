# Decision Matrix  Azure vs. AWS vs. GCP

Step 9 scores the three parallel implementations (Steps 6–8) against each other, weighted by what `problem-statement.md` and `requirements.md` actually said mattered  not a generic cloud-platform scorecard borrowed from elsewhere. Every weight below traces to a ranked business driver, a stated NFR, or a named constraint; every score traces to a concrete decision already made and documented in ADR-005 through ADR-028. Where two platforms are genuinely comparable, they're scored the same rather than forced apart for the sake of a tidier table  the same discipline this portfolio held to in Case Study 3's own comparison stage.

## 1. How the Weights Were Set

`problem-statement.md` §4 ranked four business drivers in a deliberate order and said not to let a later analysis quietly contradict that ordering. This matrix doesn't: the two highest-weighted criteria below map directly to drivers #1 and #2, and cost (driver #4) is weighted lower than either  present, not dominant, consistent with the case study's own stated priority order.

| # | Criterion | Weight | Traces to |
| --- | --- | --- | --- |
| 1 | Reliability & elastic-scaling fit for the 25x/5-minute ramp | 15% | Driver #1 (`problem-statement.md` §4); `requirements.md` §3 elasticity/availability NFRs |
| 2 | EU launch readiness  CDN latency + identity data-residency guarantee | 20% | Driver #2; `requirements.md` §3 latency and EU data-residency NFRs |
| 3 | PCI scope-reduction structural fit | 10% | Driver #3; `requirements.md` §3 PCI-DSS scope NFR |
| 4 | Cost-reduction potential (pricing-model fit to bursty load) | 10% | Driver #4; `requirements.md` §3 cost NFR (weighted last on purpose, matching the drivers' own stated order) |
| 5 | Migration/execution risk under the one-parallel-initiative bandwidth constraint | 15% | `requirements.md` §4 constraint; `requirements.md` §6 risk register |
| 6 | Operational complexity for a 22-person engineering org (network topology, ops surface area) | 10% | `problem-statement.md` §1 (team size); `architecture-options-and-styles.md` §3 (small-number-of-services restraint) |
| 7 | Messaging/event-bus architectural fit | 5% | ADR-009 / ADR-017 / ADR-025 |
| 8 | Product/ecosystem maturity for the services actually chosen | 5% | Named trade-offs across ADR-016, ADR-024, ADR-026 |
| 9 | Saga-orchestration architectural fit | 5% | ADR-008 / ADR-016 / ADR-024 |
| 10 | Product-search / catalog-tooling completeness | 5% | Service Mapping tables, all three implementation docs |

Weights sum to 100%. Each platform is scored 1–5 per criterion (5 = strongest), multiplied by the weight, and summed.

## 2. Scoring, Criterion by Criterion

### 1. Reliability & elastic-scaling fit (15%)

All three chose a genuinely fast-reacting, cluster-free compute model (Container Apps/KEDA, Fargate/target-tracking, Cloud Run/per-request)  none of the three is structurally weaker here, and forcing a gap between them would misrepresent three defensible answers to the same problem as if one were obviously better. AWS gets a narrow edge for a reason specific to *this* workload, not a generic AWS preference: Amazon RDS for PostgreSQL is the exact engine already running Solstice's production traffic today (`current-state.md` §1), including the specific connection-pool exhaustion behavior that caused the November 2024 outage (`current-state.md` §2). Operators already know how this engine misbehaves under this workload's specific pressure  a genuine, narrow reliability asset unique to the AWS track, not present for Azure's or GCP's greenfield PostgreSQL deployments.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 5 | 4 |
| Why | Container Apps + KEDA; fast, proven as Step 6's reference implementation | Fargate + target-tracking, on the same RDS engine already in production | Cloud Run's per-request scaling is the fastest raw reaction of the three, but Cloud Workflows is the least production-proven orchestration engine of the three for this specific team |

### 2. EU launch readiness  latency + identity residency (20%)

The heaviest-weighted criterion, matching driver #2's status as a board-committed, dated deadline. `ADR-003` (multi-region data topology) is vendor-neutral and identical across all three tracks, so the real differentiator here is the identity layer's data-residency guarantee  and this is the one criterion where the three tracks are *not* comparable. Azure's Entra External ID uses a single tenant with an explicit, stated EU-residency configuration. AWS's Cognito uses three separate region-scoped User Pools, each provably storing only that region's data. Both are strong, differently-shaped answers to the same guarantee. GCP's Identity Platform (ADR-026) is honestly flagged in its own ADR as *not* currently offering the same first-party per-tenant data-location guarantee  a real, stated open item requiring verification before Step 11, not a smoothed-over equivalence. Scoring this criterion generously toward GCP would contradict what ADR-026 itself says.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 5 | 5 | 3 |
| Why | Entra External ID: single tenant, explicit stated EU-residency config (ADR-010) | Cognito: three regional pools, each provably regional (ADR-018) | Identity Platform: global/project-level, residency guarantee unverified (ADR-026's own named open item) |

### 3. PCI scope-reduction structural fit (10%)

All three implement the identical vendor-neutral pattern: a dedicated compute environment, its own subnet, and client-side hosted tokenization (ADR-004) so cardholder data never reaches Solstice's servers at all. GCP adds one incremental structural layer beyond the other two: a VPC Service Controls perimeter around Checkout & Payment (ADR-021), restricting which GCP-managed resources the checkout path can reach at the control-plane level, on top of network-level subnet isolation. Azure and AWS rely on network isolation (NSG / security group) alone.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 4 | 5 |
| Why | Dedicated Container Apps environment + subnet + NSG (ADR-005) | Dedicated ECS service + subnet + security group (ADR-013) | Dedicated Cloud Run service + subnet + VPC Service Controls perimeter (ADR-021)  an added control-plane-level isolation layer |

### 4. Cost-reduction potential (10%)

Directional only  real modeling is Step 12's job, not this one's. Scored purely on how closely each platform's pricing model matches "pay for bursty, mostly-idle traffic" rather than "pay for provisioned capacity year-round." Cloud Run's pure per-request billing (even with a configured minimum-instance floor, ADR-021) is the closest structural fit. Fargate and Container Apps' Consumption profile both also avoid year-round peak-capacity pricing, but neither is quite as purely usage-metered as Cloud Run.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 4 | 5 |
| Why | Consumption + Dedicated mixed profile (ADR-005) | Fargate, no EC2 fleet to keep warm (ADR-013) | Cloud Run's per-request billing is the purest usage-metered model of the three |

### 5. Migration/execution risk under the bandwidth constraint (15%)

The second-heaviest weight, and the criterion that decides this matrix more than any other. `requirements.md` §4 states the bandwidth constraint plainly: **no more than one additional major replatforming initiative may run in parallel with the EU launch program.** Choosing Azure or GCP means running two major initiatives at once whether or not anyone calls it that: the application re-architecture *and* a full platform migration of the US region's live production traffic onto infrastructure Solstice has never operated. Choosing AWS collapses that back down to one initiative  the re-architecture happens on the platform already running in production, so there is no second platform to learn, provision an account structure for, or migrate data onto. That's a structural, not incremental, advantage specific to this constraint.

This doesn't mean AWS is risk-free: `aws-implementation.md`'s opening section names the flip side honestly  the US region carries real in-place cutover risk (EC2/monolith → ECS/Fargate microservices, same account, live traffic) that Azure's and GCP's fully greenfield regions don't have at all. That risk is real and is exactly what Step 11's migration roadmap has to manage explicitly through phased cutover  but it's a migration-*execution* risk to be sequenced and de-risked, not a second full platform to stand up from zero. Azure and GCP score identically here: neither is currently in production at Solstice, so neither carries an existing-familiarity advantage, and both carry the identical "new platform, new account structure, new operational model" risk profile relative to AWS.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 3 | 5 | 3 |
| Why | Full platform migration stacked on the re-architecture  collides with the one-parallel-initiative constraint | No platform switch; re-architecture only. US-region cutover risk is real but is one initiative, not two | Same platform-migration risk profile as Azure  no existing familiarity either way |

### 6. Operational complexity for a 22-person team (10%)

Network topology carries real, ongoing operational load for a lean team, separate from initial build effort. GCP's single global VPC (ADR-027) removes the hub/peering problem structurally  nothing to provision or monitor beyond the VPC itself. Azure's Virtual WAN bundles Azure Firewall directly into each Secured Virtual Hub (ADR-011)  one product to operate instead of two. AWS's Transit Gateway does *not* bundle a firewall (ADR-019's own named trade-off); a separate AWS Network Firewall has to be explicitly provisioned, priced, and operated in a dedicated inspection VPC per region  the most operationally involved of the three.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 3 | 5 |
| Why | Virtual WAN + bundled Azure Firewall per hub (ADR-011) | Transit Gateway + separately-provisioned Network Firewall (ADR-019) | Single global VPC, no hub or peering to operate at all (ADR-027) |

### 7. Messaging/event-bus architectural fit (5%)

GCP's Pub/Sub natively combines topic fan-out, per-order ordering keys, and dead-lettering in one product (ADR-025)  the headline platform difference named in that ADR. Azure's Service Bus does the same in one product via sessions (ADR-009). AWS needs two products glued together  EventBridge for topic-style routing plus a separate SQS FIFO queue per consumer for ordering and dead-lettering (ADR-017).

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 3 | 5 |
| Why | Service Bus: one integrated product, session-ordered | EventBridge + SQS FIFO: two products glued together | Pub/Sub: one product, natively combines all three capabilities |

### 8. Product/ecosystem maturity (5%)

Every service AWS chose has the longest production track record of the three tracks, industry-wide, for the specific role it's playing here. Azure's choices are all mature, established products. GCP's Cloud Workflows and Identity Platform are both explicitly named in their own ADRs (ADR-024, ADR-026) as newer, with a smaller install base than the most established alternatives  an honest trade-off accepted there, not a defect, but still a real maturity gap worth scoring.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 5 | 3 |
| Why | Established, mature service set throughout | Longest production track record for every service chosen | Cloud Workflows and Identity Platform both explicitly self-described as newer, smaller install base |

### 9. Saga-orchestration architectural fit (5%)

All three arrived at genuinely differentiated, purpose-built answers to the same coordination problem  Container Apps/KEDA, Step Functions, Cloud Workflows  none a "renamed copy" of another. This is close to a wash by design; AWS Step Functions gets a hair's-width edge as the most widely-adopted managed state-machine product of the three, with the deepest industry track record specifically for saga-style orchestration.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 4 | 5 | 4 |
| Why | Container Apps + KEDA queue-length scaling (ADR-008) | Step Functions: purpose-built, most widely-adopted managed state-machine product (ADR-016) | Cloud Workflows: purpose-built, newest of the three (ADR-024) |

### 10. Product-search / catalog-tooling completeness (5%)

Azure and AWS both made a concrete, named choice (Azure AI Search; Amazon OpenSearch Service). GCP's own implementation doc explicitly defers this decision (`gcp-implementation.md` §14) rather than guess at a fit without verified data  the right call for that document, but it leaves this track with a real, stated gap relative to the other two at this stage.

| | Azure | AWS | GCP |
| --- | --- | --- | --- |
| Score | 5 | 5 | 2 |
| Why | Azure AI Search, concretely chosen (Service Mapping) | Amazon OpenSearch Service, concretely chosen (Service Mapping) | Explicitly deferred, not yet mapped (`gcp-implementation.md` §14) |

## 3. Weighted Totals

| Criterion | Weight | Azure | AWS | GCP |
| --- | --- | --- | --- | --- |
| 1. Reliability & elastic scaling | 15% | 0.60 | 0.75 | 0.60 |
| 2. EU readiness (latency + identity residency) | 20% | 1.00 | 1.00 | 0.60 |
| 3. PCI scope-reduction fit | 10% | 0.40 | 0.40 | 0.50 |
| 4. Cost-reduction potential | 10% | 0.40 | 0.40 | 0.50 |
| 5. Migration/execution risk | 15% | 0.45 | 0.75 | 0.45 |
| 6. Operational complexity | 10% | 0.40 | 0.30 | 0.50 |
| 7. Messaging fit | 5% | 0.20 | 0.15 | 0.25 |
| 8. Product maturity | 5% | 0.20 | 0.25 | 0.15 |
| 9. Saga-orchestration fit | 5% | 0.20 | 0.25 | 0.20 |
| 10. Search/catalog completeness | 5% | 0.25 | 0.25 | 0.10 |
| **Total (of 5.00)** | 100% | **4.10** | **4.50** | **3.85** |
| **Normalized (%)** | | **82%** | **90%** | **77%** |

## 4. Reading the Result Honestly

**AWS wins, and it wins for a specific, structural reason: the bandwidth constraint, not a generic "AWS is best" preference.** Criterion 5 (migration/execution risk) is the single largest swing in this matrix, and it isn't close  AWS is the only track that satisfies `requirements.md` §4's one-parallel-initiative constraint by construction, because it's the only track that doesn't require standing up a second cloud platform from zero on top of the application re-architecture. Criterion 1's narrow AWS edge (the team already knows exactly how the production RDS engine behaves under this workload's specific failure mode) reinforces the same theme: familiarity reduces execution risk on the exact driver  outage prevention  this entire case study exists to address.

**Azure is a genuine, close second, not a distant one  82% to AWS's 90%.** Where Azure loses points, it loses them entirely to the bandwidth constraint (criterion 5) and the RDS-familiarity edge (criterion 1); on every other criterion it ties or nearly ties AWS, and it ties or beats AWS on operational complexity, messaging, and GDPR/identity readiness (where its single-tenant, explicit-residency Entra External ID configuration is arguably a cleaner story than AWS's three separate Cognito pools, even though both scored 5). If the bandwidth constraint didn't exist  if Solstice had the engineering capacity to run a platform migration and the EU launch in parallel  this matrix would favor Azure or run close to a genuine tie between Azure and AWS.

**GCP is honestly third, and its weakest showing traces directly to a top-two business driver, not a minor tactical gap.** GCP wins outright on cost-model fit, operational simplicity, and messaging elegance  real, structural advantages named throughout ADR-021 through ADR-028  but Identity Platform's unresolved data-residency guarantee (ADR-026's own stated open item) lands squarely on driver #2, the board-committed EU/GDPR launch. Combined with carrying the same platform-migration risk as Azure without Azure's stronger identity story, GCP doesn't have a path to winning this matrix as currently scored  though it would be the strongest candidate in a future case study without an existing AWS footprint or a live GDPR deadline.

**This is a judgment call, stated as one.** Reweighting toward cost (criterion 4) or operational simplicity (criterion 6) and away from migration risk (criterion 5) would move GCP ahead of Azure, though not past AWS's criterion-5 and criterion-1 combined edge. The weights above are not arbitrary, but they are a choice  traced explicitly to Section 1 above so a reader can substitute their own priorities and recompute rather than take the ranking on faith.

## 5. Recommendation

**AWS is the recommended platform**, carried into Step 10's target architecture. This is not a defense of the status quo for its own sake  Azure and GCP were each built out to the same depth and neither was dismissed early  it's what the weighted matrix above actually produces once the case study's own stated priorities (driver order, the bandwidth constraint, the RDS-familiarity reliability edge) are applied consistently rather than treated as decoration. Step 11's migration roadmap carries the accepted trade-off  the US region's real in-place cutover risk  forward explicitly, with a phased plan designed specifically to de-risk it rather than pretend it isn't there.

## 6. ADRs From This Step

- [ADR-029  Cloud Platform Selection](../adr/ADR-029-cloud-platform-selection.md)
