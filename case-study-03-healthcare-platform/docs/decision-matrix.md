# Decision Matrix — Meridian Health Network

This is Step 10: a weighted, vendor-neutral scoring of the four fully-built implementation tracks (`azure-implementation.md`, `aws-implementation.md`, `gcp-implementation.md`, `private-cloud-implementation.md`) against criteria and weights derived from `requirements.md`, not from the generic example in the reference guide's Section 19. The generic template (Existing skills, Data services, Regulatory fit, Latency, Cost, Portability, Operations, each weighted and scored 1–5) is the *methodology* this document follows; the *criteria and weights themselves* are Meridian's, built from the NFRs, constraints, and risks captured before any platform was designed — not reused off the shelf. Section 19's own framing is the discipline this document is trying to honor: writing the criteria and weights down before scoring is what turns "because we know Azure" into an auditable answer.

This document does not name a recommended platform. That is Step 11's job, informed by this matrix, the roadmap/rollback constraints, and Step 13's cost analysis — all deferred here on purpose, the same "decision, not a specific SKU" discipline applied everywhere else in this case study. Cost is scored below only as a *structural* signal (elastic vs. capital-heavy DR posture), not as a dollar figure — real 3–5 year TCO numbers don't exist until Step 13, and the matrix says so rather than pretending otherwise.

## 1. Methodology

Each of the four platforms was designed to the same depth (service mapping, network, identity/security, DR implementation with a timed runbook, IaC intent, Well-Architected-style self-check) before this document was started, specifically so this scoring step would have something real to compare rather than four surface-level sketches. Every score below is sourced from a specific ADR, implementation-doc section, or named gap/trade-off — not an impression. Where a track's documents flagged something explicitly as a gap or a strength, that flag is what drove the score; nothing here is scored from platform reputation.

Scores are 1–5 (5 = strongest fit for Meridian specifically, not a generic industry ranking) multiplied by each criterion's weight (weights sum to 100%) and summed per platform. Section 4 stress-tests the ranking against a plausible reweighting, because a single weighted total that isn't checked for sensitivity is exactly the "assert a platform" failure mode Section 19 exists to prevent.

## 2. Criteria and Weights

| Criterion | Weight | Why this weight, grounded in `requirements.md` |
| --- | --- | --- |
| Operational burden on the 16-person team | 20% | Explicit requirement: "any target architecture should reduce, not increase, undifferentiated operational burden on this team." Weighted highest because it's the one NFR stated as a directional constraint on every other decision, not just a target number. |
| RTO/RPO execution & DR resilience | 15% | Explicit requirement: RTO ≤ 4 hours, RPO ≤ 15 minutes, down from 24–48+ hours / ~24 hours today. All four tracks target the same warm-standby topology (ADR-004); this criterion scores how completely each platform's *actual tooling* closes the gap versus leaving named holes. |
| Identity / Zero Trust / MFA maturity | 15% | Explicit requirement: "MFA must be enforced for all clinical and administrative access, not a subset," directly motivated by the realized March 2026 credential-compromise incident named in the threat model. Scored on native Conditional-Access-equivalent maturity, not just "can MFA be turned on." |
| Existing skills / migration & rollback risk fit | 10% | Constraint: no single all-46-site cutover weekend; risk: the legacy CareLink PM thick-client/Citrix delivery model may constrain realistic target architectures; risk: a rushed, insurance-driven timeline could push toward an under-evaluated platform. A platform closer to the team's existing skills lowers execution risk across a multi-wave migration. |
| Data-services HA/DR maturity | 10% | Direct enabler of the RTO/RPO requirement at the database layer specifically — split out from the broader DR criterion above because the four tracks' database mechanisms turned out to differ sharply in kind, not just degree (see ADR-006/013/020/028), and that difference deserves its own line rather than being averaged away. |
| Regulatory fit / PHI data control | 10% | Constraint: PHI must remain within the United States; architecture must support HIPAA Security Rule technical safeguards. All four tracks satisfy the hard constraint; this criterion differentiates on *degree* of control and third-party subprocessor exposure. |
| Cost posture (structural, pre-Step 13) | 10% | Requirement: evaluate against the existing capital-refresh baseline, not against $0. No dollar figures exist yet (Step 13), but each track's DR topology already implies a structurally different cost shape (elastic pay-for-use vs. standing capital spend) worth flagging now rather than only in Step 13. |
| Messaging / integration DR resilience | 5% | Constraint: existing HL7v2 interfaces to LabCorp, Quest, hospital PACS feeds, and Surescripts must keep working throughout any transition, and LinkEngine's message bus sits in that path. Weighted lower than database DR because every track's reconciliation-step runbook mitigation is identical in shape; this criterion scores the underlying replication capability, not the mitigation. |
| Portability / lock-in avoidance | 5% | Not a named requirement, but a reasonable proxy for the growth assumption (further acquisitions, 2–4 clinics/year organically) and the general principle of not foreclosing Step 11 options later. Weighted lowest because Meridian never stated portability as a driver — it's prudent, not urgent. |

Weights sum to 100%.

## 3. Scoring

| Criterion | Weight | Azure | AWS | GCP | Private (VCF) |
| --- | --- | --- | --- | --- | --- |
| Operational burden on the 16-person team | 20% | 5 | 4 | 3 | 1 |
| RTO/RPO execution & DR resilience | 15% | 5 | 3 | 3 | 3 |
| Identity / Zero Trust / MFA maturity | 15% | 5 | 3 | 3 | 3 |
| Existing skills / migration & rollback risk fit | 10% | 4 | 3 | 2 | 5 |
| Data-services HA/DR maturity | 10% | 5 | 3 | 5 | 2 |
| Regulatory fit / PHI data control | 10% | 4 | 4 | 4 | 5 |
| Cost posture (structural, pre-Step 13) | 10% | 4 | 4 | 4 | 2 |
| Messaging / integration DR resilience | 5% | 4 | 2 | 2 | 2 |
| Portability / lock-in avoidance | 5% | 2 | 2 | 2 | 5 |

### Scoring rationale, by criterion

**Operational burden on the 16-person team.** Azure (5) is fully managed end to end — SQL Managed Instance, Service Bus, App Service, and a turnkey Landing Zone Accelerator pattern — with no self-managed tier named anywhere in `azure-implementation.md`. AWS (4) is also fully managed but carries two real added-burden notes: RDS Custom requires materially more OS-level care than a standard managed instance (ADR-013), and the SIEM layer is a four-service stitched stack (Security Lake, GuardDuty, Security Hub, OpenSearch) rather than one product (`aws-implementation.md` §7), against Control Tower's turnkey landing zone as an offsetting strength. GCP (3) has Cloud SQL fully managed, but the DR runbook requires manually rebuilding the Compute Engine tier on failover (no turnkey continuous-replication product, §8), and ADR-021 names the explicit absence of any Control-Tower-equivalent landing-zone product. Private cloud (1) is the clear outlier: no managed-database tier at all (ADR-028 — "the sharpest, most consequential difference between the private-cloud track and its three siblings"), self-managed RabbitMQ sitting directly in the platform's core resilience path (ADR-033), no turnkey landing-zone product of any kind — "one step further back from even GCP's own named gap" (`private-cloud-implementation.md` §4.2) — and a separate SIEM product Meridian must select, deploy, and operate itself (§7). The track's own Well-Architected self-check names Operational Excellence as "the heaviest-weighted pillar for this track, and it should be read that way" (§10).

**RTO/RPO execution & DR resilience.** All four meet the ≤4-hour RTO target on paper, but with materially different margins and mechanisms. Azure (5): 180 of 240 minutes, the largest real margin, achieved with native tooling on every leg (SQL MI auto-failover group, Site Recovery, Service Bus Geo-DR for topology). AWS (3): 195 minutes, a smaller margin, with RDS Custom's cross-region DR explicitly weaker than a native read replica (ADR-013) and SNS/SQS having zero native cross-region replication at all — "materially larger" than Azure's equivalent gap (ADR-018). GCP (3): 215 minutes, the largest margin erosion risk of the three hyperscalers, a genuinely mixed picture — faster on the database leg (native promotable read replica, a real strength AWS's RDS Custom lacks) but slower on the compute leg (no turnkey VM-tier replication product at all, §8). Private cloud (3): 185 minutes, but the fast wall-clock is explained honestly rather than claimed as superiority — it's fast because the DR facility is already provisioned to full capacity (no scale-up step to wait on), "bought with standing infrastructure spend the hyperscaler tracks don't carry, not a free win" (§12), and the one manually-operated step (Always On replica promotion) is allotted more time than any hyperscaler equivalent specifically because it isn't API-driven (ADR-028).

**Identity / Zero Trust / MFA maturity.** Azure (5) is the only platform with a native Conditional Access / Identity Protection product (Entra ID P2) — ADR-009 never had to name a gap here, unlike every sibling ADR. AWS (3), GCP (3), and private cloud (3) each explicitly name the same category of gap: IAM Identity Center, Cloud Identity, and Active Directory's own native capability are all "materially less mature" than Entra ID P2's Conditional Access, and each realistically requires a third-party CASB layer (Okta, Duo) to fully close it (ADR-016, ADR-023, `private-cloud-implementation.md` §5) — the same posture, not a worse one for private cloud, so all three score equally here.

**Existing skills / migration & rollback risk fit.** Private cloud (5) scores highest specifically because Meridian already operates a live vSphere 6.7 estate with existing staff skills — ADR-026's own reasoning for choosing VCF is "the smallest real operational-skill jump," and VMware Horizon (ADR-027) is the one place in the entire case study where a genuine native alternative to the existing Citrix delivery model exists. Azure (4) is a reasonable second: Entra ID/hybrid AD is a natural extension of the existing on-prem AD forest rather than a new identity paradigm. AWS (3) is a well-known platform generally but no existing team experience is documented, and IAM Identity Center is a bigger conceptual jump from on-prem AD than Entra Connect. GCP (2) scores lowest: it is the most structurally divergent of the three hyperscaler designs (regional subnets, projects instead of accounts, Network Connectivity Center instead of plain peering), and nothing in `current-state.md` suggests existing GCP experience on the team.

**Data-services HA/DR maturity.** Azure (5) and GCP (5) tie at the top for different reasons: Azure SQL Managed Instance's auto-failover groups have no compatibility caveat named anywhere in the case study, and Cloud SQL's native cross-region read replica is explicitly called out as "a genuine GCP-native capability RDS Custom explicitly lacks... a real strength relative to the AWS design, not a wash" (ADR-020). AWS (3) sits behind both: RDS Custom's cross-region DR is explicitly weaker than either (ADR-013's own flagged gap). Private cloud (2) is lowest: there is no managed-database tier of any kind — Always On Availability Groups are real, legitimate technology, but entirely self-operated, with async (not sync) DR replication as the honest cost of the Columbus–Dallas WAN link (ADR-028).

**Regulatory fit / PHI data control.** All four satisfy the hard US-residency/HIPAA-technical-safeguards constraint, so this criterion differentiates on degree of control rather than pass/fail. Private cloud (5) scores highest: PHI never leaves a facility Meridian controls directly, the strongest form of the requirement, with an honest caveat named rather than hidden — CDN/WAF and patient CIAM are still SaaS dependencies even here (ADR-031, ADR-032), so the track isn't fully self-contained at the edge. Azure, AWS, and GCP (4 each) are treated as equivalent: all three have mature HIPAA BAA/compliance programs and keep PHI within US regions throughout, with no material regulatory-fit differentiator named across any of the three implementation docs.

**Cost posture (structural, pre-Step 13).** No dollar figures exist yet, but the DR topology each track already committed to implies a structurally different cost shape worth flagging ahead of Step 13 rather than discovering it there. Azure, AWS, and GCP (4 each) all use an elastic warm-standby pattern — pay for standby capacity sized to actual need, scale on failover. Private cloud (2) is structurally different in kind: the Dallas facility must be provisioned to full 36-month target capacity from day one because physical hardware cannot be procured mid-incident (ADR-026) — real, ongoing capital spend on idle capacity from day one, not grown into, "a trade-off unique to this track... weighed with real financial weight in Step 13, not treated as equivalent to the 'idle standby capacity' cost ADR-004 already named generically for every platform" (`private-cloud-implementation.md` §8).

**Messaging / integration DR resilience.** Azure (4) is the only platform with any native cross-region messaging capability at all — Service Bus Geo-DR carries topology (queues, topics, subscriptions, rules) across regions, even though in-flight messages at the moment of failure are not carried over (ADR-011's own named gap, mitigated by the same source-system reconciliation step every track uses). AWS (2), GCP (2), and private cloud (2) all have zero native replication — SNS/SQS, Pub/Sub, and RabbitMQ each require matching infrastructure to be pre-provisioned in the DR region/facility via IaC, with no message content carried over (ADR-018, ADR-025, ADR-033 — the same category of gap named three separate times). GCP carries one further named hole no sibling has: no DR mirror for the Integration VPC has been built yet at all (`gcp-implementation.md` §4.1) — reflected in GCP's score here rather than double-counted elsewhere.

**Portability / lock-in avoidance.** Private cloud (5) owns its own stack with no hyperscaler-specific managed-service dependency for compute, database, or messaging — the direct flip side of the operational-burden and data-services scores above. Azure, AWS, and GCP (2 each) are treated as symmetrically locked in: each design leans on platform-native managed PaaS across the database, messaging, and identity layers (SQL MI/Service Bus, RDS Custom/SNS+SQS, Cloud SQL/Pub/Sub), and no implementation doc names a portability differentiator between the three.

## 4. Weighted Totals

| Platform | Weighted Total (out of 5.00) |
| --- | --- |
| **Azure** | **4.50** |
| AWS | 3.30 |
| GCP | 3.20 |
| Private (VCF) | 2.85 |

Azure leads clearly under Meridian's stated weights, driven by the combination of the two heaviest-weighted criteria (operational burden, at 20%, and the tied-for-second RTO/RPO and identity criteria, 15% each) all scoring 5 — not by winning on every dimension. Azure does not lead on existing-skills fit, data-services maturity (tied with GCP), regulatory fit, or portability; it leads on the specific criteria Meridian's own requirements weighted most heavily. AWS edges out GCP (3.30 vs. 3.20) despite scoring differently criterion-by-criterion, not identically — AWS's smaller operational-burden and RTO/RPO gaps outweigh GCP's stronger database-DR-maturity and better skills/portability-adjacent scores by a narrow margin; this is the closest ordering in the matrix and the one most worth re-checking once Step 13's cost numbers exist. Private cloud trails on the weighted total specifically because of the 20%-weighted operational-burden criterion, where it scores a 1 — a large, deliberate structural penalty, not a rounding effect — only partly offset by its leads on skills fit, regulatory fit, and portability.

### Sensitivity check

A single weighted total is only as trustworthy as the weights behind it. As a check, if Meridian's leadership weighted PHI data control and direct facility ownership above operational burden — a defensible position for a health system, not an unreasonable one — swapping the two weights (Regulatory fit → 20%, Operational burden → 10%, all other weights unchanged) produces:

| Platform | Weighted Total (Regulatory-weighted scenario) |
| --- | --- |
| **Azure** | **4.40** |
| AWS | 3.30 |
| GCP | 3.30 |
| Private (VCF) | 3.25 |

Azure's lead barely narrows (4.50 → 4.40) because it also scores well on regulatory fit (4), just not the highest. Private cloud's position improves the most (2.85 → 3.25) and closes almost all the way to AWS/GCP, which land in an exact tie at 3.30 under this reweighting — but private cloud still does not overtake either: the operational-burden penalty (a 1, the widest score spread of any cell in the matrix) is large enough that no single plausible reweighting closes it on its own, even one that directly favors private cloud's two strongest criteria. This is worth stating plainly: Azure's lead in this matrix is robust to a reasonable reweighting; the ordering among AWS, GCP, and private cloud is not — a 10-point weight swap alone moves private cloud from clearly last to a near-tie for second, and separately turns AWS/GCP's narrow 3.30-vs-3.20 gap in the base case into an exact tie. Any Step 11 conversation that leans on "the matrix says Azure" should be able to say why in the same breath; a conversation that leans on the AWS/GCP/private ordering below Azure should treat it as weight-sensitive, not settled.

## 5. What This Document Does Not Decide

- **No recommended platform.** That is Step 11, informed by this matrix plus the migration roadmap/rollback constraints (Step 12) and real cost numbers (Step 13) — a high weighted score here is an input to that decision, not a substitute for it.
- **No dollar figures.** The cost criterion above is deliberately structural (capital vs. elastic posture), not a TCO comparison — Step 13 by design, the same boundary every implementation doc already drew.
- **No re-litigation of platform-neutral decisions.** The migration strategy, the warm-standby DR topology, and the target database engine family (ADR-001 through ADR-004) were decided before any platform-specific work began and are not re-scored here — this matrix only compares how well each platform executes an already-agreed-upon design.

## 6. Traceability

Every score in Section 3 traces to a specific source document:

| Track | Primary sources |
| --- | --- |
| Azure | `azure-implementation.md` §5, §7, §8, §12; ADR-005, ADR-006, ADR-009, ADR-011 |
| AWS | `aws-implementation.md` §5, §7, §8, §12; ADR-013, ADR-016, ADR-018 |
| GCP | `gcp-implementation.md` §4.1, §4.2, §5, §8, §12; ADR-019, ADR-020, ADR-021, ADR-023, ADR-025 |
| Private cloud | `private-cloud-implementation.md` §4.2, §5, §7, §8, §12; ADR-026, ADR-027, ADR-028, ADR-031, ADR-032, ADR-033 |

All four tracks' NFR baseline is shared and unscored here because it doesn't differentiate them: `requirements.md`, `current-state.md`, and the platform-neutral ADR-001 through ADR-004.
