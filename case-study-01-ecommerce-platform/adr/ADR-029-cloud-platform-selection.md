### ADR-029: Cloud platform selection  Azure vs. AWS vs. GCP

**Context:**
Steps 6–8 built the identical vendor-neutral logical design (Step 5) three times, once per platform, to the same depth, so a fair comparison would actually be possible rather than one track being a sketch and the others being real. `docs/decision-matrix.md` (Step 9) scored all three against ten criteria weighted directly from `problem-statement.md`'s ranked business drivers and `requirements.md`'s stated NFRs and constraints  not a generic platform scorecard. This ADR records the resulting decision formally, the same way ADR-001/ADR-002 recorded Step 4's decisions and ADR-003/ADR-004 recorded Step 5's.

**Options considered:**
- Microsoft Azure  the Step 6 implementation (`docs/azure-implementation.md`, ADR-005 through ADR-012).
- Amazon Web Services  the Step 7 implementation (`docs/aws-implementation.md`, ADR-013 through ADR-020).
- Google Cloud Platform  the Step 8 implementation (`docs/gcp-implementation.md`, ADR-021 through ADR-028).

**Decision:**
Amazon Web Services, scoring 4.50 of 5.00 (90%) in the Step 9 weighted decision matrix, against Azure's 4.10 (82%) and GCP's 3.85 (77%). The target architecture (Step 10) and migration roadmap (Step 11) both build on the AWS implementation documented in `docs/aws-implementation.md` and ADR-013 through ADR-020.

**Rationale:**
Two criteria decided this matrix, and both trace directly to a stated business driver or constraint rather than a generic platform preference  the full scoring and weighting rationale for every criterion lives in `docs/decision-matrix.md` §2, summarized here for the record. First, and most decisive: `requirements.md` §4's constraint that no more than one additional major replatforming initiative may run in parallel with the board-committed EU launch program. Choosing Azure or GCP means running the application re-architecture *and* a full platform migration onto infrastructure Solstice has never operated, at the same time as the EU launch  two initiatives whether or not either is individually labeled that way. Choosing AWS collapses that back to one initiative, since the re-architecture happens on the platform already running Solstice's production traffic today. Second: Amazon RDS for PostgreSQL, chosen for the Regional Transactional Store and Global Catalog (ADR-014, ADR-015), is the exact database engine already in production, including the specific connection-pool-exhaustion failure mode that caused the November 2024 outage (`current-state.md` §2)  driver #1's single largest named risk. Operators already understand this engine's behavior under this workload's specific failure pattern, a genuine reliability asset unique to the AWS track.

This was not a foregone conclusion, and the matrix shows real strength on the other two tracks worth naming plainly rather than glossed over now that a decision has been made. Azure's Entra External ID (ADR-010) offers an arguably cleaner GDPR-residency story than AWS's three separate Cognito pools (ADR-018)  a single tenant with an explicit, stated EU-residency configuration versus three region-scoped resources  even though both scored identically (5/5) on that criterion. Azure's Virtual WAN bundles Azure Firewall directly into its hub product (ADR-011), a genuine operational-complexity advantage over AWS's Transit Gateway, which requires a separately provisioned Network Firewall (ADR-019's own named trade-off). GCP's structural advantages are real and numerous: a single global VPC removing the hub/peering problem entirely (ADR-027), Cloud Run's purer per-request billing model (ADR-021), and Pub/Sub's single-product messaging elegance (ADR-025) all beat AWS's equivalent decisions outright. None of those advantages were strong enough to overcome AWS's edge on the two highest-weighted criteria (EU-readiness tied with Azure, migration risk decisively ahead of both), but they are the concrete reasons this was a genuine three-way comparison, not a formality.

**Trade-off:**
The single largest trade-off accepted by this decision is named honestly rather than smoothed over, because it is the one Step 11 has to manage directly: unlike Azure's and GCP's fully greenfield regional builds, AWS's US region carries real in-place cutover risk  the existing EC2/monolith production traffic has to migrate onto the new ECS/Fargate microservices architecture on the same platform, in the same account, without a repeat of the November 2024 outage during the transition itself. This is a migration-*execution* risk to be sequenced and de-risked through Step 11's phased rollout plan (see ADR-030, ADR-031), not a reason to prefer a fully greenfield platform instead  the decision matrix's own scoring already weighed that trade-off against the larger risk of running two major initiatives at once, and concluded the cutover risk, while real, is the smaller of the two.

A second trade-off, smaller but worth naming: AWS's operational profile is the most complex of the three at the network layer (Transit Gateway plus a separately provisioned Network Firewall, versus Azure's bundled firewall or GCP's no-hub-needed topology), and its event-bus needs two products (EventBridge + SQS FIFO) where Azure and GCP each need one. Both are accepted, named costs of the platform that wins on the criteria that matter most to this specific case study, not evidence the comparison was rigged toward AWS.

**Proposed Configuration:**

| Setting | Value |
| --- | --- |
| Selected platform | Amazon Web Services |
| Decision basis | Step 9 weighted decision matrix (`docs/decision-matrix.md`), AWS 4.50/5.00 (90%) vs. Azure 4.10/5.00 (82%) vs. GCP 3.85/5.00 (77%) |
| Deciding criteria | Migration/execution risk under the one-parallel-initiative bandwidth constraint (15% weight); reliability edge from existing RDS PostgreSQL production familiarity (15% weight) |
| Target architecture basis | `docs/aws-implementation.md` and ADR-013 through ADR-020, carried forward unchanged into Step 10 |
| Closest alternative | Microsoft Azure (82%)  would be the preferred platform absent the bandwidth constraint, or in a future case study without an existing production footprint on any of the three platforms |
| Accepted trade-off | US-region in-place cutover risk, explicitly managed by Step 11's phased migration roadmap (ADR-030, ADR-031), not treated as resolved by this ADR |

**Status:** Approved

---

See [diagram](../diagrams/cloud-platform-selection.png).
