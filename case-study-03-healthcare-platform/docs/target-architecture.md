# Target Architecture — Meridian Health Network

Step 11: the recommended platform and target architecture, following the decision made in ADR-034. This document does not re-describe the Azure design in full — that already exists, in depth, in `azure-implementation.md` and `application-architecture.md` — it states the decision plainly, explains why in terms a non-architect stakeholder can follow, and marks exactly what is now approved versus what remains open for Step 12 (migration roadmap) and Step 13 (cost and risk analysis).

## 1. The Decision

**Meridian Health Network's target cloud platform is Microsoft Azure.** The target architecture is the design already built and documented in `azure-implementation.md` (platform-wide: service mapping, network, identity/security, DR, IaC intent) and `application-architecture.md` (per-application: CareLink PM, MeridianConnect Portal, Telehealth, LinkEngine), governed by ADR-001 through ADR-011 and ADR-034. Nothing about that design changes as a result of this document — Step 11's job is to make the choice official and explain it, not to redesign anything.

## 2. Why, in Plain Terms

Four platforms were designed to the same depth and scored against nine criteria weighted from Meridian's own requirements (`decision-matrix.md`). Azure scored highest, and by a margin that held up even when the criteria weights were deliberately stress-tested (`decision-matrix.md` §4). But the number on its own isn't the reason — it's a summary of two specific, concrete facts that matter more than the arithmetic:

**Meridian's 16-person team, plus its after-hours MSP, cannot take on new full-time administrative burden.** That's not an inference — it's stated directly in `requirements.md`: "any target architecture should reduce, not increase, undifferentiated operational burden on this team." Of the four platforms designed, Azure is the only one with nothing self-managed in its critical path. The other three each hand real, ongoing administrative work back to Meridian's team that doesn't exist today in the same form: AWS's database tier needs materially more hands-on OS-level care than a fully managed instance; GCP's disaster-recovery plan requires manually rebuilding a server tier during an actual incident because no turnkey continuous-replication product exists for it; and the private-cloud option requires Meridian to run its own database replication and its own message-broker cluster by hand — named in that track's own documentation as the single most consequential and the sharpest trade-off in the entire design. Azure has none of that.

**The MFA requirement isn't hypothetical — it's a direct response to something that already happened.** The March 2026 credential-compromise incident is what put "MFA must be enforced for all clinical and administrative access, not a subset" into the requirements in the first place. Azure is the only one of the four platforms where the strongest form of that control — blocking sign-in from a non-compliant device, flagging an atypical sign-in risk score — comes built in. On every other platform, closing that same gap fully requires bringing in and paying for a separate third-party identity vendor on top of the platform itself. Choosing a platform that still needs a follow-on purchase to fully address the exact kind of incident that already happened is a weaker starting position, not a neutral one.

Beyond those two points, Azure's disaster-recovery numbers hold up under scrutiny rather than looking good only on the surface: a 180-minute actual recovery time against the 240-minute (4-hour) requirement, achieved with the platform's own native tools handling both the database and the messaging layer — not a number that depends on a manual process going smoothly, and not one bought by paying to keep duplicate hardware idle at a second physical site the way the private-cloud option's comparable number is.

**This is not a claim that Azure is the best choice on every single dimension**, and the record should say so plainly: GCP's database replication technology is genuinely more capable than AWS's equivalent; the private-cloud option keeps patient data under Meridian's own direct physical control more completely than any cloud platform can; and the private-cloud option is also the closest fit to skills Meridian's team already has today, running the VMware systems the organization already operates. Those are real, accepted trade-offs of this decision, not oversights — recorded in full in `decision-matrix.md` §3 and ADR-034's Trade-off section.

## 3. What's Now Approved

| Item | Status |
| --- | --- |
| Platform-neutral decisions (migration strategy, target architecture style, database technology family, DR strategy) — ADR-001 through ADR-004 | Approved |
| Azure-specific implementation — `azure-implementation.md`, `application-architecture.md`, ADR-005 through ADR-011 | Approved |
| Platform selection itself | Approved — ADR-034 |
| AWS track — `aws-implementation.md`, `application-architecture-aws.md`, ADR-012 through ADR-018 | Superseded by ADR-034, retained as the documented rejected alternative |
| GCP track — `gcp-implementation.md`, `application-architecture-gcp.md`, ADR-019 through ADR-025 | Superseded by ADR-034, retained as the documented rejected alternative |
| Private-cloud track — `private-cloud-implementation.md`, `application-architecture-private-cloud.md`, ADR-026 through ADR-033 | Superseded by ADR-034, retained as the documented rejected alternative |

The three rejected tracks are not deleted. They stay in this repository at full depth — they're the evidence this decision was actually made against a real comparison, not asserted, and the reference guide's own documentation discipline (Section 8) calls for exactly this: keep the rejected options and why, not just the winner.

## 4. What This Document Does Not Resolve

Choosing Azure closes the platform question; it does not close every open item the Azure track itself already named honestly rather than hid:

- **Service Bus Geo-DR in-flight-message gap** (ADR-011). Azure Service Bus's geo-disaster-recovery feature carries queue/topic/subscription *topology* across regions on failover, but not messages that were in flight at the exact moment of failure. The DR runbook already mitigates this with a source-system reconciliation step against LabCorp, Quest, and Surescripts (`azure-implementation.md` §12) — that mitigation is approved as part of the target architecture, but the underlying gap is a platform limitation, not something Step 11 can close.
- **Bicep IaC modules** — not yet built. Explicitly deferred in `azure-implementation.md` §14; this becomes real, buildable scope in Step 12.
- **Remaining private-cloud detail diagrams, cost figures, and vendor selections in the rejected tracks** are left exactly as those tracks' own documents already recorded them (each track's own "Explicitly Deferred" section) — they are not being finished now, since those tracks are no longer the target.
- **Cost.** No dollar figures exist anywhere in this case study yet, by design — that's Step 13. Choosing Azure here is based on the operational, resilience, and identity reasoning above, checked against the decision matrix; it is explicitly not a cost-driven decision, and Step 13 could still surface a cost finding worth weighing against this ADR, the same way any ADR can be revisited with new information.

## 5. What's Next: Step 12 (Migration Roadmap and ADRs)

Step 12 turns this approved target architecture into a phased plan across Meridian's 46 sites, respecting the constraint already established in `requirements.md`: no single all-46-site cutover weekend. It should draw directly on:

- ADR-001's replatform strategy for CareLink PM and ADR-002's Strangler Fig approach for the owned components (Portal, Telehealth, LinkEngine) — these define what moves and in what order, not just where it lands.
- The rollback-strategy placeholder in `requirements.md` ("to be defined per migration wave in the roadmap stage") — Step 12 is where that actually gets defined, per wave.
- The 9-clinic acquisition closing within 12 months, named in `requirements.md` as a real near-term forcing function that the wave sequencing needs to account for directly, not treat as a footnote.
- The two open Azure-track items in Section 4 above (Bicep modules, Service Bus Geo-DR reconciliation-step operational readiness) as concrete Step 12 workstreams, not lingering unknowns.
